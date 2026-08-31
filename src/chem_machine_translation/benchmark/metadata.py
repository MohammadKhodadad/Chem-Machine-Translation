from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any

from chem_machine_translation.benchmark.config import BenchmarkBuildConfig

PERCENTILES = (5, 10, 25, 50, 75, 90, 95)
TERM_BUCKETS = (
    (0, 0, "0"),
    (1, 2, "1-2"),
    (3, 5, "3-5"),
    (6, 8, "6-8"),
    (9, 15, "9-15"),
    (16, None, "16+"),
)


def write_benchmark_metadata(
    metadata_path: Path,
    *,
    rows: list[dict[str, Any]],
    build: BenchmarkBuildConfig,
) -> None:
    metadata_path.write_text(
        json.dumps(
            build_benchmark_metadata(rows=rows, build=build),
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def build_benchmark_metadata(
    *,
    rows: list[dict[str, Any]],
    build: BenchmarkBuildConfig,
) -> dict[str, Any]:
    directions = sorted({str(row.get("direction") or "") for row in rows if row.get("direction")})
    anchor_ids = sorted({str(row.get("anchor_id") or "") for row in rows if row.get("anchor_id")})
    return {
        "build_name": build.name,
        "kind": build.kind,
        "source_pairs_jsonl": portable_path(build.source_pairs_jsonl),
        "output_dir": portable_path(build.output_dir),
        "selection": {
            "mode": build.selection_mode,
            "languages": list(build.languages),
            "limit": build.limit if build.selection_mode == "per_direction" else None,
            "anchor_limit": build.anchor_limit,
            "bidirectional": build.bidirectional,
        },
        "row_count": len(rows),
        "direction_count": len(directions),
        "anchor_count": len(anchor_ids),
        "directions": directions,
        "overall": summarize_rows(rows),
        "by_direction": group_summaries(rows, key="direction"),
        "by_source_language": group_summaries(rows, key="source_language_code"),
        "by_target_language": group_summaries(rows, key="target_language_code"),
    }


def group_summaries(rows: list[dict[str, Any]], *, key: str) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        value = str(row.get(key) or "")
        if not value:
            continue
        grouped.setdefault(value, []).append(row)
    return {value: summarize_rows(group_rows) for value, group_rows in sorted(grouped.items())}


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    candidate_counts = [candidate_term_count(row) for row in rows]
    refined_counts = [refined_term_count(row) for row in rows]
    verified_refined_counts = [verified_refined_term_count(row) for row in rows]
    return {
        "row_count": len(rows),
        "source_tokens": numeric_summary(
            numeric_values(row.get("approx_source_tokens") for row in rows)
        ),
        "target_tokens": numeric_summary(
            numeric_values(row.get("approx_target_tokens") for row in rows)
        ),
        "candidate_terms_per_row": term_count_summary(candidate_counts),
        "refined_terms_per_row": term_count_summary(refined_counts),
        "verified_refined_terms_per_row": term_count_summary(verified_refined_counts),
        "rows_with_terms_pct": percent(
            sum(count > 0 for count in candidate_counts),
            len(candidate_counts),
        ),
        "rows_with_refined_terms_pct": percent(
            sum(count > 0 for count in refined_counts),
            len(refined_counts),
        ),
    }


def term_count_summary(counts: list[int]) -> dict[str, Any]:
    return {
        "stats": numeric_summary(counts),
        "buckets": bucket_distribution(counts),
    }


def bucket_distribution(counts: list[int]) -> dict[str, dict[str, float | int]]:
    total = len(counts)
    counter: Counter[str] = Counter()
    for count in counts:
        counter[bucket_label(count)] += 1
    return {
        label: {"count": counter[label], "pct": percent(counter[label], total)}
        for _, _, label in TERM_BUCKETS
    }


def bucket_label(count: int) -> str:
    for minimum, maximum, label in TERM_BUCKETS:
        if count >= minimum and (maximum is None or count <= maximum):
            return label
    raise ValueError(f"Unsupported term count: {count}")


def candidate_term_count(row: dict[str, Any]) -> int:
    return sum(1 for term in terminology_entries(row) if term.get("term_group") != "refined")


def refined_term_count(row: dict[str, Any]) -> int:
    return sum(1 for term in terminology_entries(row) if term.get("term_group") == "refined")


def verified_refined_term_count(row: dict[str, Any]) -> int:
    return sum(
        1
        for term in terminology_entries(row)
        if term.get("term_group") == "refined" and term.get("verified_by")
    )


def terminology_entries(row: dict[str, Any]) -> list[dict[str, Any]]:
    return [term for term in row.get("terminology", []) if isinstance(term, dict)]


def numeric_values(values: Any) -> list[float]:
    output = []
    for value in values:
        if value in (None, ""):
            continue
        output.append(float(value))
    return output


def numeric_summary(values: list[float] | list[int]) -> dict[str, float | int | None]:
    if not values:
        return {
            "count": 0,
            "min": None,
            "mean": None,
            "max": None,
            **{f"p{percentile}": None for percentile in PERCENTILES},
        }
    sorted_values = sorted(float(value) for value in values)
    summary: dict[str, float | int | None] = {
        "count": len(sorted_values),
        "min": round(sorted_values[0], 2),
        "mean": round(mean(sorted_values), 2),
        "max": round(sorted_values[-1], 2),
    }
    summary.update(
        {
            f"p{percentile}": round(percentile_value(sorted_values, percentile), 2)
            for percentile in PERCENTILES
        }
    )
    return summary


def percentile_value(sorted_values: list[float], percentile: int) -> float:
    if len(sorted_values) == 1:
        return sorted_values[0]
    position = (len(sorted_values) - 1) * percentile / 100
    lower_index = int(position)
    upper_index = min(lower_index + 1, len(sorted_values) - 1)
    fraction = position - lower_index
    return sorted_values[lower_index] + (
        sorted_values[upper_index] - sorted_values[lower_index]
    ) * fraction


def percent(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(100 * numerator / denominator, 2)


def portable_path(path: Path) -> str:
    try:
        return path.relative_to(Path.cwd()).as_posix()
    except ValueError:
        return str(path)
