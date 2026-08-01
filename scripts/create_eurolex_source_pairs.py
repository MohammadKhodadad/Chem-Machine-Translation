from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from chem_machine_translation.data.terminology import build_eurolex_descriptor_terms
from chem_machine_translation.utils.text import approximate_token_count, normalize_text

DEFAULT_LANGUAGES = ["en", "de", "fr", "sk"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create EuroLex source-target pair JSONL from a tracked row snapshot.",
    )
    parser.add_argument(
        "--source-jsonl",
        type=Path,
        default=Path("benchmark_sources/eurolex_4000.jsonl"),
    )
    parser.add_argument(
        "--descriptor-json",
        type=Path,
        default=Path("benchmark_sources/eurovoc_descriptors_subset.json"),
    )
    parser.add_argument(
        "--output-jsonl",
        type=Path,
        default=Path("benchmark_sources/eurolex_within_document_pairs_250_per_language_pair.jsonl"),
    )
    parser.add_argument(
        "--metadata-output",
        type=Path,
        default=Path(
            "benchmark_sources/eurolex_within_document_pairs_250_per_language_pair_metadata.json",
        ),
    )
    parser.add_argument("--language", action="append", dest="languages")
    parser.add_argument("--limit", type=int, default=250)
    parser.add_argument("--min-input-tokens", type=int, default=32)
    parser.add_argument("--max-input-tokens", type=int, default=1024)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    languages = args.languages or DEFAULT_LANGUAGES
    descriptors = load_descriptor_map(args.descriptor_json)
    records = load_records(args.source_jsonl, descriptors)
    pair_rows = build_pair_rows(
        records=records,
        languages=languages,
        limit=args.limit,
        min_input_tokens=args.min_input_tokens,
        max_input_tokens=args.max_input_tokens,
    )

    args.output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with args.output_jsonl.open("w", encoding="utf-8") as handle:
        for row in pair_rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    counts = Counter(row["language_pair"] for row in pair_rows)
    metadata = {
        "source_jsonl": str(args.source_jsonl),
        "descriptor_json": str(args.descriptor_json),
        "rows": len(pair_rows),
        "language_pairs": dict(sorted(counts.items())),
        "languages": languages,
        "limit_per_pair": args.limit,
        "schema": {
            "id": "example_id",
            "document_id": "doc_id",
            "source_language": "source_language",
            "target_language": "target_language",
            "source_text": "source_text",
            "target_text": "target_text",
            "eurovoc_descriptors": "eurovoc_descriptors",
            "eurovoc_target_terms": "eurovoc_target_terms",
        },
        "selection": (
            "Same EuroLex document, selected per ordered language pair by descending "
            "target-language EuroVoc descriptor matches."
        ),
        "min_input_tokens": args.min_input_tokens,
        "max_input_tokens": args.max_input_tokens,
    }
    args.metadata_output.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(metadata)
    print({"output_jsonl": str(args.output_jsonl), "size": args.output_jsonl.stat().st_size})


def load_descriptor_map(path: Path) -> dict[str, dict[str, str]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    descriptors: dict[str, dict[str, str]] = {}
    for concept_id, value in raw.items():
        if isinstance(value, str):
            descriptors[str(concept_id)] = {"en": value}
        elif isinstance(value, dict):
            descriptors[str(concept_id)] = {
                str(language): str(label)
                for language, label in value.items()
                if isinstance(label, str) and label.strip()
            }
    return descriptors


def load_records(
    source_jsonl: Path,
    descriptors: dict[str, dict[str, str]],
) -> list[dict[str, Any]]:
    records = []
    with source_jsonl.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            label_ids = [
                str(label)
                for label in record.get("eurovoc_concepts", {}).get("level_1", [])
            ]
            record["labels"] = label_ids
            record["eurovoc_descriptors"] = {
                label_id: descriptors[label_id]
                for label_id in label_ids
                if label_id in descriptors
            }
            records.append(record)
    return records


def build_pair_rows(
    *,
    records: list[dict[str, Any]],
    languages: list[str],
    limit: int,
    min_input_tokens: int,
    max_input_tokens: int,
) -> list[dict[str, Any]]:
    pair_rows = []
    for source_language in languages:
        for target_language in languages:
            if source_language == target_language:
                continue
            candidates = pair_candidates(
                records=records,
                source_language=source_language,
                target_language=target_language,
                min_input_tokens=min_input_tokens,
                max_input_tokens=max_input_tokens,
            )
            candidates.sort(
                key=lambda candidate: (
                    candidate["eurovoc_target_term_count"],
                    candidate["doc_id"],
                ),
                reverse=True,
            )
            pair_rows.extend(candidates[:limit])
    return pair_rows


def pair_candidates(
    *,
    records: list[dict[str, Any]],
    source_language: str,
    target_language: str,
    min_input_tokens: int,
    max_input_tokens: int,
) -> list[dict[str, Any]]:
    candidates = []
    for record in records:
        source_text = text_for_language(record, source_language)
        target_text = text_for_language(record, target_language)
        token_count = approximate_token_count(source_text)
        if (
            not source_text
            or not target_text
            or token_count < min_input_tokens
            or token_count > max_input_tokens
        ):
            continue
        target_terms = build_eurolex_descriptor_terms(
            descriptors_by_concept_id=record.get("eurovoc_descriptors", {}),
            target_language_code=target_language,
            target_text=target_text,
        )
        candidates.append(
            {
                "example_id": (
                    f"within-document:eurolex:{source_language}-{target_language}:"
                    f"{record['celex_id']}"
                ),
                "doc_id": str(record["celex_id"]),
                "corpus_id": "multi-eurlex",
                "source": "EU",
                "group_key": str(record["celex_id"]),
                "pub_date": str(record.get("publication_date") or ""),
                "field": "context",
                "language_pair": f"{source_language}-{target_language}",
                "source_language": source_language,
                "target_language": target_language,
                "source_text": source_text,
                "target_text": target_text,
                "selection_rule": (
                    "same EuroLex document; ranked by target-language EuroVoc "
                    "descriptor matches"
                ),
                "eurovoc_labels": record.get("labels", []),
                "eurovoc_descriptors": record.get("eurovoc_descriptors", {}),
                "eurovoc_target_terms": [term.to_json() for term in target_terms],
                "eurovoc_target_term_count": len(target_terms),
            },
        )
    return candidates


def text_for_language(record: dict[str, Any], language: str) -> str:
    texts = record.get("text", {})
    text = texts.get(language)
    if text is None and language != "en":
        text = texts.get(f"en2{language}")
    return normalize_text(str(text or ""))


if __name__ == "__main__":
    main()
