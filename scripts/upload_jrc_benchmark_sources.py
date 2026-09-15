from __future__ import annotations

import argparse
import json
import math
from io import BytesIO
from pathlib import Path

from huggingface_hub import HfApi

from chem_machine_translation.config import load_settings

DEFAULT_ARTICLES_JSONL = Path(
    "benchmark_sources/jrc_acquis_anchored_articles_250_per_language_pair.jsonl"
)
DEFAULT_ARTICLES_METADATA = Path(
    "benchmark_sources/jrc_acquis_anchored_articles_250_per_language_pair_metadata.json"
)
DEFAULT_DEFINITIONS_JSONL = Path(
    "benchmark_sources/jrc_acquis_anchored_definitions_250_per_language_pair.jsonl"
)
DEFAULT_DEFINITIONS_METADATA = Path(
    "benchmark_sources/jrc_acquis_anchored_definitions_250_per_language_pair_metadata.json"
)
DEFAULT_ARTICLES_HF_REPO_ID = "BASF-AI/ai4chem-clir-jrc-acquis-articles-benchmark-sources"
DEFAULT_DEFINITIONS_HF_REPO_ID = (
    "BASF-AI/ai4chem-clir-jrc-acquis-definitions-benchmark-sources"
)
DEFAULT_HF_REPO_ID = "BASF-AI/ai4chem-clir-jrc-acquis-benchmark-sources"
DEFAULT_HF_COLLECTION = "BASF-AI/ai4chem-clir"


def load_metadata_summary(metadata_path: Path) -> dict:
    with metadata_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    pair_counts = data.get("language_pair_counts", {})
    ordered_pairs = len(pair_counts)
    rows_per_pair = next(iter(pair_counts.values()), 0) if pair_counts else 0
    total_rows = data.get("rows", sum(pair_counts.values()))
    source_token_stats = data.get("source_token_stats", {})
    chunking = data.get("chunking", {})
    languages = data.get("languages", [])

    return {
        "rows": total_rows,
        "languages": languages,
        "ordered_pairs": ordered_pairs,
        "rows_per_pair": rows_per_pair,
        "pair_counts": pair_counts,
        "min_source_tokens": source_token_stats.get("min", "n/a"),
        "max_source_tokens": source_token_stats.get("max", "n/a"),
        "mean_source_tokens": source_token_stats.get("mean", "n/a"),
        "selection_mode": data.get("selection_mode", "n/a"),
        "quality_mode": data.get("quality_mode", "n/a"),
        "clean_legacy_markup": data.get("clean_legacy_markup", False),
        "anchor_language": data.get("anchor_language", "n/a"),
        "limit_per_direction": data.get("limit_per_direction", "n/a"),
        "chunk_min": chunking.get("min_chunk_tokens", "n/a"),
        "chunk_target": chunking.get("target_chunk_tokens", "n/a"),
        "chunk_max": chunking.get("max_chunk_tokens", "n/a"),
    }


def compute_percentile(values: list[int], percentile: int) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil((percentile / 100) * len(ordered)) - 1))
    return ordered[index]


def load_jsonl_token_summary(jsonl_path: Path) -> dict[str, dict[str, int]]:
    source_values: list[int] = []
    target_values: list[int] = []
    with jsonl_path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            source_values.append(int(row.get("approx_source_tokens", 0)))
            target_values.append(int(row.get("approx_target_tokens", 0)))

    return {
        "source": {
            "p1": compute_percentile(source_values, 1),
            "p5": compute_percentile(source_values, 5),
            "p10": compute_percentile(source_values, 10),
            "p50": compute_percentile(source_values, 50),
            "p90": compute_percentile(source_values, 90),
            "p95": compute_percentile(source_values, 95),
            "p99": compute_percentile(source_values, 99),
        },
        "target": {
            "p1": compute_percentile(target_values, 1),
            "p5": compute_percentile(target_values, 5),
            "p10": compute_percentile(target_values, 10),
            "p50": compute_percentile(target_values, 50),
            "p90": compute_percentile(target_values, 90),
            "p95": compute_percentile(target_values, 95),
            "p99": compute_percentile(target_values, 99),
        },
    }


def build_repo_readme(section_type: str, repo_id: str, metadata_path: Path, jsonl_path: Path) -> str:
    title = (
        "JRC-Acquis Anchored Article Source Snapshot"
        if section_type == "article"
        else "JRC-Acquis Anchored Definition Source Snapshot"
    )
    file_prefix = (
        "jrc_acquis_anchored_articles_250_per_language_pair"
        if section_type == "article"
        else "jrc_acquis_anchored_definitions_250_per_language_pair"
    )
    metadata = load_metadata_summary(metadata_path)
    token_summary = load_jsonl_token_summary(jsonl_path)
    pair_counts = metadata["pair_counts"]
    pair_rows = "| Language pair | Rows |\n| --- | ---: |\n"
    for pair in [
        "de-en",
        "de-es",
        "de-fr",
        "de-pt",
        "en-de",
        "en-es",
        "en-fr",
        "en-pt",
        "es-de",
        "es-en",
        "es-fr",
        "es-pt",
        "fr-de",
        "fr-en",
        "fr-es",
        "fr-pt",
        "pt-de",
        "pt-en",
        "pt-es",
        "pt-fr",
    ]:
        pair_rows += f"| {pair} | {pair_counts.get(pair, 250)} |\n"

    quality_pipeline = (
        "Legacy markup cleanup and strict benchmark-quality filtering were applied. "
        "The selection pipeline uses anchored document filtering across the shared language set, "
        "followed by ordered-direction expansion and token-length constraints."
    )

    return f"""---
title: "{title}"
emoji: "📚"
colorFrom: blue
colorTo: green
annotations_creators:
- expert-generated
language:
- en
- es
- de
- fr
- pt
license: "cc-by-4.0"
tags:
- legal
- multilingual
- machine-translation
- retrieval
- benchmark
- jrc-acquis
- source-snapshot
---

# {title}

This dataset is a benchmark-ready source snapshot extracted from JRC-Acquis for multilingual legal and technical retrieval experiments.

## Overview

The repository contains a portable source JSONL snapshot and its paired metadata file for the {section_type}-section variant of the JRC-Acquis benchmark sources. Each snapshot is built from the same five source languages and the same 20 ordered language pairs, with a constant `250` rows per pair and a total of `{metadata['rows']}` rows.

- Dataset repo: `{repo_id}`
- Source section type: `{section_type}`
- Languages: `{', '.join(metadata['languages'])}`
- Ordered language pairs: `{metadata['ordered_pairs']}`
- Rows per pair: `{metadata['rows_per_pair']}`
- Rows per snapshot: `{metadata['rows']}`
- Selection mode: `{metadata['selection_mode']}`
- Quality mode: `{metadata['quality_mode']}`
- Primary bundle: `{file_prefix}.jsonl`
- Metadata bundle: `{file_prefix}_metadata.json`

## Benchmark dimensions

| Metric | Value |
| --- | ---: |
| Total rows | {metadata['rows']} |
| Source languages | {len(metadata['languages'])} |
| Ordered language pairs | {metadata['ordered_pairs']} |
| Rows per pair | {metadata['rows_per_pair']} |
| Anchor language | {metadata['anchor_language']} |
| Limit per direction | {metadata['limit_per_direction']} |
| Min source tokens | {metadata['min_source_tokens']} |
| Max source tokens | {metadata['max_source_tokens']} |
| Mean source tokens | {metadata['mean_source_tokens']} |
| Chunk min tokens | {metadata['chunk_min']} |
| Chunk target tokens | {metadata['chunk_target']} |
| Chunk max tokens | {metadata['chunk_max']} |

## Quality pipeline

{quality_pipeline}

- `clean_legacy_markup`: {str(metadata['clean_legacy_markup']).lower()}
- selection mode: `{metadata['selection_mode']}`
- quality mode: `{metadata['quality_mode']}`
- chunk range: `{metadata['chunk_min']}` to `{metadata['chunk_max']}` tokens

## Why this dataset exists

These snapshots provide a reproducible legal benchmark source that can be shared and reused without re-running the expensive source-generation pipeline. They are well suited for:

- retrieval benchmarking
- reranker evaluation
- legal-domain multilingual source matching
- pair-balance and length-distribution analysis

## Record schema

Each row in the JSONL file contains a source-pair example generated from aligned JRC-Acquis segments. The metadata file stores the associated provenance and chunk summary fields used for quality control and downstream benchmark preparation.

Typical fields include:

- `source_lang`, `target_lang`
- `source_text`, `target_text`
- `section_type`
- `anchor_id`
- `pair_id`
- `approx_source_tokens`, `approx_target_tokens`
- document and segment provenance metadata

## Language coverage and pair balance

The pair structure is constant across snapshots. The distribution below is identical for the article and definition variants.

{pair_rows}

## Snapshot statistics

| Snapshot | section_type | rows | language coverage | min source tokens | max source tokens | mean source tokens | p1 | p5 | p10 | p50 | p90 | p95 | p99 |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `{file_prefix}.jsonl` | {section_type} | {metadata['rows']} | {', '.join(metadata['languages'])} | {metadata['min_source_tokens']} | {metadata['max_source_tokens']} | {metadata['mean_source_tokens']} | {token_summary['source']['p1']} | {token_summary['source']['p5']} | {token_summary['source']['p10']} | {token_summary['source']['p50']} | {token_summary['source']['p90']} | {token_summary['source']['p95']} | {token_summary['source']['p99']} |

### Percentile summary

| Token type | p1 | p5 | p10 | p50 | p90 | p95 | p99 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Source tokens | {token_summary['source']['p1']} | {token_summary['source']['p5']} | {token_summary['source']['p10']} | {token_summary['source']['p50']} | {token_summary['source']['p90']} | {token_summary['source']['p95']} | {token_summary['source']['p99']} |
| Target tokens | {token_summary['target']['p1']} | {token_summary['target']['p5']} | {token_summary['target']['p10']} | {token_summary['target']['p50']} | {token_summary['target']['p90']} | {token_summary['target']['p95']} | {token_summary['target']['p99']} |

## Files in this repo

- `{file_prefix}.jsonl` — benchmark source snapshot
- `{file_prefix}_metadata.json` — associated per-row metadata and provenance fields

## Recommended usage

This dataset is designed as a portable benchmark source snapshot. Use the JSONL rows directly for source-side experiments or attach the metadata file for token-length, provenance, or pair-balance analysis.

## Notes

- The anchored selection logic uses shared document anchors across all five languages.
- Every ordered direction is represented equally, so pair balance remains stable across snapshots.
- The article and definition variants differ mainly in section type and token-length distribution, not in the pair coverage pattern.
- The metadata files expose both pair-level counts and source-token summary statistics for reproducible benchmark reporting.

## Source provenance

The data is derived from the public OPUS JRC-Acquis corpus and normalized into a benchmark-friendly source snapshot for multilingual legal benchmarking.

## License and usage

This repository is intended for research and benchmark preparation. Please check the upstream licensing and provenance constraints for the original JRC-Acquis content before production deployment or redistribution.
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Upload existing JRC-Acquis benchmark source files to Hugging Face "
            "without regenerating them."
        ),
    )
    parser.add_argument(
        "--hf-repo-id",
        default=None,
        help=(
            "Legacy fallback repo ID used for both source sets when no per-set repo is set. "
            f"Defaults to CHEM_MT_HF_REPO_ID/HF_REPO_ID, then {DEFAULT_HF_REPO_ID}."
        ),
    )
    parser.add_argument(
        "--articles-hf-repo-id",
        default=None,
        help=(
            "Hugging Face dataset repo ID for the article source set. Defaults to the "
            "legacy repo ID or the article-specific baseline."
        ),
    )
    parser.add_argument(
        "--definitions-hf-repo-id",
        default=None,
        help=(
            "Hugging Face dataset repo ID for the definition source set. Defaults to the "
            "legacy repo ID or the definitions-specific baseline."
        ),
    )
    parser.add_argument(
        "--hf-collection",
        default=DEFAULT_HF_COLLECTION,
        help="Collection slug to update after each source set is uploaded. Use an empty value to skip.",
    )
    parser.add_argument(
        "--skip-collection",
        action="store_true",
        help="Skip collection update entirely; useful when the token lacks collection permissions.",
    )
    parser.add_argument(
        "--hf-path-prefix",
        default="benchmark_sources",
        help="Repository directory under which the two source sets are stored.",
    )
    parser.add_argument("--articles-jsonl", type=Path, default=DEFAULT_ARTICLES_JSONL)
    parser.add_argument("--articles-metadata", type=Path, default=DEFAULT_ARTICLES_METADATA)
    parser.add_argument("--definitions-jsonl", type=Path, default=DEFAULT_DEFINITIONS_JSONL)
    parser.add_argument("--definitions-metadata", type=Path, default=DEFAULT_DEFINITIONS_METADATA)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    articles_repo_id = args.articles_hf_repo_id or args.hf_repo_id or DEFAULT_ARTICLES_HF_REPO_ID
    definitions_repo_id = (
        args.definitions_hf_repo_id or args.hf_repo_id or DEFAULT_DEFINITIONS_HF_REPO_ID
    )
    collection_slug = None if args.skip_collection else args.hf_collection

    upload_jrc_source_set(
        name="jrc_acquis_anchored_articles",
        jsonl_path=args.articles_jsonl,
        metadata_path=args.articles_metadata,
        repo_id=articles_repo_id,
        path_prefix=args.hf_path_prefix,
        collection_slug=collection_slug,
    )
    upload_jrc_source_set(
        name="jrc_acquis_anchored_definitions",
        jsonl_path=args.definitions_jsonl,
        metadata_path=args.definitions_metadata,
        repo_id=definitions_repo_id,
        path_prefix=args.hf_path_prefix,
        collection_slug=collection_slug,
    )


def upload_jrc_source_set(
    *,
    name: str,
    jsonl_path: Path,
    metadata_path: Path,
    repo_id: str | None,
    path_prefix: str,
    collection_slug: str | None,
) -> None:
    settings = load_settings()
    resolved_repo_id = repo_id or settings.hf_repo_id or DEFAULT_HF_REPO_ID
    if not resolved_repo_id:
        raise ValueError(
            "--hf-repo-id, CHEM_MT_HF_REPO_ID, or HF_REPO_ID is required for Hugging Face upload."
        )
    if not settings.hf_token:
        raise ValueError("CHEM_MT_HF_TOKEN or HF_TOKEN is required for Hugging Face upload.")

    source_paths = (jsonl_path, metadata_path)
    missing_paths = [path for path in source_paths if not path.is_file()]
    if missing_paths:
        missing = ", ".join(str(path) for path in missing_paths)
        raise FileNotFoundError(f"JRC benchmark source files do not exist: {missing}")

    api = HfApi(token=settings.hf_token)
    api.create_repo(
        repo_id=resolved_repo_id,
        repo_type="dataset",
        exist_ok=True,
    )
    normalized_prefix = path_prefix.strip("/")
    source_prefix = f"{normalized_prefix}/{name}" if normalized_prefix else name
    for local_path in source_paths:
        path_in_repo = f"{source_prefix}/{local_path.name}"
        api.upload_file(
            path_or_fileobj=local_path,
            path_in_repo=path_in_repo,
            repo_id=resolved_repo_id,
            repo_type="dataset",
            commit_message=f"Upload {name} benchmark source {local_path.name}",
        )
        print(f"Uploaded {local_path} to {resolved_repo_id}/{path_in_repo}")

    readme_text = build_repo_readme(
        section_type="article" if "articles" in name else "definition",
        repo_id=resolved_repo_id,
        metadata_path=metadata_path,
        jsonl_path=jsonl_path,
    )
    api.upload_file(
        path_or_fileobj=BytesIO(readme_text.encode("utf-8")),
        path_in_repo="README.md",
        repo_id=resolved_repo_id,
        repo_type="dataset",
        commit_message=f"Add README for {name} benchmark source",
    )
    print(f"Uploaded README.md to {resolved_repo_id}/README.md")

    if collection_slug:
        api.add_collection_item(
            collection_slug=collection_slug,
            item_id=resolved_repo_id,
            item_type="dataset",
            exists_ok=True,
        )
        print(f"Added {resolved_repo_id} to collection {collection_slug}")


if __name__ == "__main__":
    main()
