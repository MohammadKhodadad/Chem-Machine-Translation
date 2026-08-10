from __future__ import annotations

import argparse
import csv
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from openai import OpenAI

from chem_machine_translation.config import DEFAULT_MODEL, load_settings
from chem_machine_translation.data.terminology import DatasetTerminologyGenerator
from chem_machine_translation.utils.text import approximate_token_count, normalize_text

LANGUAGE_NAMES = {
    "de": "German",
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "nl": "Dutch",
    "pt": "Portuguese",
    "zh": "Chinese",
}
DEFAULT_LANGUAGES = ("de", "en", "es", "fr", "pt", "zh")
TEXT_FIELD = "context"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a Google Patents benchmark dataset from a source-pair JSONL snapshot.",
    )
    parser.add_argument(
        "--source-pairs-jsonl",
        type=Path,
        required=True,
        help="Tracked benchmark source-pair JSONL with source_text and target_text fields.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("benchmark_datasets/google_patents_eval_subset_generated"),
    )
    parser.add_argument("--limit", type=int, default=50, help="Rows per ordered direction.")
    parser.add_argument(
        "--language",
        action="append",
        dest="languages",
        choices=sorted(LANGUAGE_NAMES),
        help="Language included in benchmark generation. Repeat for multiple languages.",
    )
    parser.add_argument("--min-input-tokens", type=int, default=128)
    parser.add_argument("--max-input-tokens", type=int, default=384)
    parser.add_argument("--extract-terminology", action="store_true")
    parser.add_argument("--terminology-model", default=DEFAULT_MODEL)
    parser.add_argument("--terminology-max-terms", type=int, default=20)
    parser.add_argument("--iate-terminology", action="store_true")
    parser.add_argument("--wikidata-terminology", action="store_true")
    parser.add_argument("--wikipedia-terminology", action="store_true")
    parser.add_argument("--pubchem-terminology", action="store_true")
    parser.add_argument("--chebi-terminology", action="store_true")
    parser.add_argument("--chembl-terminology", action="store_true")
    parser.add_argument("--mesh-terminology", action="store_true")
    parser.add_argument("--nci-terminology", action="store_true")
    parser.add_argument("--agrovoc-terminology", action="store_true")
    parser.add_argument("--terminology-cache", type=Path, default=None)
    parser.add_argument("--terminology-workers", type=int, default=1)
    parser.add_argument("--openai-timeout", type=float, default=120.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pair_rows = select_source_pair_rows(
        source_pairs_jsonl=args.source_pairs_jsonl,
        languages=args.languages,
        limit=args.limit,
        min_input_tokens=args.min_input_tokens,
        max_input_tokens=args.max_input_tokens,
    )
    write_source_pair_dataset(
        output_dir=args.output_dir,
        pair_rows=pair_rows,
        generator=build_generator(args),
        terminology_workers=max(1, args.terminology_workers),
    )


def select_source_pair_rows(
    *,
    source_pairs_jsonl: Path,
    languages: list[str] | None,
    limit: int,
    min_input_tokens: int,
    max_input_tokens: int,
) -> dict[str, list[dict[str, Any]]]:
    selected: dict[str, list[dict[str, Any]]] = {}
    language_filter = set(languages or [])
    with source_pairs_jsonl.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = normalize_source_pair_row(json.loads(line))
            if language_filter and (
                row["source_language"] not in language_filter
                or row["target_language"] not in language_filter
            ):
                continue
            token_count = approximate_token_count(row["source_text"])
            if (
                not row["source_text"]
                or not row["target_text"]
                or token_count < min_input_tokens
                or token_count > max_input_tokens
            ):
                continue
            direction = row["language_pair"]
            selected.setdefault(direction, [])
            if len(selected[direction]) < limit:
                selected[direction].append(row)
    return {direction: rows for direction, rows in selected.items() if rows}


def normalize_source_pair_row(row: dict[str, Any]) -> dict[str, Any]:
    source_language = str(row.get("source_language") or "").strip().lower()
    target_language = str(row.get("target_language") or "").strip().lower()
    if not source_language or not target_language:
        language_pair = str(row.get("language_pair") or "")
        source_language, _, target_language = language_pair.partition("-")
    direction = f"{source_language}-{target_language}"
    if source_language not in LANGUAGE_NAMES:
        raise ValueError(f"Unsupported source language in pair JSONL: {source_language}")
    if target_language not in LANGUAGE_NAMES:
        raise ValueError(f"Unsupported target language in pair JSONL: {target_language}")
    return {
        **row,
        "language_pair": direction,
        "source_language": source_language,
        "target_language": target_language,
        "source_text": normalize_text(str(row.get("source_text") or "")),
        "target_text": normalize_text(str(row.get("target_text") or "")),
    }


def write_source_pair_dataset(
    *,
    output_dir: Path,
    pair_rows: dict[str, list[dict[str, Any]]],
    generator: DatasetTerminologyGenerator | None,
    terminology_workers: int,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    combined_rows = []
    for direction, rows in sorted(pair_rows.items()):
        direction_dir = output_dir / direction
        direction_dir.mkdir(parents=True, exist_ok=True)
        manifest_rows = [build_source_pair_manifest_row(row) for row in rows]
        manifest_rows = add_terminology_parallel(
            rows=manifest_rows,
            generator=generator,
            workers=terminology_workers,
        )
        write_rows(direction_dir / "source.csv", [row["_source_row"] for row in manifest_rows])
        write_rows(direction_dir / "target.csv", [row["_target_row"] for row in manifest_rows])
        manifest_path = (
            direction_dir / f"google-patents-{direction}-{len(manifest_rows)}-manifest.jsonl"
        )
        write_manifest_rows(manifest_path, manifest_rows)
        combined_rows.extend(manifest_rows)

    combined_path = (
        output_dir
        / f"google-patents-{len(pair_rows)}-directions-{len(combined_rows)}-manifest.jsonl"
    )
    write_manifest_rows(combined_path, combined_rows)
    print(f"Wrote {len(pair_rows)} directions and {len(combined_rows)} pairs.")
    print(f"Combined manifest: {combined_path}")


def build_source_pair_manifest_row(row: dict[str, Any]) -> dict[str, Any]:
    example_id = str(row.get("example_id") or row.get("doc_id") or "")
    direction = str(row["language_pair"])
    source_row = {
        "id": f"{example_id}_source",
        "doc_id": str(row.get("doc_id") or ""),
        "language": str(row["source_language"]),
        TEXT_FIELD: str(row["source_text"]),
    }
    target_row = {
        "id": f"{example_id}_target",
        "doc_id": str(row.get("doc_id") or ""),
        "language": str(row["target_language"]),
        TEXT_FIELD: str(row["target_text"]),
    }
    return {
        "dataset": "google_patents",
        "source_id": example_id,
        "direction": direction,
        "source_language": LANGUAGE_NAMES[str(row["source_language"])],
        "source_language_code": str(row["source_language"]),
        "target_language": LANGUAGE_NAMES[str(row["target_language"])],
        "target_language_code": str(row["target_language"]),
        "source_row_id": source_row["id"],
        "target_row_id": target_row["id"],
        "example_id": example_id,
        "doc_id": str(row.get("doc_id") or ""),
        "corpus_id": str(row.get("corpus_id") or ""),
        "publication_number": str(row.get("doc_id") or ""),
        "family_id": str(row.get("group_key") or ""),
        "country_code": str(row.get("source") or ""),
        "publication_date": str(row.get("pub_date") or ""),
        "field": str(row.get("field") or ""),
        "approx_source_tokens": approximate_token_count(str(row["source_text"])),
        "text_field": TEXT_FIELD,
        "selection": str(row.get("selection_rule") or "preselected_source_target_pair"),
        "_source_text": str(row["source_text"]),
        "_target_text": str(row["target_text"]),
        "_source_row": source_row,
        "_target_row": target_row,
    }


def add_terminology_parallel(
    *,
    rows: list[dict[str, Any]],
    generator: DatasetTerminologyGenerator | None,
    workers: int,
) -> list[dict[str, Any]]:
    if not generator:
        return rows
    if workers == 1:
        return [add_terminology(row, generator) for row in rows]
    with ThreadPoolExecutor(max_workers=workers) as executor:
        return list(executor.map(lambda row: add_terminology(row, generator), rows))


def add_terminology(row: dict[str, Any], generator: DatasetTerminologyGenerator) -> dict[str, Any]:
    print(
        f"Generating terminology for {row['source_id']} -> {row['target_language']}",
        flush=True,
    )
    row["terminology"] = [
        term.to_json()
        for term in generator.generate(
            source_text=row["_source_text"],
            target_language=row["target_language"],
            reference_text=row["_target_text"],
        )
    ]
    return row


def build_generator(args: argparse.Namespace) -> DatasetTerminologyGenerator | None:
    if not (
        args.extract_terminology
        or args.iate_terminology
        or args.wikidata_terminology
        or args.wikipedia_terminology
        or args.pubchem_terminology
        or args.chebi_terminology
        or args.chembl_terminology
        or args.mesh_terminology
        or args.nci_terminology
        or args.agrovoc_terminology
    ):
        return None
    client = None
    if args.extract_terminology:
        settings = load_settings()
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for LLM target terminology extraction.")
        client = OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            timeout=args.openai_timeout,
        )
    return DatasetTerminologyGenerator(
        client=client,
        model=args.terminology_model,
        max_terms=args.terminology_max_terms,
        use_llm=args.extract_terminology,
        use_iate=args.iate_terminology,
        use_wikidata=args.wikidata_terminology or args.wikipedia_terminology,
        use_pubchem=args.pubchem_terminology,
        use_chebi=args.chebi_terminology,
        use_chembl=args.chembl_terminology,
        use_mesh=args.mesh_terminology,
        use_nci=args.nci_terminology,
        use_agrovoc=args.agrovoc_terminology,
        cache_path=args.terminology_cache,
    )


def write_rows(csv_path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = sorted({field for row in rows for field in row})
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_manifest_rows(manifest_path: Path, rows: list[dict[str, Any]]) -> None:
    temp_path = manifest_path.with_suffix(manifest_path.suffix + ".tmp")
    with temp_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            output_row = {
                key: value
                for key, value in row.items()
                if key not in {"_source_text", "_target_text", "_source_row", "_target_row"}
            }
            handle.write(json.dumps(output_row, ensure_ascii=False) + "\n")
    temp_path.replace(manifest_path)


if __name__ == "__main__":
    main()
