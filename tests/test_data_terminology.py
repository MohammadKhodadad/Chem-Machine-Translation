import json
from pathlib import Path

from chem_machine_translation.data.terminology import (
    DatasetTerminologyTerm,
    append_terminology_cache,
    dataset_term_from_json,
    load_manifest_terminology,
    load_terminology_cache,
    parse_dataset_extracted_terms,
    parse_refined_dataset_terms,
)


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
