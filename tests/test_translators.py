import sqlite3

from chem_machine_translation.core.schemas import Document
from chem_machine_translation.translation.iate import (
    IATEEntryMetadata,
    IATETermTranslation,
    IATEClient,
    LocalIATEClient,
    iate_language_code,
    parse_iate_synonyms,
    parse_iate_translation,
)
from chem_machine_translation.translation.prompts import (
    build_initial_translation_prompt,
    translator_system_prompt,
)
from chem_machine_translation.translation.terminology import (
    ExtractedTerm,
    LLMTerminologyLayer,
    ManifestTerminologyLayer,
    StaticTerminologyLayer,
    TerminologyContext,
    parse_extracted_terms,
    parse_refined_terms,
)
from chem_machine_translation.translation.translators import DryRunTranslator, OneShotTranslator
from chem_machine_translation.config import Settings
from chem_machine_translation.translation.providers import resolve_provider_settings
from chem_machine_translation.translation.wikidata import (
    WikidataEntityMetadata,
    WikidataTermTranslation,
    WikidataClient,
    wikidata_language_code,
)


def test_dry_run_translator_returns_source_text() -> None:
    document = Document(
        dataset="dolma",
        source_id="1",
        text="Preserve CO2 and Zr/ZIF-8 notation.",
        metadata={},
    )

    result = DryRunTranslator().translate(document, target_language="German")

    assert result.translated_text == document.text
    assert result.target_language == "German"
    assert result.strategy == "dry-run"


def test_provider_settings_keep_openai_and_opencode_credentials_separate() -> None:
    settings = Settings(
        openai_api_key="openai-key",
        openai_base_url="https://api.openai.test/v1",
        opencode_api_key="opencode-key",
        opencode_base_url="https://opencode.test/v1",
    )

    assert resolve_provider_settings(
        provider="openai", settings=settings, base_url=None
    ) == ("openai-key", "https://api.openai.test/v1", "responses", None)
    assert resolve_provider_settings(
        provider="opencode", settings=settings, base_url=None
    ) == ("opencode-key", "https://opencode.test/v1", "chat_completions", "disabled")


class _FakeResponse:
    def __init__(self, output_text: str) -> None:
        self.output_text = output_text


class _FakeResponses:
    def __init__(self, outputs: list[str]) -> None:
        self.outputs = outputs
        self.calls = []

    def create(self, **kwargs) -> _FakeResponse:
        self.calls.append(kwargs)
        return _FakeResponse(self.outputs.pop(0))


class _FakeClient:
    def __init__(self, outputs: list[str]) -> None:
        self.responses = _FakeResponses(outputs)


class _FakeProvider:
    name = "fake"

    def __init__(self, output: str) -> None:
        self.output = output
        self.calls = []

    def generate(self, **kwargs) -> str:
        self.calls.append(kwargs)
        return self.output


class _FakeWikidataClient:
    def __init__(self, translations: dict[str, WikidataTermTranslation | None]) -> None:
        self.translations = translations
        self.calls = []

    def translate_term(
        self,
        source_term: str,
        source_language_code: str,
        target_language_code: str,
    ) -> WikidataTermTranslation | None:
        self.calls.append((source_term, source_language_code, target_language_code))
        return self.translations.get(source_term)


class _FakeIATEClient:
    def __init__(self, translations: dict[str, IATETermTranslation | None]) -> None:
        self.translations = translations
        self.calls = []

    def translate_term(
        self,
        source_term: str,
        source_language_code: str,
        target_language_code: str,
    ) -> IATETermTranslation | None:
        self.calls.append((source_term, source_language_code, target_language_code))
        return self.translations.get(source_term)


def test_wikidata_synonyms_require_an_exact_same_language_entity_term() -> None:
    client = WikidataClient(endpoint="https://example.test/wikidata")
    payloads = iter(
        [
            {"search": [{"id": "Q1"}]},
            {
                "entities": {
                    "Q1": {
                        "labels": {"en": {"value": "European Union"}},
                        "aliases": {
                            "en": [
                                {"value": "EU"},
                                {"value": "the Union"},
                            ]
                        },
                    }
                }
            },
        ]
    )
    client._get_json = lambda params: next(payloads)  # type: ignore[method-assign]

    assert client.lookup_synonyms("EU", "en") == [
        "European Union",
        "EU",
        "the Union",
    ]


def test_wikidata_synonyms_reject_a_fuzzy_search_result() -> None:
    client = WikidataClient(endpoint="https://example.test/wikidata")
    payloads = iter(
        [
            {"search": [{"id": "Q1"}]},
            {"entities": {"Q1": {"labels": {"en": {"value": "water"}}}}},
        ]
    )
    client._get_json = lambda params: next(payloads)  # type: ignore[method-assign]

    assert client.lookup_synonyms("wate", "en") == []


def test_wikidata_metadata_returns_exact_match_entity_classes() -> None:
    client = WikidataClient(endpoint="https://example.test/wikidata")
    payloads = iter(
        [
            {"search": [{"id": "Q1"}]},
            {
                "entities": {
                    "Q1": {
                        "labels": {"en": {"value": "sodium chloride"}},
                        "descriptions": {"en": {"value": "chemical compound"}},
                        "claims": {
                            "P31": [
                                {"mainsnak": {"datavalue": {"value": {"id": "Q2"}}}}
                            ],
                            "P279": [
                                {"mainsnak": {"datavalue": {"value": {"id": "Q3"}}}}
                            ],
                        },
                    }
                }
            },
            {
                "entities": {
                    "Q2": {"labels": {"en": {"value": "chemical compound"}}},
                    "Q3": {"labels": {"en": {"value": "salt"}}},
                }
            },
        ]
    )
    client._get_json = lambda params: next(payloads)  # type: ignore[method-assign]

    assert client.lookup_metadata("sodium chloride", "en") == WikidataEntityMetadata(
        entity_id="Q1",
        description="chemical compound",
        instance_of=("chemical compound",),
        subclass_of=("salt",),
    )


def test_one_shot_translator_uses_provider_and_terminology() -> None:
    document = Document(
        dataset="dolma",
        source_id="1",
        text="CO2 hydrogenation to formate at 80 °C.",
        metadata={},
    )
    provider = _FakeProvider("German translation preserving CO2.")
    translator = OneShotTranslator(
        provider=provider,
        model="model-a",
        terminology_layer=StaticTerminologyLayer("CO2 -> CO2"),
    )

    result = translator.translate(document, target_language="German", source_language="English")

    assert result.translated_text == "German translation preserving CO2."
    assert result.strategy == "one-shot"
    assert result.model == "model-a"
    assert "CO2 -> CO2" in result.terminology_section
    assert provider.calls[0]["model"] == "model-a"
    assert "CO2 -> CO2" in provider.calls[0]["user_prompt"]


def test_empty_terminology_section_is_not_added_to_prompt() -> None:
    document = Document(
        dataset="dolma",
        source_id="1",
        text="CO2 hydrogenation to formate at 80 °C.",
        metadata={},
    )

    prompt = build_initial_translation_prompt(
        document=document,
        target_language="German",
        source_language="English",
    )

    assert "Approved terminology" not in prompt
    assert "Source document:" in prompt


def test_one_shot_translator_can_use_legal_prompt() -> None:
    document = Document(
        dataset="jrc_acquis",
        source_id="1",
        text="Article 1 This Regulation shall apply.",
        metadata={},
    )
    provider = _FakeProvider("Legal translation.")
    translator = OneShotTranslator(
        provider=provider,
        model="model-a",
        translation_domain="legal",
    )

    translator.translate(document, target_language="Spanish", source_language="English")

    assert "senior legal translator" in provider.calls[0]["system_prompt"]
    assert "legal document" in provider.calls[0]["user_prompt"]
    assert translator_system_prompt("generic").startswith("You are a senior professional")


def test_manifest_terminology_layer_filters_term_groups() -> None:
    document = Document(
        dataset="parallel_manifest",
        source_id="1",
        text="Agreement text.",
        metadata={
            "terminology": [
                {
                    "target_terms": ["Comité mixto del EEE"],
                    "category": "institution",
                    "term_group": "verified",
                },
                {
                    "target_terms": ["texto común"],
                    "category": "other",
                    "term_group": "llm",
                },
            ]
        },
    )
    layer = ManifestTerminologyLayer(term_groups=("verified",))

    section = layer.build_prompt_section(
        TerminologyContext(
            document=document,
            target_language="Spanish",
            source_language="English",
        )
    )

    assert "Comité mixto del EEE [institution; verified]" in section
    assert "texto común" not in section


def test_parse_extracted_terms_from_json() -> None:
    terms = parse_extracted_terms(
        """
        {
          "terms": [
            {
              "source_term": "CO2 hydrogenation",
              "category": "process",
              "reason": "reaction phrase"
            },
            {
              "source_term": "",
              "category": "other",
              "reason": "ignored"
            }
          ]
        }
        """
    )

    assert len(terms) == 1
    assert terms[0].source_term == "CO2 hydrogenation"
    assert terms[0].category == "process"


def test_llm_terminology_layer_extracts_and_formats_terms() -> None:
    document = Document(
        dataset="dolma",
        source_id="1",
        text="CO2 hydrogenation to formate at 80 °C.",
        metadata={},
    )
    client = _FakeClient(
        [
            (
                '{"terms": ['
                '{"source_term": "CO2 hydrogenation", "category": "process", '
                '"reason": "reaction phrase"}, '
                '{"source_term": "80 °C", "category": "unit", "reason": "condition"}'
                "]}"
            )
        ]
    )
    layer = LLMTerminologyLayer(client=client, model="gpt-4.1-mini", max_terms=5)

    section = layer.build_prompt_section(
        TerminologyContext(
            document=document,
            target_language="German",
            source_language="English",
        )
    )

    assert "LLM-extracted terminology focus list:" in section
    assert "CO2 hydrogenation [process]" in section
    assert "80 °C [unit]" in section
    assert len(client.responses.calls) == 1


def test_llm_terminology_layer_caches_terms() -> None:
    document = Document(
        dataset="dolma",
        source_id="1",
        text="The catalyst was stable.",
        metadata={},
    )
    client = _FakeClient(
        ['{"terms": [{"source_term": "catalyst", "category": "chemical", "reason": "term"}]}']
    )
    layer = LLMTerminologyLayer(client=client, model="gpt-4.1-mini")
    context = TerminologyContext(
        document=document,
        target_language="German",
        source_language="English",
    )

    first = layer.build_prompt_section(context=context)
    second = layer.build_prompt_section(context=context)

    assert first == second
    assert len(client.responses.calls) == 1


def test_wikidata_language_code_maps_target_languages() -> None:
    assert wikidata_language_code("German") == "de"
    assert wikidata_language_code("French") == "fr"
    assert wikidata_language_code("Spanish") == "es"
    assert wikidata_language_code("unknown") is None


def test_iate_language_code_maps_target_languages() -> None:
    assert iate_language_code("German") == "de"
    assert iate_language_code("Portuguese") == "pt"
    assert iate_language_code("Dutch") == "nl"
    assert iate_language_code("unknown") is None


def test_parse_iate_translation_from_payload() -> None:
    translation = parse_iate_translation(
        payload={
            "items": [
                {
                    "code": "ENTRY-1",
                    "language": {
                        "de": {
                            "term_entries": [
                                {"term_value": "Katalysator"},
                            ]
                        }
                    },
                }
            ]
        },
        source_term="catalyst",
        target_language_code="de",
    )

    assert translation == IATETermTranslation(
        source_term="catalyst",
        target_label="Katalysator",
        entry_id="ENTRY-1",
    )


def test_parse_iate_synonyms_requires_an_exact_same_language_match() -> None:
    payload = {
        "items": [
            {
                "language": {
                    "de": {
                        "term_entries": [
                            {"term_value": "Katalysator"},
                            {"term_value": "Katalyseur"},
                        ]
                    }
                }
            },
            {
                "language": {"de": {"term_entries": [{"term_value": "Katalysatorin"}]}},
            },
        ]
    }

    assert parse_iate_synonyms(payload, "Katalysator", "de") == [
        "Katalysator",
        "Katalyseur",
    ]
    assert parse_iate_synonyms(payload, "Katalys", "de") == []


def test_local_iate_client_reads_csv_export(tmp_path) -> None:
    csv_path = tmp_path / "iate.csv"
    csv_path.write_text(
        "entry_id,language_code,term\n"
        "IATE-1,en,catalyst\n"
        "IATE-1,de,Katalysator\n"
        "IATE-1,de,Katalyseur\n"
        "IATE-2,fr,fluor\n",
        encoding="utf-8",
    )
    client = LocalIATEClient(csv_path, auto_build_index=False)

    translation = client.translate_term("catalyst", "en", "de")
    same_language = client.translate_term("fluor", "fr", "fr")

    assert translation == IATETermTranslation(
        source_term="catalyst",
        target_label="Katalysator",
        entry_id="IATE-1",
    )
    assert same_language == IATETermTranslation(
        source_term="fluor",
        target_label="fluor",
        entry_id="IATE-2",
    )
    assert client.lookup_synonyms("Katalysator", "de") == ["Katalysator", "Katalyseur"]


def test_local_iate_client_auto_builds_sqlite_index(tmp_path) -> None:
    csv_path = tmp_path / "iate.csv"
    sqlite_path = tmp_path / "iate.sqlite"
    csv_path.write_text(
        "E_ID|L_CODE|T_TERM\n"
        "IATE-1|en|catalyst\n"
        "IATE-1|de|Katalysator\n",
        encoding="utf-8",
    )
    client = LocalIATEClient(tmp_path)

    translation = client.translate_term("catalyst", "en", "de")

    assert sqlite_path.exists()
    assert translation == IATETermTranslation(
        source_term="catalyst",
        target_label="Katalysator",
        entry_id="IATE-1",
    )


def test_local_iate_client_retains_export_metadata(tmp_path) -> None:
    csv_path = tmp_path / "iate.csv"
    csv_path.write_text(
        "E_ID|E_DOMAINS|L_CODE|T_TERM|T_TYPE|T_RELIABILITY|T_INSTITUTION\n"
        "IATE-1|chemistry;environment|en|catalyst|Term|Reliable|Commission\n",
        encoding="utf-8",
    )
    client = LocalIATEClient(tmp_path)

    assert client.lookup_metadata("catalyst", "en") == IATEEntryMetadata(
        domains=("chemistry", "environment"),
        term_type="Term",
        reliability="Reliable",
        institution="Commission",
    )


def test_local_iate_client_uses_sqlite_index(tmp_path) -> None:
    sqlite_path = tmp_path / "iate.sqlite"
    with sqlite3.connect(sqlite_path) as connection:
        connection.executescript(
            """
            CREATE TABLE terms (
                entry_id TEXT NOT NULL,
                language_code TEXT NOT NULL,
                normalized_term TEXT NOT NULL,
                term TEXT NOT NULL
            );
            CREATE INDEX idx_terms_lookup ON terms(language_code, normalized_term);
            CREATE INDEX idx_terms_entry_language ON terms(entry_id, language_code);
            """
        )
        connection.executemany(
            """
            INSERT INTO terms(entry_id, language_code, normalized_term, term)
            VALUES (?, ?, ?, ?)
            """,
            [
                ("IATE-1", "en", "catalyst", "catalyst"),
                ("IATE-1", "fr", "catalyseur", "catalyseur"),
                ("IATE-1", "fr", "catalystes", "catalystes"),
                ("IATE-2", "fr", "induit", "induit"),
                ("IATE-2", "fr", "rotor", "rotor"),
            ],
        )

    client = LocalIATEClient(sqlite_path)

    assert client.translate_term("catalyst", "en", "fr") == IATETermTranslation(
        source_term="catalyst",
        target_label="catalyseur",
        entry_id="IATE-1",
    )
    assert client.translate_term("rotor", "fr", "fr") == IATETermTranslation(
        source_term="rotor",
        target_label="rotor",
        entry_id="IATE-2",
    )
    assert client.lookup_synonyms("catalyseur", "fr") == ["catalyseur", "catalystes"]


def test_llm_terminology_layer_adds_wikidata_candidates() -> None:
    document = Document(
        dataset="dolma",
        source_id="1",
        text="The catalyst was stable.",
        metadata={},
    )
    client = _FakeClient(
        ['{"terms": [{"source_term": "catalyst", "category": "chemical", "reason": "term"}]}']
    )
    wikidata_client = _FakeWikidataClient(
        {
            "catalyst": WikidataTermTranslation(
                source_term="catalyst",
                target_label="Katalysator",
                entity_id="Q426978",
                description="substance that increases reaction rate",
            )
        }
    )
    layer = LLMTerminologyLayer(
        client=client,
        model="gpt-4.1-mini",
        wikidata_client=wikidata_client,
    )

    section = layer.build_prompt_section(
        TerminologyContext(
            document=document,
            target_language="German",
            source_language="English",
        )
    )

    assert "catalyst [chemical] | Wikidata candidate: Katalysator (Q426978)" in section
    assert wikidata_client.calls == [("catalyst", "en", "de")]


def test_llm_terminology_layer_prefers_iate_over_wikidata() -> None:
    document = Document(
        dataset="dolma",
        source_id="1",
        text="The catalyst was stable.",
        metadata={},
    )
    client = _FakeClient(
        ['{"terms": [{"source_term": "catalyst", "category": "chemical", "reason": "term"}]}']
    )
    wikidata_client = _FakeWikidataClient(
        {
            "catalyst": WikidataTermTranslation(
                source_term="catalyst",
                target_label="Wikidata Katalysator",
                entity_id="Q426978",
            )
        }
    )
    iate_client = _FakeIATEClient(
        {
            "catalyst": IATETermTranslation(
                source_term="catalyst",
                target_label="Katalysator",
                entry_id="IATE-1",
            )
        }
    )
    layer = LLMTerminologyLayer(
        client=client,
        model="gpt-4.1-mini",
        wikidata_client=wikidata_client,
        iate_client=iate_client,
    )

    section = layer.build_prompt_section(
        TerminologyContext(
            document=document,
            target_language="German",
            source_language="English",
        )
    )

    assert "catalyst [chemical] | IATE candidate: Katalysator (IATE-1)" in section
    assert wikidata_client.calls == []
    assert iate_client.calls == [("catalyst", "en", "de")]


def test_llm_terminology_layer_uses_wikidata_when_iate_missing() -> None:
    document = Document(
        dataset="dolma",
        source_id="1",
        text="The catalyst was stable.",
        metadata={},
    )
    client = _FakeClient(
        ['{"terms": [{"source_term": "catalyst", "category": "chemical", "reason": "term"}]}']
    )
    iate_client = _FakeIATEClient({"catalyst": None})
    wikidata_client = _FakeWikidataClient(
        {
            "catalyst": WikidataTermTranslation(
                source_term="catalyst",
                target_label="Katalysator",
                entity_id="Q426978",
            )
        }
    )
    layer = LLMTerminologyLayer(
        client=client,
        model="gpt-4.1-mini",
        iate_client=iate_client,
        wikidata_client=wikidata_client,
    )

    section = layer.build_prompt_section(
        TerminologyContext(
            document=document,
            target_language="German",
            source_language="English",
        )
    )

    assert "catalyst [chemical] | Wikidata candidate: Katalysator (Q426978)" in section
    assert iate_client.calls == [("catalyst", "en", "de")]
    assert wikidata_client.calls == [("catalyst", "en", "de")]


def test_llm_terminology_layer_preserves_element_symbols_without_external_lookup() -> None:
    document = Document(
        dataset="dolma",
        source_id="1",
        text="The oxide contains Mo, W, V, Cu and Sb.",
        metadata={},
    )
    client = _FakeClient(
        [
            (
                '{"terms": ['
                '{"source_term": "Mo", "category": "chemical", "reason": "element symbol"}, '
                '{"source_term": "Cu", "category": "chemical", "reason": "element symbol"}'
                "]}"
            )
        ]
    )
    iate_client = _FakeIATEClient({})
    wikidata_client = _FakeWikidataClient({})
    layer = LLMTerminologyLayer(
        client=client,
        model="gpt-4.1-mini",
        iate_client=iate_client,
        wikidata_client=wikidata_client,
    )

    section = layer.build_prompt_section(
        TerminologyContext(
            document=document,
            target_language="German",
            source_language="English",
        )
    )

    assert "Mo [chemical]" in section
    assert "Cu [chemical]" in section
    assert iate_client.calls == []
    assert wikidata_client.calls == []


def test_parse_refined_terms_updates_and_drops_rows() -> None:
    original_terms = [
        ExtractedTerm(
            source_term="aqueous solution",
            category="material",
            reason="solvent system",
            iate_target_label="wässrige Lösung",
            iate_entry_id="IATE-1",
        ),
        ExtractedTerm(
            source_term="dryer",
            category="material",
            reason="equipment",
            iate_target_label="Trockenkammer",
            iate_entry_id="IATE-2",
        ),
        ExtractedTerm(
            source_term="powder P",
            category="material",
            reason="variable-like material label",
        ),
    ]

    refined_terms = parse_refined_terms(
        """
        {
          "terms": [
            {
              "source_term": "aqueous solution",
              "decision": "keep",
              "final_translation": "wässrige Lösung",
              "confidence": 0.93,
              "reason": "standard term"
            },
            {
              "source_term": "dryer",
              "decision": "replace",
              "final_translation": "Trockner",
              "confidence": 0.91,
              "reason": "candidate is too specific"
            },
            {
              "source_term": "powder P",
              "decision": "drop",
              "final_translation": "",
              "confidence": 0.2,
              "reason": "not useful terminology"
            }
          ]
        }
        """,
        original_terms,
    )

    assert refined_terms[0].refinement_decision == "keep"
    assert refined_terms[0].final_translation == "wässrige Lösung"
    assert refined_terms[0].refinement_confidence == 0.93
    assert refined_terms[1].refinement_decision == "replace"
    assert refined_terms[1].final_translation == "Trockner"
    assert refined_terms[2].refinement_decision == "drop"


def test_llm_terminology_layer_refines_candidates_before_prompting() -> None:
    document = Document(
        dataset="dolma",
        source_id="1",
        text="An aqueous solution is dried in a dryer with Mo.",
        metadata={},
    )
    client = _FakeClient(
        [
            (
                '{"terms": ['
                '{"source_term": "aqueous solution", "category": "material", '
                '"reason": "solvent system"}, '
                '{"source_term": "dryer", "category": "material", "reason": "equipment"}, '
                '{"source_term": "Mo", "category": "chemical", "reason": "element symbol"}, '
                '{"source_term": "powder P", "category": "material", "reason": "label"}'
                "]}"
            ),
            (
                '{"terms": ['
                '{"source_term": "aqueous solution", "decision": "keep", '
                '"final_translation": "wässrige Lösung", "confidence": 0.93, '
                '"reason": "standard term"}, '
                '{"source_term": "dryer", "decision": "replace", '
                '"final_translation": "Trockner", "confidence": 0.91, '
                '"reason": "generic equipment"}, '
                '{"source_term": "Mo", "decision": "preserve", '
                '"final_translation": "Mo", "confidence": 0.99, "reason": "element symbol"}, '
                '{"source_term": "powder P", "decision": "drop", '
                '"final_translation": "", "confidence": 0.2, "reason": "variable-like label"}'
                "]}"
            ),
        ]
    )
    iate_client = _FakeIATEClient(
        {
            "aqueous solution": IATETermTranslation(
                source_term="aqueous solution",
                target_label="wässrige Lösung",
                entry_id="IATE-1",
            ),
            "dryer": IATETermTranslation(
                source_term="dryer",
                target_label="Trockenkammer",
                entry_id="IATE-2",
            ),
        }
    )
    layer = LLMTerminologyLayer(
        client=client,
        model="gpt-4.1-mini",
        iate_client=iate_client,
        refine_terms=True,
    )

    section = layer.build_prompt_section(
        TerminologyContext(
            document=document,
            target_language="German",
            source_language="English",
        )
    )

    assert "Refined terminology instructions:" in section
    assert "aqueous solution -> wässrige Lösung" in section
    assert "dryer -> Trockner" in section
    assert "Mo" in section
    assert "powder P" not in section
    assert "confidence=0.93" in section
    assert len(client.responses.calls) == 2


def test_refinement_gate_rejects_low_confidence_and_generic_terms() -> None:
    original_terms = [
        ExtractedTerm(
            source_term="aqueous suspension",
            category="material",
            reason="solvent system",
            iate_target_label="wässrige Suspension",
            iate_entry_id="IATE-1",
        ),
        ExtractedTerm(
            source_term="system",
            category="other",
            reason="generic noun",
            iate_target_label="System",
            iate_entry_id="IATE-2",
        ),
        ExtractedTerm(
            source_term="apparatus",
            category="other",
            reason="generic patent noun",
            iate_target_label="Apparat",
            iate_entry_id="IATE-3",
        ),
    ]

    refined_terms = parse_refined_terms(
        """
        {
          "terms": [
            {
              "source_term": "aqueous suspension",
              "decision": "keep",
              "final_translation": "wässrige Suspension",
              "confidence": 0.84,
              "reason": "almost good, but below threshold"
            },
            {
              "source_term": "system",
              "decision": "keep",
              "final_translation": "System",
              "confidence": 0.9,
              "reason": "generic term should require higher confidence"
            },
            {
              "source_term": "apparatus",
              "decision": "keep",
              "final_translation": "Vorrichtung",
              "confidence": 0.96,
              "reason": "high-confidence patent term"
            }
          ]
        }
        """,
        original_terms,
    )

    assert [term.source_term for term in refined_terms] == ["apparatus"]
    assert refined_terms[0].final_translation == "Vorrichtung"
