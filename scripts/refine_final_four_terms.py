from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from openai import OpenAI

from chem_machine_translation.config import load_settings
from chem_machine_translation.data.terminology import (
    DatasetTerminologyTerm,
    LLMTerminologyRefiner,
    dataset_term_from_json,
    deduplicate_terms,
)


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_DIR = ROOT / "benchmark_datasets"
OUTPUT_PATH = ROOT / "docs" / "final-four-extractor-refiner-results.json"

CASES = [
    {
        "item": 1,
        "label": "Chemistry, carbon gasification patent",
        "domain": "chemistry",
        "direction": "de-en",
        "example_id": "within-document:abstract:en-de:AT-503517-B1:reverse",
        "roots": [
            "google_patents_5_bidirectional_all_candidate_terms",
            "google_patents_5_bidirectional_spacy_only_terms",
        ],
    },
    {
        "item": 2,
        "label": "Chemistry, pharmaceutical salt patent",
        "domain": "chemistry",
        "direction": "ru-en",
        "example_id": "within-document:abstract:en-ru:EA-001190-B1:reverse",
        "roots": [
            "google_patents_5_bidirectional_all_candidate_terms",
            "google_patents_5_bidirectional_spacy_only_terms",
        ],
    },
    {
        "item": 3,
        "label": "JRC, additional protocol on blood-grouping reagents",
        "domain": "jrc",
        "direction": "de-en",
        "example_id": "de-en:jrc21987A0207_06:chunk-0135",
        "roots": [
            "jrc_acquis_anchored_articles_5_all_non_llm_terms",
            "jrc_acquis_anchored_articles_5_llm_terms",
            "jrc_acquis_anchored_articles_5_spacy_only_terms",
        ],
    },
    {
        "item": 4,
        "label": "JRC, agreement on racism and xenophobia observatory",
        "domain": "jrc",
        "direction": "de-fr",
        "example_id": "de-fr:jrc21999A0218_01:chunk-0453",
        "roots": [
            "jrc_acquis_anchored_articles_5_all_non_llm_terms",
            "jrc_acquis_anchored_articles_5_llm_terms",
            "jrc_acquis_anchored_articles_5_spacy_only_terms",
        ],
    },
]


def main() -> None:
    settings = load_settings()
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is required to run the LLM terminology refiner.")

    client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
    refiner = LLMTerminologyRefiner(client=client, model=settings.default_model)

    results = []
    for case in CASES:
        rows = [load_case_from_root(case, root) for root in case["roots"]]
        rows = [row for row in rows if row is not None]
        if not rows:
            raise ValueError(f"Could not find case row: {case['example_id']}")
        target_text = rows[0]["target_text"]
        target_language = rows[0]["manifest"]["target_language"]
        terms = deduplicate_terms(
            [
                term
                for row in rows
                for term in load_terms(row["manifest"].get("terminology", []))
            ]
        )
        refined = refiner.refine(
            text=target_text,
            target_language=target_language,
            candidates=terms,
            domain=case["domain"],
            max_terms=8,
        )
        results.append(
            {
                **case,
                "target_language": target_language,
                "candidate_count": len(terms),
                "verified_candidate_count": sum(1 for term in terms if term.verified_by),
                "refined_count": len(refined),
                "refined_verified_count": sum(1 for term in refined if term.verified_by),
                "refined_terms": [term.to_json() for term in refined],
            }
        )

    OUTPUT_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH}")
    for result in results:
        terms = ", ".join(term["target_terms"][0] for term in result["refined_terms"])
        print(
            f"Item {result['item']}: {result['refined_count']}/"
            f"{result['candidate_count']} refined terms ({result['refined_verified_count']} verified): "
            f"{terms}"
        )


def load_case_from_root(case: dict[str, Any], root_name: str) -> dict[str, Any] | None:
    root = BENCHMARK_DIR / root_name / case["direction"]
    manifest_path = next(root.glob("*-manifest.jsonl"))
    manifest_rows = [
        json.loads(line)
        for line in manifest_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    for index, manifest in enumerate(manifest_rows):
        if manifest.get("example_id") == case["example_id"] or manifest.get("source_id") == case[
            "example_id"
        ]:
            return {
                "manifest": manifest,
                "target_text": load_target_text(root / "target.csv", index),
            }
    return None


def load_target_text(path: Path, index: int) -> str:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return rows[index]["context"]


def load_terms(raw_terms: list[dict[str, Any]]) -> list[DatasetTerminologyTerm]:
    return [dataset_term_from_json(term) for term in raw_terms]


if __name__ == "__main__":
    main()
