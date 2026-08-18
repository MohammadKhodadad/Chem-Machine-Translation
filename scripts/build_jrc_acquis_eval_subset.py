from __future__ import annotations

import argparse
import csv
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from openai import OpenAI

from chem_machine_translation.config import DEFAULT_MODEL, load_settings
from chem_machine_translation.data.terminology import (
    DatasetTerminologyGenerator,
    LegalTerminologyGenerator,
    dataset_term_from_json,
    deduplicate_terms,
)
from chem_machine_translation.utils.text import approximate_token_count, normalize_text

TEXT_FIELD = "context"
LANGUAGE_NAMES = {
    "de": "German",
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "pt": "Portuguese",
}
DEFAULT_LANGUAGES = ("en", "es", "de", "fr", "pt")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a JRC-Acquis benchmark dataset from a source-pair JSONL snapshot.",
    )
    parser.add_argument(
        "--source-pairs-jsonl",
        type=Path,
        required=True,
        help="Benchmark source-pair JSONL created by create_jrc_acquis_source_pairs.py.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("benchmark_datasets/jrc_acquis_chunks"),
    )
    parser.add_argument(
        "--language",
        action="append",
        dest="languages",
        choices=sorted(LANGUAGE_NAMES),
        help="Language included in all ordered pair generation. Repeat for multiple languages.",
    )
    parser.add_argument("--limit", type=int, default=250, help="Rows per ordered direction.")
    parser.add_argument("--extract-legal-terms", action="store_true")
    parser.add_argument("--legal-terminology-model", default=DEFAULT_MODEL)
    parser.add_argument("--legal-terminology-max-terms", type=int, default=20)
    parser.add_argument("--legal-terminology-cache", type=Path, default=None)
    parser.add_argument("--legal-terminology-workers", type=int, default=1)
    parser.add_argument("--extract-stanza-terms", action="store_true")
    parser.add_argument("--stanza-terminology-max-terms", type=int, default=20)
    parser.add_argument("--stanza-terminology-cache", type=Path, default=None)
    parser.add_argument("--iate-terminology", action="store_true")
    parser.add_argument("--wikipedia-terminology", action="store_true")
    parser.add_argument("--unterm-terminology", action="store_true")
    parser.add_argument("--pubchem-terminology", action="store_true")
    parser.add_argument("--chebi-terminology", action="store_true")
    parser.add_argument("--chembl-terminology", action="store_true")
    parser.add_argument("--mesh-terminology", action="store_true")
    parser.add_argument("--nci-terminology", action="store_true")
    parser.add_argument("--agrovoc-terminology", action="store_true")
    parser.add_argument("--openai-timeout", type=float, default=120.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    languages = tuple(dict.fromkeys(args.languages or DEFAULT_LANGUAGES))
    if len(languages) < 2:
        raise ValueError("At least two languages are required.")
    legal_generator = build_legal_generator(args)
    stanza_generator = build_stanza_generator(args)
    pair_rows = select_source_pair_rows(
        source_pairs_jsonl=args.source_pairs_jsonl,
        languages=languages,
        limit=args.limit,
    )
    write_source_pair_dataset(
        output_dir=args.output_dir,
        pair_rows=pair_rows,
        legal_generator=legal_generator,
        stanza_generator=stanza_generator,
        legal_terminology_workers=max(1, args.legal_terminology_workers),
    )


def build_legal_generator(args: argparse.Namespace) -> LegalTerminologyGenerator | None:
    if not args.extract_legal_terms:
        return None
    settings = load_settings()
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is required for legal LLM terminology extraction.")
    client = OpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        timeout=args.openai_timeout,
    )
    return LegalTerminologyGenerator(
        client=client,
        model=args.legal_terminology_model,
        max_terms=args.legal_terminology_max_terms,
        use_iate=args.iate_terminology,
        use_wikidata=args.wikipedia_terminology,
        use_unterm=args.unterm_terminology,
        cache_path=args.legal_terminology_cache,
    )


def build_stanza_generator(args: argparse.Namespace) -> DatasetTerminologyGenerator | None:
    if not args.extract_stanza_terms:
        return None
    return DatasetTerminologyGenerator(
        max_terms=args.stanza_terminology_max_terms,
        use_iate=args.iate_terminology,
        use_wikidata=args.wikipedia_terminology,
        use_pubchem=args.pubchem_terminology,
        use_chebi=args.chebi_terminology,
        use_chembl=args.chembl_terminology,
        use_mesh=args.mesh_terminology,
        use_nci=args.nci_terminology,
        use_agrovoc=args.agrovoc_terminology,
        use_unterm=args.unterm_terminology,
        cache_path=args.stanza_terminology_cache,
    )


def select_source_pair_rows(
    *,
    source_pairs_jsonl: Path,
    languages: tuple[str, ...],
    limit: int,
) -> dict[str, list[dict[str, Any]]]:
    selected: dict[str, list[dict[str, Any]]] = {}
    language_filter = set(languages)
    with source_pairs_jsonl.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = normalize_source_pair_row(json.loads(line))
            if (
                row["source_language"] not in language_filter
                or row["target_language"] not in language_filter
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
        direction = str(row.get("language_pair") or "")
        source_language, _, target_language = direction.partition("-")
    if source_language not in LANGUAGE_NAMES:
        raise ValueError(f"Unsupported source language in JRC source JSONL: {source_language}")
    if target_language not in LANGUAGE_NAMES:
        raise ValueError(f"Unsupported target language in JRC source JSONL: {target_language}")
    direction = f"{source_language}-{target_language}"
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
    legal_generator: LegalTerminologyGenerator | None,
    stanza_generator: DatasetTerminologyGenerator | None,
    legal_terminology_workers: int,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    combined_rows = []
    stanza_term_cache: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for direction, rows in sorted(pair_rows.items()):
        direction_dir = output_dir / direction
        direction_dir.mkdir(parents=True, exist_ok=True)
        manifest_rows = [build_source_pair_manifest_row(row=row) for row in rows]
        manifest_rows = add_legal_terms_parallel(
            rows=manifest_rows,
            generator=legal_generator,
            workers=legal_terminology_workers,
        )
        manifest_rows = add_stanza_terms(
            rows=manifest_rows,
            generator=stanza_generator,
            term_cache=stanza_term_cache,
        )
        write_rows(direction_dir / "source.csv", [row["_source_row"] for row in manifest_rows])
        write_rows(direction_dir / "target.csv", [row["_target_row"] for row in manifest_rows])
        manifest_path = (
            direction_dir / f"jrc-acquis-{direction}-{len(manifest_rows)}-manifest.jsonl"
        )
        write_manifest(manifest_path, manifest_rows)
        combined_rows.extend(manifest_rows)

    combined_path = (
        output_dir
        / f"jrc-acquis-{len(pair_rows)}-directions-{len(combined_rows)}-manifest.jsonl"
    )
    write_manifest(combined_path, combined_rows)
    print(f"Wrote {len(pair_rows)} directions and {len(combined_rows)} chunks.")
    print(f"Combined manifest: {combined_path}")


def build_source_pair_manifest_row(*, row: dict[str, Any]) -> dict[str, Any]:
    example_id = str(row.get("example_id") or row["language_pair"])
    source_language = str(row["source_language"])
    target_language = str(row["target_language"])
    source_text = str(row["source_text"])
    target_text = str(row["target_text"])
    doc_id = str(row.get("doc_id") or "unknown")
    source_row = {
        "id": f"{example_id}_source",
        "doc_id": doc_id,
        "language": source_language,
        TEXT_FIELD: source_text,
    }
    target_row = {
        "id": f"{example_id}_target",
        "doc_id": doc_id,
        "language": target_language,
        TEXT_FIELD: target_text,
    }
    return {
        "dataset": "jrc_acquis",
        "source_id": example_id,
        "direction": str(row["language_pair"]),
        "source_language": LANGUAGE_NAMES[source_language],
        "source_language_code": source_language,
        "target_language": LANGUAGE_NAMES[target_language],
        "target_language_code": target_language,
        "source_row_id": source_row["id"],
        "target_row_id": target_row["id"],
        "doc_id": doc_id,
        "chunk_id": example_id,
        "segment_count": int(row.get("segment_count") or 0),
        "approx_source_tokens": approximate_token_count(source_text),
        "approx_target_tokens": approximate_token_count(target_text),
        "text_field": TEXT_FIELD,
        "selection": str(row.get("selection") or "jrc_acquis_source_pair_snapshot"),
        "terminology": [],
        "_source_text": source_text,
        "_target_text": target_text,
        "_source_row": source_row,
        "_target_row": target_row,
    }


def add_legal_terms_parallel(
    rows: list[dict[str, Any]],
    generator: LegalTerminologyGenerator | None,
    workers: int,
) -> list[dict[str, Any]]:
    if generator is None:
        return rows
    if workers == 1:
        return [add_legal_terms(row, generator) for row in rows]
    with ThreadPoolExecutor(max_workers=workers) as executor:
        return list(executor.map(lambda row: add_legal_terms(row, generator), rows))


def add_legal_terms(
    row: dict[str, Any],
    generator: LegalTerminologyGenerator,
) -> dict[str, Any]:
    print(
        f"Generating legal terms for {row['chunk_id']} -> {row['target_language']}",
        flush=True,
    )
    legal_terms = generator.generate(
        target_language=row["target_language"],
        reference_text=row["_target_text"],
        eurovoc_descriptors={},
    )
    row["terminology"] = [term.to_json() for term in deduplicate_terms(legal_terms)]
    return row


def add_stanza_terms(
    rows: list[dict[str, Any]],
    generator: DatasetTerminologyGenerator | None,
    term_cache: dict[tuple[str, str], list[dict[str, Any]]] | None = None,
) -> list[dict[str, Any]]:
    if generator is None:
        return rows
    return [add_stanza_terms_to_row(row, generator, term_cache=term_cache) for row in rows]


def add_stanza_terms_to_row(
    row: dict[str, Any],
    generator: DatasetTerminologyGenerator,
    term_cache: dict[tuple[str, str], list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    cache_key = stanza_term_cache_key(row)
    cached_terms = term_cache.get(cache_key) if term_cache is not None else None
    if cached_terms is None:
        print(
            f"Generating Stanza terms for {row['chunk_id']} -> {row['target_language']}",
            flush=True,
        )
        stanza_terms = generator.generate(
            source_text=row["_source_text"],
            target_language=row["target_language"],
            reference_text=row["_target_text"],
        )
        cached_terms = [term.to_json() for term in stanza_terms]
        if term_cache is not None:
            term_cache[cache_key] = cached_terms
    else:
        print(
            f"Reusing Stanza terms for {row['chunk_id']} -> {row['target_language']}",
            flush=True,
        )
    existing_terms = [
        dataset_term_from_json(term)
        for term in row["terminology"]
        if isinstance(term, dict)
    ]
    stanza_terms = [dataset_term_from_json(term) for term in cached_terms]
    row["terminology"] = [
        term.to_json() for term in deduplicate_terms(existing_terms + stanza_terms)
    ]
    return row


def stanza_term_cache_key(row: dict[str, Any]) -> tuple[str, str]:
    target_language = str(row.get("target_language_code") or row["target_language"])
    return target_language, row["_target_text"]


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
