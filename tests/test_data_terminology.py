import json
from pathlib import Path

from chem_machine_translation.data.terminology import (
    TARGET_CANDIDATE_EXTRACTOR_SYSTEM_PROMPT,
    DatasetTerminologyGenerator,
    DatasetTerminologyTerm,
    LLMTargetCandidateExtractor,
    TargetTerminologyExtractor,
    append_terminology_cache,
    dataset_term_from_json,
    load_manifest_terminology,
    load_terminology_cache,
    parse_llm_target_candidates,
    select_dataset_terms,
    should_preserve_dataset_term,
)


class _FakePubChemClient:
    def lookup_synonyms(self, term: str) -> list[str]:
        return ["sodium chloride", "chlorure de sodium"] if term == "chlorure de sodium" else []


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


def test_target_candidate_prompt_requires_exact_target_spans() -> None:
    assert "exact spans that appear in the provided target text" in (
        TARGET_CANDIDATE_EXTRACTOR_SYSTEM_PROMPT
    )
    assert "Do not translate" in TARGET_CANDIDATE_EXTRACTOR_SYSTEM_PROMPT


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
    assert terms[0].source == "llm_target+pubchem"
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
