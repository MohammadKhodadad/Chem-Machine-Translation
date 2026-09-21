import json
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

from chem_machine_translation.data.terminology import (
    TARGET_CANDIDATE_EXTRACTOR_SYSTEM_PROMPT,
    UNTERM_LANGUAGE_CODES,
    UNTERMClient,
    DatasetTerminologyGenerator,
    DatasetTerminologyTerm,
    LLMTargetCandidateExtractor,
    LLMTerminologyRefiner,
    SpaCyTerminologyExtractor,
    TargetTerminologyExtractor,
    append_terminology_cache,
    dataset_term_from_json,
    deduplicate_terms,
    load_manifest_terminology,
    load_terminology_cache,
    llm_refiner_candidate_payload,
    make_stanza_terms,
    parse_llm_refined_terms,
    parse_llm_target_candidates,
    select_dataset_terms,
    should_preserve_dataset_term,
    stanza_candidate_surface_is_clean,
    stanza_span_confidence,
)


class _FakePubChemClient:
    def lookup_synonyms(self, term: str) -> list[str]:
        return ["sodium chloride", "chlorure de sodium"] if term == "chlorure de sodium" else []


class _FakeIATEClient:
    def lookup_synonyms(self, term: str, language_code: str) -> list[str]:
        if term == "chlorure de sodium" and language_code == "fr":
            return ["chlorure de sodium", "sel de table"]
        return []


class _FakeExtractor:
    def extract(
        self,
        text: str,
        max_terms: int,
        target_language: str = "",
    ) -> list[DatasetTerminologyTerm]:
        assert text
        assert max_terms == 5
        assert target_language == "French"
        return [
            DatasetTerminologyTerm(
                source_term="",
                target_terms=("chlorure de sodium",),
                reference_candidates=("chlorure de sodium",),
                category="chemical",
                source="fake_ner",
                confidence=0.8,
                decision="keep_reference",
            )
        ]


class _FakeResponses:
    def create(self, **kwargs: object) -> object:
        assert kwargs["temperature"] == 0.0
        return type(
            "Response",
            (),
            {
                "output_text": json.dumps(
                    {
                        "terms": [
                            {
                                "target_term": "chlorure de sodium",
                                "category": "chemical",
                                "confidence": 0.91,
                                "reason": "Compound name",
                            },
                            {
                                "target_term": "hallucinated term",
                                "category": "chemical",
                                "confidence": 0.99,
                                "reason": "Not in text",
                            },
                        ]
                    }
                )
            },
        )()


class _FakeClient:
    responses = _FakeResponses()


class _FakeRefinerResponses:
    def create(self, **kwargs: object) -> object:
        assert kwargs["temperature"] == 0.0
        return type(
            "Response",
            (),
            {
                "output_text": json.dumps(
                    {
                        "terms": [
                            {
                                "candidate_id": 0,
                                "target_term": "chlorure de sodium",
                                "category": "chemical",
                                "quality_score": 0.95,
                                "reason": "Specific compound name.",
                            },
                            {
                                "candidate_id": 1,
                                "target_term": "hallucinated term",
                                "category": "chemical",
                                "quality_score": 0.99,
                                "reason": "Mismatched candidate text.",
                            },
                            {
                                "candidate_id": 99,
                                "target_term": "chlorure de sodium",
                                "category": "chemical",
                                "quality_score": 0.99,
                                "reason": "Invalid candidate id.",
                            },
                        ]
                    }
                )
            },
        )()


class _FakeRefinerClient:
    responses = _FakeRefinerResponses()


def test_target_candidate_prompt_requires_exact_target_spans() -> None:
    assert "exact spans that appear in the provided target text" in (
        TARGET_CANDIDATE_EXTRACTOR_SYSTEM_PROMPT
    )
    assert "Do not translate" in TARGET_CANDIDATE_EXTRACTOR_SYSTEM_PROMPT


def test_unterm_client_requires_exact_result_match() -> None:
    payload = """
    <html>
      <div>Results 1-10 of 120</div>
      <a href="/en/search?searchTerm=water">water</a>
      <a href="/en/search?searchTerm=watery">watery</a>
    </html>
    """

    assert UNTERMClient._result_contains_exact_match(payload, "water") is True
    assert UNTERMClient._result_contains_exact_match(payload, "wate") is False


def test_unterm_client_supports_all_six_un_languages_only() -> None:
    assert UNTERM_LANGUAGE_CODES == {"ar", "zh", "en", "fr", "ru", "es"}
    assert "de" not in UNTERM_LANGUAGE_CODES


def test_unterm_search_uses_language_filter_not_language_route() -> None:
    client = UNTERMClient(endpoint="https://example.test/unterm2")
    captured = {}

    class _Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return b""

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        return _Response()

    import chem_machine_translation.data.terminology as terminology_module

    original_urlopen = terminology_module.urlopen
    terminology_module.urlopen = fake_urlopen
    try:
        client._search("water", "de")
    finally:
        terminology_module.urlopen = original_urlopen

    parsed = urlparse(captured["url"])
    query = parse_qs(parsed.query)
    assert parsed.path == "/unterm2/en/search"
    assert query["searchTerm"] == ["water"]
    assert query["searchLanguages"] == ["de"]
    assert query["languagesDisplay"] == ["de"]


def test_dataset_term_round_trips_json_shape() -> None:
    term = DatasetTerminologyTerm(
        source_term="",
        target_terms=("chlorure de sodium",),
        reference_candidates=("chlorure de sodium",),
        category="chemical",
        source="target_ner+pubchem",
        term_group="verified",
        verified_by=("pubchem",),
        confidence=0.91,
        decision="keep_reference",
        reason="Target-side term",
        candidates={"pubchem": ["sodium chloride"]},
    )

    loaded = dataset_term_from_json(term.to_json())

    assert loaded == term


def test_deduplicate_terms_merges_extractor_and_verifier_tags() -> None:
    stanza_term = DatasetTerminologyTerm(
        target_terms=("sodium chloride",),
        reference_candidates=("sodium chloride",),
        category="chemical",
        source="stanza_ud_dependency+pubchem",
        term_group="verified",
        verified_by=("pubchem",),
        confidence=0.82,
        decision="keep_reference",
        candidates={"pubchem": ["sodium chloride"]},
    )
    nobi_term = DatasetTerminologyTerm(
        target_terms=("sodium chloride",),
        reference_candidates=("sodium chloride", "Sodium chloride"),
        category="chemical",
        source="xlmr_nobi+chebi",
        term_group="verified",
        verified_by=("chebi",),
        confidence=0.76,
        decision="keep_reference",
        candidates={"chebi": ["sodium chloride", "NaCl"]},
    )

    merged = deduplicate_terms([stanza_term, nobi_term])

    assert len(merged) == 1
    assert merged[0].source == "stanza_ud_dependency+pubchem+xlmr_nobi+chebi"
    assert merged[0].term_group == "verified"
    assert merged[0].verified_by == ("pubchem", "chebi")
    assert merged[0].candidates == {
        "pubchem": ["sodium chloride"],
        "chebi": ["sodium chloride", "NaCl"],
    }
    assert merged[0].confidence == 0.82


def test_parse_llm_target_candidates_drops_terms_missing_from_reference() -> None:
    terms = parse_llm_target_candidates(
        json.dumps(
            {
                "terms": [
                    {
                        "target_term": "chlorure de sodium",
                        "category": "chemical",
                        "confidence": 0.92,
                        "reason": "Compound name",
                    },
                    {
                        "target_term": "not in the text",
                        "category": "chemical",
                        "confidence": 0.99,
                    },
                ]
            }
        ),
        reference_text="La solution contient du chlorure de sodium.",
    )

    assert [term.target_terms[0] for term in terms] == ["chlorure de sodium"]
    assert terms[0].source == "llm_target"
    assert terms[0].term_group == "llm"


def test_llm_target_candidate_extractor_uses_target_text_only() -> None:
    extractor = LLMTargetCandidateExtractor(client=_FakeClient(), model="gpt-test")

    terms = extractor.extract(
        text="La solution contient du chlorure de sodium.",
        target_language="French",
        max_terms=5,
    )

    assert [term.target_terms[0] for term in terms] == ["chlorure de sodium"]


def test_parse_llm_refined_terms_requires_existing_candidate_and_exact_span() -> None:
    candidates = [
        DatasetTerminologyTerm(
            target_terms=("chlorure de sodium",),
            reference_candidates=("chlorure de sodium",),
            category="chemical",
            source="spacy_ngram+pubchem",
            term_group="verified",
            verified_by=("pubchem",),
            confidence=0.8,
            candidates={"pubchem": ["sodium chloride"]},
        ),
        DatasetTerminologyTerm(
            target_terms=("solution",),
            reference_candidates=("solution",),
            category="other",
            source="spacy_ngram",
            confidence=0.4,
        ),
    ]

    terms = parse_llm_refined_terms(
        json.dumps(
            {
                "terms": [
                    {
                        "candidate_id": 0,
                        "target_term": "chlorure de sodium",
                        "category": "chemical",
                        "quality_score": 0.95,
                    },
                    {
                        "candidate_id": 1,
                        "target_term": "hallucinated term",
                        "category": "chemical",
                        "quality_score": 0.99,
                    },
                    {
                        "candidate_id": 99,
                        "target_term": "chlorure de sodium",
                        "category": "chemical",
                    },
                ]
            }
        ),
        reference_text="La solution contient du chlorure de sodium.",
        candidates=candidates,
        source_tag="llm_refiner_chem",
    )

    assert [term.target_terms[0] for term in terms] == ["chlorure de sodium"]
    assert terms[0].source == "spacy_ngram+pubchem+llm_refiner_chem"
    assert terms[0].term_group == "refined"
    assert terms[0].verified_by == ("pubchem",)
    assert terms[0].decision == "keep_refined"


def test_llm_refiner_keeps_candidate_category_and_discards_overlapping_terms() -> None:
    candidates = [
        DatasetTerminologyTerm(
            target_terms=("European Economic Community",),
            category="institution",
            source="llm_legal",
            confidence=0.8,
        ),
        DatasetTerminologyTerm(
            target_terms=("Community",),
            category="other",
            source="spacy_ngram",
            confidence=0.99,
        ),
    ]

    terms = parse_llm_refined_terms(
        json.dumps(
            {
                "terms": [
                    {"candidate_id": 1, "category": "legal_act", "quality_score": 0.99},
                    {"candidate_id": 0, "category": "other", "quality_score": 0.8},
                ]
            }
        ),
        reference_text="The European Economic Community shall act.",
        candidates=candidates,
        source_tag="llm_refiner_jrc",
    )

    assert [term.target_terms[0] for term in terms] == ["European Economic Community"]
    assert terms[0].category == "institution"


def test_llm_refiner_payload_summarizes_external_evidence_without_variants() -> None:
    payload = llm_refiner_candidate_payload(
        [
            DatasetTerminologyTerm(
                target_terms=("European Economic Community",),
                category="institution",
                source="legal_llm+local_iate+wikidata",
                verified_by=("local_iate", "wikidata"),
                candidates={
                    "local_iate": ["EEC", "European Economic Community"],
                    "wikidata": [
                        "European Economic Community",
                        "EEC",
                        "European Common Market",
                        "ECM",
                    ],
                },
            )
        ]
    )

    assert payload[0]["evidence_source_count"] == 2
    assert payload[0]["variant_count"] == 3
    assert "candidates" not in payload[0]


def test_llm_terminology_refiner_uses_candidate_ids_only() -> None:
    refiner = LLMTerminologyRefiner(client=_FakeRefinerClient(), model="gpt-test")
    terms = refiner.refine(
        text="La solution contient du chlorure de sodium.",
        target_language="French",
        candidates=[
            DatasetTerminologyTerm(
                target_terms=("chlorure de sodium",),
                reference_candidates=("chlorure de sodium",),
                category="chemical",
                source="llm_target",
                verified_by=("pubchem",),
                confidence=0.8,
            ),
            DatasetTerminologyTerm(
                target_terms=("solution",),
                reference_candidates=("solution",),
                category="other",
                source="spacy_ngram",
                confidence=0.4,
            ),
        ],
        domain="chemistry",
        max_terms=5,
    )

    assert [term.target_terms[0] for term in terms] == ["chlorure de sodium"]
    assert "llm_refiner_chem" in terms[0].source


def test_target_terminology_extractor_deduplicates_terms() -> None:
    class _DuplicateExtractor:
        def extract(
            self,
            text: str,
            max_terms: int,
            target_language: str = "",
        ) -> list[DatasetTerminologyTerm]:
            del text, target_language
            return [
                DatasetTerminologyTerm(target_terms=("chlorure de sodium",), confidence=0.6),
                DatasetTerminologyTerm(target_terms=("chlorure de sodium",), confidence=0.8),
            ][:max_terms]

    generator = DatasetTerminologyGenerator(max_terms=10, extractor=_DuplicateExtractor())
    terms = generator.generate(
        source_text="Ignored.",
        reference_text="La solution contient du chlorure de sodium.",
        target_language="French",
    )

    target_terms = [term.target_terms[0] for term in terms]
    assert len(target_terms) == len(set(target_terms))
    assert terms[0].confidence == 0.8


def test_generator_attaches_iate_same_language_variants() -> None:
    generator = DatasetTerminologyGenerator(
        max_terms=5,
        extractor=_FakeExtractor(),
        use_iate=True,
        iate_client=_FakeIATEClient(),
    )

    terms = generator.generate(
        source_text="The solution contains sodium chloride.",
        reference_text="La solution contient du chlorure de sodium.",
        target_language="French",
    )

    assert terms[0].verified_by == ("iate",)
    assert terms[0].candidates == {"iate": ["chlorure de sodium", "sel de table"]}


def test_generator_unions_multiple_candidate_extractors() -> None:
    class _ExtractorA:
        def extract(
            self,
            text: str,
            max_terms: int,
            target_language: str = "",
        ) -> list[DatasetTerminologyTerm]:
            del text, max_terms, target_language
            return [
                DatasetTerminologyTerm(
                    target_terms=("European Economic Community",),
                    confidence=0.7,
                )
            ]

    class _ExtractorB:
        def extract(
            self,
            text: str,
            max_terms: int,
            target_language: str = "",
        ) -> list[DatasetTerminologyTerm]:
            del text, max_terms, target_language
            return [DatasetTerminologyTerm(target_terms=("Council of Europe",), confidence=0.8)]

    generator = DatasetTerminologyGenerator(
        max_terms=10,
        extractors=(_ExtractorA(), _ExtractorB()),
    )

    terms = generator.generate(
        source_text="Ignored.",
        reference_text="European Economic Community and Council of Europe.",
        target_language="English",
    )

    assert [term.target_terms[0] for term in terms] == [
        "Council of Europe",
        "European Economic Community",
    ]


def test_spacy_extractor_returns_exact_ngram_spans() -> None:
    extractor = SpaCyTerminologyExtractor(max_ngram_tokens=4)

    terms = extractor.extract(
        text="The controlled substances include carbon tetrachloride.",
        target_language="English",
        max_terms=10,
    )

    target_terms = [term.target_terms[0] for term in terms]
    assert "controlled substances" in target_terms
    assert "carbon tetrachloride" in target_terms
    assert all(term.source.startswith("spacy_") for term in terms)

def test_stanza_candidate_cleanup_rejects_internal_separators_and_citations() -> None:
    assert not stanza_candidate_surface_is_clean(
        "containment, recovery, recycling or destruction of controlled substances"
    )
    assert not stanza_candidate_surface_is_clean("paragraph 1 of this Article")
    assert not stanza_candidate_surface_is_clean("European Agreement of 14 May 1962")
    assert not stanza_candidate_surface_is_clean("Artikels 2")
    assert not stanza_candidate_surface_is_clean("Übereinkommens vom 14")
    assert not stanza_candidate_surface_is_clean("May")
    assert not stanza_candidate_surface_is_clean("5")
    assert not stanza_candidate_surface_is_clean("DEM")


def test_make_stanza_terms_rejects_punctuation_crossing_span() -> None:
    word = SimpleNamespace(id=1, upos="NOUN", start_char=0, end_char=47)

    terms = make_stanza_terms(
        text="containment, recovery, recycling of substances",
        words=[word],
        source="stanza_ud_dependency",
        confidence=0.72,
        reason="test",
    )

    assert terms == []


def test_stanza_span_confidence_penalizes_longer_spans() -> None:
    short_words = [
        SimpleNamespace(upos="PROPN"),
        SimpleNamespace(upos="PROPN"),
        SimpleNamespace(upos="PROPN"),
    ]
    long_words = [
        SimpleNamespace(upos="PROPN"),
        SimpleNamespace(upos="PROPN"),
        SimpleNamespace(upos="PROPN"),
        SimpleNamespace(upos="ADP"),
        SimpleNamespace(upos="DET"),
        SimpleNamespace(upos="PROPN"),
    ]

    assert stanza_span_confidence(short_words, 0.72) > stanza_span_confidence(
        long_words,
        0.72,
    )


def test_stanza_span_confidence_downranks_single_tokens() -> None:
    single_word = [SimpleNamespace(upos="PROPN", text="Agreement")]
    phrase = [
        SimpleNamespace(upos="PROPN", text="European"),
        SimpleNamespace(upos="PROPN", text="Economic"),
        SimpleNamespace(upos="PROPN", text="Community"),
    ]

    assert stanza_span_confidence(single_word, 0.72) < stanza_span_confidence(
        phrase,
        0.72,
    )


def test_generator_uses_target_reference_and_pubchem_without_llm() -> None:
    generator = DatasetTerminologyGenerator(
        max_terms=5,
        use_pubchem=True,
        pubchem_client=_FakePubChemClient(),
        extractor=_FakeExtractor(),
    )

    terms = generator.generate(
        source_text="The source can be ignored by target-only extraction.",
        reference_text="La solution contient du chlorure de sodium.",
        target_language="French",
    )

    assert len(terms) == 1
    assert terms[0].source_term == ""
    assert terms[0].target_terms == ("chlorure de sodium",)
    assert terms[0].source == "fake_ner+pubchem"
    assert terms[0].term_group == "verified"
    assert terms[0].verified_by == ("pubchem",)
    assert terms[0].candidates == {"pubchem": ["sodium chloride", "chlorure de sodium"]}


def test_generator_uses_llm_target_candidates_before_database_checks() -> None:
    generator = DatasetTerminologyGenerator(
        client=_FakeClient(),
        model="gpt-test",
        max_terms=5,
        use_llm=True,
        use_pubchem=True,
        pubchem_client=_FakePubChemClient(),
        extractor=TargetTerminologyExtractor(),
    )

    terms = generator.generate(
        source_text="Ignored source text.",
        reference_text="La solution contient du chlorure de sodium.",
        target_language="French",
    )

    assert terms[0].target_terms == ("chlorure de sodium",)
    assert terms[0].source == "llm_target+stanza_ud_dependency+stanza_ud_ngram+pubchem"
    assert terms[0].term_group == "verified"
    assert terms[0].verified_by == ("pubchem",)


def test_select_dataset_terms_keeps_target_terms_by_confidence() -> None:
    terms = [
        DatasetTerminologyTerm(target_terms=("low",), confidence=0.1),
        DatasetTerminologyTerm(target_terms=("high",), confidence=0.9),
        DatasetTerminologyTerm(target_terms=(), confidence=1.0),
        DatasetTerminologyTerm(target_terms=("drop",), confidence=1.0, decision="drop"),
    ]

    selected = select_dataset_terms(terms, max_terms=2, confidence_threshold=0.0)

    assert [term.target_terms[0] for term in selected] == ["high", "low"]


def test_preserve_detection_only_keeps_compact_units_and_identifiers() -> None:
    assert should_preserve_dataset_term("55 to 65 °C", "unit")
    assert should_preserve_dataset_term("700 ppm", "unit")
    assert should_preserve_dataset_term("SEQ ID NO: 10", "identifier")
    assert should_preserve_dataset_term("Li2O", "chemical")

    assert not should_preserve_dataset_term("one or more dosages per day", "unit")
    assert not should_preserve_dataset_term("40% of the weight of the starch product", "unit")
    assert not should_preserve_dataset_term("quantitative trait locus (QTL)", "identifier")


def test_terminology_cache_round_trip(tmp_path: Path) -> None:
    cache_path = tmp_path / "terminology-cache.jsonl"
    term = DatasetTerminologyTerm(
        source_term="",
        target_terms=("Li2O",),
        category="identifier",
        source="regex",
        confidence=0.85,
        decision="preserve",
    )

    append_terminology_cache(cache_path, "cache-key", [term])

    assert load_terminology_cache(cache_path) == {"cache-key": [term.to_json()]}


def test_load_manifest_terminology_indexes_by_source_language_and_text_field(
    tmp_path: Path,
) -> None:
    manifest_path = tmp_path / "epo-subset-2-manifest.jsonl"
    terminology = [
        DatasetTerminologyTerm(
            source_term="",
            target_terms=("Festelektrolyt",),
            category="material",
        ).to_json()
    ]
    manifest_path.write_text(
        json.dumps(
            {
                "source_id": "EP-1",
                "target_language_code": "de",
                "text_field": "context",
                "terminology": terminology,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    assert load_manifest_terminology(tmp_path) == {("EP-1", "de", "context"): terminology}
