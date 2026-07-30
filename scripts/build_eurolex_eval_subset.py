from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from chem_machine_translation.data.terminology import build_eurolex_descriptor_terms
from chem_machine_translation.utils.text import approximate_token_count, normalize_text

LANGUAGE_NAMES = {
    "bg": "Bulgarian",
    "cs": "Czech",
    "da": "Danish",
    "de": "German",
    "el": "Greek",
    "en": "English",
    "es": "Spanish",
    "et": "Estonian",
    "fi": "Finnish",
    "fr": "French",
    "hr": "Croatian",
    "hu": "Hungarian",
    "it": "Italian",
    "lt": "Lithuanian",
    "lv": "Latvian",
    "mt": "Maltese",
    "nl": "Dutch",
    "pl": "Polish",
    "pt": "Portuguese",
    "ro": "Romanian",
    "sk": "Slovak",
    "sl": "Slovenian",
    "sv": "Swedish",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a EuroLex/MultiEURLEX parallel benchmark subset from a local JSONL export."
        ),
    )
    parser.add_argument("--source-jsonl", type=Path, default=Path("data/multi_eurlex/train.jsonl"))
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("benchmark_datasets/eurolex_eval_subset_generated"),
    )
    parser.add_argument("--source-language", choices=sorted(LANGUAGE_NAMES), default="en")
    parser.add_argument(
        "--target-language",
        action="append",
        dest="target_languages",
        choices=sorted(LANGUAGE_NAMES),
    )
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--min-input-tokens", type=int, default=128)
    parser.add_argument("--max-input-tokens", type=int, default=512)
    parser.add_argument("--label-level", default="level_1")
    parser.add_argument(
        "--descriptor-json",
        type=Path,
        default=None,
        help=(
            "Optional EuroVoc descriptor map. Supports {id: 'label'} or "
            "{id: {lang: 'label'}} JSON."
        ),
    )
    parser.add_argument(
        "--no-eurovoc-terminology",
        action="store_true",
        help="Keep EuroVoc descriptors as metadata only; do not add in-text descriptors as terms.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    target_languages = args.target_languages or ["de", "fr"]
    descriptors = load_descriptor_map(args.descriptor_json)
    selections = select_records(
        source_jsonl=args.source_jsonl,
        source_language=args.source_language,
        target_languages=target_languages,
        limit=args.limit,
        min_input_tokens=args.min_input_tokens,
        max_input_tokens=args.max_input_tokens,
        label_level=args.label_level,
        descriptors=descriptors,
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    combined_rows = []
    for target_language in target_languages:
        direction = f"{args.source_language}-{target_language}"
        direction_dir = args.output_dir / direction
        direction_dir.mkdir(parents=True, exist_ok=True)
        direction_rows = [
            build_manifest_row(
                record=record,
                source_language=args.source_language,
                target_language=target_language,
                include_eurovoc_terminology=not args.no_eurovoc_terminology,
            )
            for record in selections
        ]
        write_rows(direction_dir / "source.csv", [row["_source_row"] for row in direction_rows])
        write_rows(direction_dir / "target.csv", [row["_target_row"] for row in direction_rows])
        manifest_path = direction_dir / f"eurolex-{direction}-{len(direction_rows)}-manifest.jsonl"
        write_manifest(manifest_path, direction_rows)
        combined_rows.extend(direction_rows)

    target_slug = "-".join(target_languages)
    combined_path = (
        args.output_dir
        / f"eurolex-{args.source_language}-to-{target_slug}-{len(combined_rows)}-manifest.jsonl"
    )
    write_manifest(combined_path, combined_rows)
    print(f"Wrote {len(selections)} source records and {len(combined_rows)} pairs.")
    print(f"Combined manifest: {combined_path}")


def load_descriptor_map(path: Path | None) -> dict[str, dict[str, str]]:
    if path is None:
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    descriptors = {}
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


def select_records(
    source_jsonl: Path,
    source_language: str,
    target_languages: list[str],
    limit: int,
    min_input_tokens: int,
    max_input_tokens: int,
    label_level: str,
    descriptors: dict[str, dict[str, str]],
) -> list[dict[str, Any]]:
    selected = []
    with source_jsonl.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = normalize_record(json.loads(line), label_level, descriptors)
            texts = record.get("text", {})
            source_text = normalize_text(str(texts.get(source_language) or ""))
            token_count = approximate_token_count(source_text)
            if not source_text or token_count < min_input_tokens or token_count > max_input_tokens:
                continue
            missing_target = any(
                not normalize_text(str(texts.get(language) or ""))
                for language in target_languages
            )
            if missing_target:
                continue
            selected.append(record)
            if len(selected) >= limit:
                break
    return selected


def normalize_record(
    record: dict[str, Any],
    label_level: str,
    descriptors: dict[str, dict[str, str]],
) -> dict[str, Any]:
    labels = record.get("labels")
    if labels is None:
        labels = record.get("eurovoc_concepts", {}).get(label_level, [])
    label_ids = [str(label) for label in labels or []]
    record["labels"] = label_ids
    record["eurovoc_descriptors"] = {
        label_id: descriptors.get(label_id, {}) for label_id in label_ids if label_id in descriptors
    }
    return record


def build_manifest_row(
    record: dict[str, Any],
    source_language: str,
    target_language: str,
    include_eurovoc_terminology: bool,
) -> dict[str, Any]:
    celex_id = str(record["celex_id"])
    source_text = normalize_text(str(record["text"][source_language]))
    target_text = normalize_text(str(record["text"][target_language]))
    direction = f"{source_language}-{target_language}"
    source_row = {
        "id": f"{celex_id}_{source_language}",
        "celex_id": celex_id,
        "language": source_language,
        "context": source_text,
    }
    target_row = {
        "id": f"{celex_id}_{target_language}",
        "celex_id": celex_id,
        "language": target_language,
        "context": target_text,
    }
    eurovoc_terms = (
        build_eurolex_descriptor_terms(
            descriptors_by_concept_id=record.get("eurovoc_descriptors", {}),
            target_language_code=target_language,
            target_text=target_text,
        )
        if include_eurovoc_terminology
        else []
    )
    return {
        "dataset": "eurolex",
        "source_id": celex_id,
        "direction": direction,
        "source_language": LANGUAGE_NAMES[source_language],
        "source_language_code": source_language,
        "target_language": LANGUAGE_NAMES[target_language],
        "target_language_code": target_language,
        "source_row_id": source_row["id"],
        "target_row_id": target_row["id"],
        "celex_id": celex_id,
        "eurovoc_labels": record.get("labels", []),
        "eurovoc_descriptors": record.get("eurovoc_descriptors", {}),
        "approx_source_tokens": approximate_token_count(source_text),
        "text_field": "context",
        "selection": "requires_source_and_target_context_token_window",
        "terminology": [term.to_json() for term in eurovoc_terms],
        "_source_text": source_text,
        "_target_text": target_text,
        "_source_row": source_row,
        "_target_row": target_row,
    }


def write_rows(csv_path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = sorted({field for row in rows for field in row})
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_manifest(manifest_path: Path, rows: list[dict[str, Any]]) -> None:
    temp_path = manifest_path.with_suffix(manifest_path.suffix + ".tmp")
    with temp_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            output_row = {
                key: value
                for key, value in row.items()
                if not key.startswith("_") and value not in (None, "")
            }
            handle.write(json.dumps(output_row, ensure_ascii=False) + "\n")
    temp_path.replace(manifest_path)


if __name__ == "__main__":
    main()
