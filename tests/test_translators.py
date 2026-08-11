from chem_machine_translation.core.schemas import Document
from chem_machine_translation.translation.iate import (
    IATETermTranslation,
    iate_language_code,
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
from chem_machine_translation.translation.wikidata import (
    WikidataTermTranslation,
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
