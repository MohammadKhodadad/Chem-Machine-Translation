import json
from pathlib import Path

from chem_machine_translation.data.terminology import (
    DATASET_REFERENCE_CANDIDATE_SYSTEM_PROMPT,
    DATASET_TERM_EXTRACTOR_SYSTEM_PROMPT,
    DATASET_TERM_REFINER_SYSTEM_PROMPT,
    DatasetTerminologyGenerator,
    DatasetTerminologyTerm,
    append_terminology_cache,
    dataset_term_from_json,
    load_manifest_terminology,
    load_terminology_cache,
    parse_dataset_extracted_terms,
    parse_reference_candidate_terms,
    parse_refined_dataset_terms,
    select_dataset_terms,
    should_preserve_dataset_term,
)


def test_dataset_term_prompts_are_strict_and_language_pair_neutral() -> None:
    assert "source text may be in any language" in DATASET_TERM_EXTRACTOR_SYSTEM_PROMPT
    assert "Use only spans that appear in the target reference" in (
        DATASET_REFERENCE_CANDIDATE_SYSTEM_PROMPT
    )
    assert "source and target texts may be any language pair" in DATASET_TERM_REFINER_SYSTEM_PROMPT
    assert "External candidates are validation/canonicalization evidence only" in (
        DATASET_TERM_REFINER_SYSTEM_PROMPT
    )
    assert "Do not extract generic patent scaffolding" in DATASET_TERM_EXTRACTOR_SYSTEM_PROMPT
    assert "language-neutral" in DATASET_TERM_REFINER_SYSTEM_PROMPT


def test_dataset_term_round_trips_json_shape() -> None:
    term = DatasetTerminologyTerm(
        source_term="solid electrolyte",
        target_terms=("Festelektrolyt",),
        category="material",
        source="llm+iate",
        confidence=0.91,
        decision="keep",
        reason="Standard term",
        candidates={"iate": ["Festelektrolyt"]},
    )

    loaded = dataset_term_from_json(term.to_json())

    assert loaded == term


def test_parse_dataset_extracted_terms_ignores_invalid_rows() -> None:
    terms = parse_dataset_extracted_terms(
        json.dumps(
            {
                "terms": [
                    {
                        "source_term": "Mo",
                        "category": "chemical",
                        "reason": "element symbol",
                    },
                    {"source_term": ""},
                ]
            }
        )
    )

    assert len(terms) == 1
    assert terms[0].source_term == "Mo"
    assert terms[0].category == "chemical"


def test_parse_refined_dataset_terms_applies_confidence_gate() -> None:
    original_terms = [
        DatasetTerminologyTerm(
            source_term="solid electrolyte",
            target_terms=("Festelektrolyt",),
            reference_candidates=("Festelektrolyt",),
            category="material",
            source="llm+iate",
            confidence=0.75,
        ),
        DatasetTerminologyTerm(
            source_term="method",
            target_terms=("Verfahren",),
            category="other",
            source="llm+iate",
            confidence=0.75,
        ),
    ]

    refined = parse_refined_dataset_terms(
        json.dumps(
            {
                "terms": [
                    {
                        "source_term": "solid electrolyte",
                        "decision": "keep",
                        "target_terms": ["Festelektrolyt"],
                        "confidence": 0.93,
                        "reason": "Context-relevant material term",
                    },
                    {
                        "source_term": "method",
                        "decision": "drop",
                        "target_terms": [],
                        "confidence": 0.2,
                        "reason": "Too generic",
                    },
                ]
            }
        ),
        original_terms,
        confidence_threshold=0.85,
        max_terms=5,
    )

    assert [term.source_term for term in refined] == ["solid electrolyte"]
    assert refined[0].target_terms == ("Festelektrolyt",)
    assert refined[0].decision == "keep"


def test_refiner_drop_decision_filters_generic_and_clause_like_terms() -> None:
    terms = [
        DatasetTerminologyTerm(
            source_term="gastrointestinal tract",
            target_terms=("tube digestif",),
            reference_candidates=("tube digestif",),
            category="other",
            source="reference+refined",
            confidence=0.95,
            decision="keep_reference",
        ),
        DatasetTerminologyTerm(
            source_term="cow",
            target_terms=("une vache",),
            reference_candidates=("une vache",),
            category="other",
            source="reference+refined",
            confidence=0.99,
            decision="drop",
        ),
        DatasetTerminologyTerm(
            source_term="working amount",
            target_terms=("une quantité de travail",),
            reference_candidates=("une quantité de travail",),
            category="other",
            source="reference+refined",
            confidence=0.99,
            decision="drop",
        ),
        DatasetTerminologyTerm(
            source_term="one or more nutrients selected from minerals, vitamins and amino acids",
            target_terms=(
                "un ou plusieurs nutriments choisis parmi des minéraux, des vitamines et "
                "des acides aminés",
            ),
            reference_candidates=(
                "un ou plusieurs nutriments choisis parmi des minéraux, des vitamines et "
                "des acides aminés",
            ),
            category="other",
            source="reference+refined",
            confidence=0.99,
            decision="drop",
        ),
        DatasetTerminologyTerm(
            source_term="starch is at least 40% of the weight of the starch product",
            target_terms=("l'amidon représente au moins 40 % du poids du produit d'amidon",),
            reference_candidates=(
                "l'amidon représente au moins 40 % du poids du produit d'amidon",
            ),
            category="unit",
            source="reference+refined",
            confidence=0.99,
            decision="drop",
        ),
    ]

    selected = select_dataset_terms(terms, confidence_threshold=0.85, max_terms=10)

    assert [term.source_term for term in selected] == ["gastrointestinal tract"]


def test_select_dataset_terms_keeps_refiner_approved_terms_without_english_filters() -> None:
    terms = [
        DatasetTerminologyTerm(
            source_term="55 to 65 °C",
            target_terms=("55 à 65 °C",),
            reference_candidates=("55 à 65 °C",),
            category="unit",
            source="reference+refined",
            confidence=0.95,
            decision="keep_reference",
        ),
        DatasetTerminologyTerm(
            source_term="marker assisted selection",
            target_terms=("sélection assistée par marqueur",),
            reference_candidates=("sélection assistée par marqueur",),
            category="process",
            source="reference+refined",
            confidence=0.94,
            decision="keep_reference",
        ),
        DatasetTerminologyTerm(
            source_term="quantitative trait locus (QTL)",
            target_terms=("locus de caractère quantitatif (QTL)",),
            reference_candidates=("locus de caractère quantitatif (QTL)",),
            category="identifier",
            source="reference+refined",
            confidence=0.93,
            decision="keep_reference",
        ),
        DatasetTerminologyTerm(
            source_term="valid non-English technical phrase",
            target_terms=("terme technique valide",),
            reference_candidates=("terme technique valide",),
            category="other",
            source="reference+refined",
            confidence=0.92,
            decision="keep_reference",
        ),
    ]

    selected = select_dataset_terms(terms, confidence_threshold=0.85, max_terms=10)

    assert [term.source_term for term in selected] == [
        "55 to 65 °C",
        "marker assisted selection",
        "quantitative trait locus (QTL)",
        "valid non-English technical phrase",
    ]


def test_parse_reference_candidate_terms_adds_reference_spans() -> None:
    original_terms = [
        DatasetTerminologyTerm(
            source_term="gastrointestinal tract",
            category="other",
            source="llm",
        )
    ]

    terms = parse_reference_candidate_terms(
        json.dumps(
            {
                "terms": [
                    {
                        "source_term": "gastrointestinal tract",
                        "reference_candidates": ["tractus gastro-intestinal"],
                        "confidence": 0.96,
                        "reason": "Exact target reference span.",
                    }
                ]
            }
        ),
        original_terms,
    )

    assert terms[0].target_terms == ("tractus gastro-intestinal",)
    assert terms[0].reference_candidates == ("tractus gastro-intestinal",)
    assert terms[0].source == "reference"


def test_refinement_can_keep_reference_and_external_candidates_separate() -> None:
    original_terms = [
        DatasetTerminologyTerm(
            source_term="gastrointestinal tract",
            target_terms=("tube digestif",),
            reference_candidates=("tube digestif",),
            category="other",
            source="reference+iate",
            confidence=0.85,
            candidates={"iate": ["tractus gastro-intestinal"]},
        )
    ]

    refined = parse_refined_dataset_terms(
        json.dumps(
            {
                "terms": [
                    {
                        "source_term": "gastrointestinal tract",
                        "decision": "keep_both",
                        "target_terms": [],
                        "confidence": 0.94,
                        "reason": "Reference and external candidates are valid variants.",
                    }
                ]
            }
        ),
        original_terms,
        confidence_threshold=0.85,
        max_terms=5,
    )

    assert refined[0].target_terms == ("tube digestif", "tractus gastro-intestinal")
    assert refined[0].reference_candidates == ("tube digestif",)
    assert refined[0].candidates == {"iate": ["tractus gastro-intestinal"]}


def test_lookup_miss_is_kept_as_llm_only_candidate() -> None:
    generator = DatasetTerminologyGenerator()
    term = DatasetTerminologyTerm(
        source_term="ion-conductive polymer matrix",
        category="material",
        source="llm",
        reason="Technical patent phrase",
    )

    enriched = generator.add_target_candidates(
        term=term,
        source_language="English",
        target_language="German",
    )

    assert enriched.source == "llm_only"
    assert enriched.target_terms == ()
    assert enriched.confidence == 0.5


def test_llm_only_terms_survive_refinement_when_no_decision_is_returned() -> None:
    original_terms = [
        DatasetTerminologyTerm(
            source_term="ion-conductive polymer matrix",
            category="material",
            source="llm_only",
            confidence=0.5,
        )
    ]

    refined = parse_refined_dataset_terms(
        json.dumps({"terms": []}),
        original_terms,
        confidence_threshold=0.85,
        max_terms=5,
    )

    assert len(refined) == 1
    assert refined[0].source == "llm_only"
    assert refined[0].decision == "llm_only"


def test_preserve_detection_only_keeps_compact_units_and_identifiers() -> None:
    assert should_preserve_dataset_term("55 to 65 °C", "unit")
    assert should_preserve_dataset_term("700 ppm or less", "unit")
    assert should_preserve_dataset_term("SEQ ID NO: 10", "identifier")
    assert should_preserve_dataset_term("Li2O", "chemical")

    assert not should_preserve_dataset_term("one or more dosages per day", "unit")
    assert not should_preserve_dataset_term("40% of the weight of the starch product", "unit")
    assert not should_preserve_dataset_term("moisture level of about 20-30%", "unit")
    assert not should_preserve_dataset_term("quantitative trait locus (QTL)", "identifier")
    assert not should_preserve_dataset_term("specific markers", "identifier")


def test_terminology_cache_round_trip(tmp_path: Path) -> None:
    cache_path = tmp_path / "terminology-cache.jsonl"
    term = DatasetTerminologyTerm(
        source_term="Mo",
        target_terms=("Mo",),
        category="chemical",
        source="preserve",
        confidence=1.0,
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
            source_term="solid electrolyte",
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
