from __future__ import annotations

import argparse
import json
from collections import Counter
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any

from chem_machine_translation.utils.text import approximate_token_count, normalize_text

DEFAULT_DATASET_ID = "BASF-AI/ai4chem-clir-google-patents-within-document-abstract-pairs"
DEFAULT_OUTPUT_JSONL = Path(
    "benchmark_sources/google_patents_within_document_pairs_250_per_language_pair.jsonl"
)
DEFAULT_METADATA_OUTPUT = Path(
    "benchmark_sources/google_patents_within_document_pairs_250_per_language_pair_metadata.json"
)
SOURCE_SCHEMA_VERSION = "hf-google-patents-within-document-abstract-pairs-v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export Google Patents within-document abstract pairs from Hugging Face.",
    )
    parser.add_argument("--dataset-id", default=DEFAULT_DATASET_ID)
    parser.add_argument("--split", default="train")
    parser.add_argument("--revision", default=None)
    parser.add_argument("--output-jsonl", type=Path, default=DEFAULT_OUTPUT_JSONL)
    parser.add_argument("--metadata-output", type=Path, default=DEFAULT_METADATA_OUTPUT)
    parser.add_argument(
        "--limit-per-pair",
        type=int,
        default=250,
        help="Maximum rows exported per language_pair. Use 0 for no cap.",
    )
    parser.add_argument("--min-source-tokens", type=int, default=None)
    parser.add_argument("--max-source-tokens", type=int, default=None)
    parser.add_argument("--min-target-tokens", type=int, default=None)
    parser.add_argument("--max-target-tokens", type=int, default=None)
    parser.add_argument(
        "--backfill-shortfalls",
        action="store_true",
        help="Prefer length-matching rows, then fill each pair from the rest up to the cap.",
    )
    parser.add_argument(
        "--require-full-limit",
        action="store_true",
        help="Drop language pairs that cannot reach --limit-per-pair rows.",
    )
    parser.add_argument(
        "--language",
        action="append",
        dest="languages",
        help="Keep rows where both source and target language are included. Repeatable.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows, metadata = export_google_patents_source_pairs(
        rows=iter_hf_dataset_rows(
            dataset_id=args.dataset_id,
            split=args.split,
            revision=args.revision,
        ),
        output_jsonl=args.output_jsonl,
        metadata_output=args.metadata_output,
        dataset_id=args.dataset_id,
        split=args.split,
        revision=args.revision,
        limit_per_pair=args.limit_per_pair,
        min_source_tokens=args.min_source_tokens,
        max_source_tokens=args.max_source_tokens,
        min_target_tokens=args.min_target_tokens,
        max_target_tokens=args.max_target_tokens,
        backfill_shortfalls=args.backfill_shortfalls,
        require_full_limit=args.require_full_limit,
        languages=args.languages,
    )
    print(f"Wrote {rows} source pairs to {args.output_jsonl}")
    print(f"Metadata: {args.metadata_output}")
    print(f"Language pairs: {', '.join(sorted(metadata['language_pair_counts']))}")


def iter_hf_dataset_rows(
    *,
    dataset_id: str,
    split: str,
    revision: str | None,
) -> Iterator[dict[str, Any]]:
    from datasets import load_dataset

    dataset = load_dataset(dataset_id, split=split, revision=revision, streaming=True)
    for row in dataset:
        yield dict(row)


def export_google_patents_source_pairs(
    *,
    rows: Iterable[dict[str, Any]],
    output_jsonl: Path,
    metadata_output: Path,
    dataset_id: str,
    split: str,
    revision: str | None,
    limit_per_pair: int,
    min_source_tokens: int | None,
    max_source_tokens: int | None,
    min_target_tokens: int | None,
    max_target_tokens: int | None,
    backfill_shortfalls: bool,
    require_full_limit: bool,
    languages: list[str] | None,
) -> tuple[int, dict[str, Any]]:
    language_filter = {language.lower() for language in languages or []}
    selected_rows, skipped_empty = select_source_pair_rows(
        rows=rows,
        language_filter=language_filter,
        limit_per_pair=limit_per_pair,
        min_source_tokens=min_source_tokens,
        max_source_tokens=max_source_tokens,
        min_target_tokens=min_target_tokens,
        max_target_tokens=max_target_tokens,
        backfill_shortfalls=backfill_shortfalls,
        require_full_limit=require_full_limit,
    )
    output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    metadata_output.parent.mkdir(parents=True, exist_ok=True)
    with output_jsonl.open("w", encoding="utf-8", newline="\n") as handle:
        for row in selected_rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    metadata = build_metadata(
        rows=selected_rows,
        skipped_empty=skipped_empty,
        dataset_id=dataset_id,
        split=split,
        revision=revision,
        output_jsonl=output_jsonl,
        limit_per_pair=limit_per_pair,
        min_source_tokens=min_source_tokens,
        max_source_tokens=max_source_tokens,
        min_target_tokens=min_target_tokens,
        max_target_tokens=max_target_tokens,
        backfill_shortfalls=backfill_shortfalls,
        require_full_limit=require_full_limit,
        language_filter=language_filter,
    )
    metadata_output.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return len(selected_rows), metadata


def select_source_pair_rows(
    *,
    rows: Iterable[dict[str, Any]],
    language_filter: set[str],
    limit_per_pair: int,
    min_source_tokens: int | None,
    max_source_tokens: int | None,
    min_target_tokens: int | None,
    max_target_tokens: int | None,
    backfill_shortfalls: bool,
    require_full_limit: bool,
) -> tuple[list[dict[str, Any]], int]:
    if backfill_shortfalls:
        return select_source_pair_rows_with_backfill(
            rows=rows,
            language_filter=language_filter,
            limit_per_pair=limit_per_pair,
            min_source_tokens=min_source_tokens,
            max_source_tokens=max_source_tokens,
            min_target_tokens=min_target_tokens,
            max_target_tokens=max_target_tokens,
            require_full_limit=require_full_limit,
        )

    selected = []
    counts: Counter[str] = Counter()
    skipped_empty = 0
    for raw_row in rows:
        row = normalize_google_patents_source_row(raw_row)
        if not row["source_text"] or not row["target_text"]:
            skipped_empty += 1
            continue
        if language_filter and (
            row["source_language"] not in language_filter
            or row["target_language"] not in language_filter
        ):
            continue
        if not token_counts_in_range(
            row=row,
            min_source_tokens=min_source_tokens,
            max_source_tokens=max_source_tokens,
            min_target_tokens=min_target_tokens,
            max_target_tokens=max_target_tokens,
        ):
            continue
        language_pair = row["language_pair"]
        if limit_per_pair > 0 and counts[language_pair] >= limit_per_pair:
            continue
        selected.append(row)
        counts[language_pair] += 1
    return selected, skipped_empty


def select_source_pair_rows_with_backfill(
    *,
    rows: Iterable[dict[str, Any]],
    language_filter: set[str],
    limit_per_pair: int,
    min_source_tokens: int | None,
    max_source_tokens: int | None,
    min_target_tokens: int | None,
    max_target_tokens: int | None,
    require_full_limit: bool,
) -> tuple[list[dict[str, Any]], int]:
    grouped: dict[str, list[tuple[int, int, dict[str, Any]]]] = {}
    skipped_empty = 0
    for index, raw_row in enumerate(rows):
        row = normalize_google_patents_source_row(raw_row)
        if not row["source_text"] or not row["target_text"]:
            skipped_empty += 1
            continue
        if language_filter and (
            row["source_language"] not in language_filter
            or row["target_language"] not in language_filter
        ):
            continue
        priority = length_priority(
            row=row,
            min_source_tokens=min_source_tokens,
            max_source_tokens=max_source_tokens,
            min_target_tokens=min_target_tokens,
            max_target_tokens=max_target_tokens,
        )
        grouped.setdefault(row["language_pair"], []).append((priority, index, row))

    selected = []
    for language_pair in sorted(grouped):
        candidates = sorted(grouped[language_pair], key=lambda item: (item[0], item[1]))
        if limit_per_pair > 0:
            if require_full_limit and len(candidates) < limit_per_pair:
                continue
            candidates = candidates[:limit_per_pair]
        selected.extend(row for _, _, row in candidates)
    return selected, skipped_empty


def length_priority(
    *,
    row: dict[str, Any],
    min_source_tokens: int | None,
    max_source_tokens: int | None,
    min_target_tokens: int | None,
    max_target_tokens: int | None,
) -> int:
    source_in_range = source_token_count_in_range(
        row=row,
        min_source_tokens=min_source_tokens,
        max_source_tokens=max_source_tokens,
    )
    target_in_range = target_token_count_in_range(
        row=row,
        min_target_tokens=min_target_tokens,
        max_target_tokens=max_target_tokens,
    )
    if source_in_range and target_in_range:
        return 0
    if source_in_range:
        return 1
    if target_in_range:
        return 2
    return 3


def token_counts_in_range(
    *,
    row: dict[str, Any],
    min_source_tokens: int | None,
    max_source_tokens: int | None,
    min_target_tokens: int | None,
    max_target_tokens: int | None,
) -> bool:
    return source_token_count_in_range(
        row=row,
        min_source_tokens=min_source_tokens,
        max_source_tokens=max_source_tokens,
    ) and target_token_count_in_range(
        row=row,
        min_target_tokens=min_target_tokens,
        max_target_tokens=max_target_tokens,
    )


def source_token_count_in_range(
    *,
    row: dict[str, Any],
    min_source_tokens: int | None,
    max_source_tokens: int | None,
) -> bool:
    source_tokens = approximate_token_count(str(row["source_text"]))
    if min_source_tokens is not None and source_tokens < min_source_tokens:
        return False
    if max_source_tokens is not None and source_tokens > max_source_tokens:
        return False
    return True


def target_token_count_in_range(
    *,
    row: dict[str, Any],
    min_target_tokens: int | None,
    max_target_tokens: int | None,
) -> bool:
    target_tokens = approximate_token_count(str(row["target_text"]))
    if min_target_tokens is not None and target_tokens < min_target_tokens:
        return False
    if max_target_tokens is not None and target_tokens > max_target_tokens:
        return False
    return True


def normalize_google_patents_source_row(row: dict[str, Any]) -> dict[str, Any]:
    source_language = str(row.get("source_language") or "").strip().lower()
    target_language = str(row.get("target_language") or "").strip().lower()
    language_pair = str(row.get("language_pair") or f"{source_language}-{target_language}")
    return {
        "example_id": str(row.get("example_id") or ""),
        "doc_id": str(row.get("doc_id") or ""),
        "corpus_id": str(row.get("corpus_id") or "google-patents-chem"),
        "source": str(row.get("source") or ""),
        "group_key": str(row.get("group_key") or ""),
        "pub_date": str(row.get("pub_date") or ""),
        "field": str(row.get("field") or "abstract"),
        "language_pair": language_pair,
        "source_language": source_language,
        "target_language": target_language,
        "source_text": normalize_text(str(row.get("source_text") or "")),
        "target_text": normalize_text(str(row.get("target_text") or "")),
        "source_char_count": int(row.get("source_char_count") or 0),
        "target_char_count": int(row.get("target_char_count") or 0),
        "source_token_count": int(row.get("source_token_count") or 0),
        "target_token_count": int(row.get("target_token_count") or 0),
        "source_sentence_count": int(row.get("source_sentence_count") or 0),
        "target_sentence_count": int(row.get("target_sentence_count") or 0),
        "source_tokens_per_sentence": float(row.get("source_tokens_per_sentence") or 0.0),
        "target_tokens_per_sentence": float(row.get("target_tokens_per_sentence") or 0.0),
        "tokenizer": str(row.get("tokenizer") or ""),
        "selection_rule": str(row.get("selection_rule") or ""),
    }


def build_metadata(
    *,
    rows: list[dict[str, Any]],
    skipped_empty: int,
    dataset_id: str,
    split: str,
    revision: str | None,
    output_jsonl: Path,
    limit_per_pair: int,
    min_source_tokens: int | None,
    max_source_tokens: int | None,
    min_target_tokens: int | None,
    max_target_tokens: int | None,
    backfill_shortfalls: bool,
    require_full_limit: bool,
    language_filter: set[str],
) -> dict[str, Any]:
    language_pair_counts = Counter(row["language_pair"] for row in rows)
    source_language_counts = Counter(row["source_language"] for row in rows)
    target_language_counts = Counter(row["target_language"] for row in rows)
    priority_counts = Counter(
        length_priority(
            row=row,
            min_source_tokens=min_source_tokens,
            max_source_tokens=max_source_tokens,
            min_target_tokens=min_target_tokens,
            max_target_tokens=max_target_tokens,
        )
        for row in rows
    )
    return {
        "schema_version": SOURCE_SCHEMA_VERSION,
        "dataset_id": dataset_id,
        "split": split,
        "revision": revision,
        "output_jsonl": output_jsonl.as_posix(),
        "rows": len(rows),
        "limit_per_pair": limit_per_pair,
        "min_source_tokens": min_source_tokens,
        "max_source_tokens": max_source_tokens,
        "min_target_tokens": min_target_tokens,
        "max_target_tokens": max_target_tokens,
        "backfill_shortfalls": backfill_shortfalls,
        "require_full_limit": require_full_limit,
        "length_filter_tokenizer": "chem_machine_translation.utils.text.approximate_token_count",
        "language_filter": sorted(language_filter),
        "language_pair_counts": dict(sorted(language_pair_counts.items())),
        "source_language_counts": dict(sorted(source_language_counts.items())),
        "target_language_counts": dict(sorted(target_language_counts.items())),
        "length_priority_counts": {
            "source_and_target_in_range": priority_counts[0],
            "source_only_in_range": priority_counts[1],
            "target_only_in_range": priority_counts[2],
            "backfill_out_of_range": priority_counts[3],
        },
        "skipped_empty_text_rows": skipped_empty,
        "selection_policy": source_selection_policy(backfill_shortfalls),
    }


def source_selection_policy(backfill_shortfalls: bool) -> str:
    base = (
        "Streaming export from the Hugging Face Google Patents within-document abstract-pair "
        "dataset in dataset order."
    )
    if backfill_shortfalls:
        return (
            f"{base} Rows matching both source and target token bounds are preferred, then "
            "source-only matches, then target-only matches, then remaining rows. Each "
            "language_pair is capped when limit_per_pair is positive."
        )
    return (
        f"{base} Rows are filtered by this repository's approximate token-count bounds when "
        "provided, and capped per language_pair when limit_per_pair is positive."
    )


if __name__ == "__main__":
    main()
