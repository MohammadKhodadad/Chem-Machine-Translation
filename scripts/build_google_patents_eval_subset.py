from __future__ import annotations

import argparse
import csv
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from openai import OpenAI

from chem_machine_translation.config import DEFAULT_MODEL, load_settings
from chem_machine_translation.data.google_patents import LANGUAGE_NAMES
from chem_machine_translation.data.terminology import DatasetTerminologyGenerator
from chem_machine_translation.utils.text import approximate_token_count, normalize_text

ALL_LANGUAGE_NAMES = {"en": "English", **LANGUAGE_NAMES}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a Google Patents evaluation subset.")
    parser.add_argument("--source-dir", type=Path, default=Path("data/preprocessed"))
    parser.add_argument("--raw-ndjson", type=Path, default=Path("data/chemistry_patents.ndjson"))
    parser.add_argument(
        "--source-pairs-jsonl",
        type=Path,
        default=None,
        help=(
            "Optional JSONL of preselected source-target pairs with source_text and "
            "target_text fields."
        ),
    )
    parser.add_argument("--manifest-template", type=Path, default=None)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("benchmark_datasets/google_patents_eval_subset_generated"),
    )
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument(
        "--language",
        action="append",
        dest="languages",
        choices=sorted(ALL_LANGUAGE_NAMES),
    )
    parser.add_argument("--min-input-tokens", type=int, default=128)
    parser.add_argument("--max-input-tokens", type=int, default=384)
    parser.add_argument("--text-field", default="context", choices=["context", "abstract", "title"])
    parser.add_argument("--extract-terminology", action="store_true")
    parser.add_argument("--terminology-model", default=DEFAULT_MODEL)
    parser.add_argument("--terminology-max-terms", type=int, default=20)
    parser.add_argument("--iate-terminology", action="store_true")
    parser.add_argument("--wikidata-terminology", action="store_true")
    parser.add_argument("--wikipedia-terminology", action="store_true")
    parser.add_argument("--pubchem-terminology", action="store_true")
    parser.add_argument("--terminology-cache", type=Path, default=None)
    parser.add_argument("--terminology-workers", type=int, default=1)
    parser.add_argument("--openai-timeout", type=float, default=120.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    languages = args.languages or ["fr", "de", "es", "pt", "nl", "zh"]
    generator = build_generator(args)
    if args.source_pairs_jsonl:
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
            generator=generator,
            terminology_workers=max(1, args.terminology_workers),
        )
        return

    if args.manifest_template:
        selected, languages = select_pairs_from_manifest_template(
            manifest_template=args.manifest_template,
            raw_ndjson=args.raw_ndjson,
            languages=args.languages,
        )
    else:
        rows_by_language = {
            language: load_language_csv(args.source_dir / f"{language}.csv")
            for language in ["en", *languages]
        }
        selected = select_pairs(
            rows_by_language=rows_by_language,
            languages=languages,
            limit=args.limit,
            text_field=args.text_field,
            min_input_tokens=args.min_input_tokens,
            max_input_tokens=args.max_input_tokens,
        )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_language_csvs(args.output_dir, selected, languages)
    pair_count = sum(len(v) for v in selected.values())
    manifest_path = (
        args.output_dir / args.manifest_template.name
        if args.manifest_template
        else args.output_dir / f"google-patents-subset-{pair_count}-manifest.jsonl"
    )
    write_manifest(
        manifest_path=manifest_path,
        selected=selected,
        languages=languages,
        text_field=args.text_field,
        generator=generator,
        terminology_workers=max(1, args.terminology_workers),
    )
    print(f"Wrote {pair_count} source-target pairs.")
    print(f"Manifest: {manifest_path}")


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
    if source_language not in ALL_LANGUAGE_NAMES:
        raise ValueError(f"Unsupported source language in pair JSONL: {source_language}")
    if target_language not in ALL_LANGUAGE_NAMES:
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
        "context": str(row["source_text"]),
    }
    target_row = {
        "id": f"{example_id}_target",
        "doc_id": str(row.get("doc_id") or ""),
        "language": str(row["target_language"]),
        "context": str(row["target_text"]),
    }
    return {
        "dataset": "google_patents",
        "source_id": example_id,
        "direction": direction,
        "source_language": ALL_LANGUAGE_NAMES[str(row["source_language"])],
        "source_language_code": str(row["source_language"]),
        "target_language": ALL_LANGUAGE_NAMES[str(row["target_language"])],
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
        "text_field": "context",
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


def load_language_csv(csv_path: Path) -> dict[str, dict[str, str]]:
    rows = {}
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            publication_number = row.get("publication_number")
            if publication_number:
                rows[publication_number] = row
    return rows


def select_pairs(
    rows_by_language: dict[str, dict[str, dict[str, str]]],
    languages: list[str],
    limit: int,
    text_field: str,
    min_input_tokens: int,
    max_input_tokens: int,
) -> dict[str, list[tuple[dict[str, str], dict[str, str]]]]:
    source_rows = rows_by_language["en"]
    selected: dict[str, list[tuple[dict[str, str], dict[str, str]]]] = {
        language: [] for language in languages
    }
    for language in languages:
        target_rows = rows_by_language[language]
        for publication_number in sorted(source_rows):
            if publication_number not in target_rows:
                continue
            source_text = normalize_text(source_rows[publication_number].get(text_field, ""))
            target_text = normalize_text(target_rows[publication_number].get(text_field, ""))
            token_count = approximate_token_count(source_text)
            if (
                not source_text
                or not target_text
                or token_count < min_input_tokens
                or token_count > max_input_tokens
            ):
                continue
            selected[language].append(
                (source_rows[publication_number], target_rows[publication_number])
            )
            if len(selected[language]) >= limit:
                break
    return selected


def select_pairs_from_manifest_template(
    manifest_template: Path,
    raw_ndjson: Path,
    languages: list[str] | None,
) -> tuple[dict[str, list[tuple[dict[str, str], dict[str, str]]]], list[str]]:
    template_rows = [
        json.loads(line)
        for line in manifest_template.read_text(encoding="utf-8", errors="replace").splitlines()
        if line.strip()
    ]
    selected_languages = languages or sorted(
        {str(row["target_language_code"]) for row in template_rows}
    )
    publications = {str(row["publication_number"]) for row in template_rows}
    patents = load_raw_patents_by_publication(raw_ndjson, publications)
    selected: dict[str, list[tuple[dict[str, str], dict[str, str]]]] = {
        language: [] for language in selected_languages
    }

    for template_row in template_rows:
        language = str(template_row["target_language_code"])
        if language not in selected:
            continue
        publication_number = str(template_row["publication_number"])
        patent = patents.get(publication_number)
        if not patent:
            continue
        source_row = raw_patent_row(
            patent=patent,
            language="en",
            row_id=str(template_row.get("source_row_id") or f"{publication_number}_en"),
            selection=str(template_row.get("selection") or ""),
        )
        target_row = raw_patent_row(
            patent=patent,
            language=language,
            row_id=str(template_row.get("target_row_id") or f"{publication_number}_{language}"),
            selection=str(template_row.get("selection") or ""),
        )
        if source_row["context"] and target_row["context"]:
            selected[language].append((source_row, target_row))

    return selected, selected_languages


def load_raw_patents_by_publication(
    raw_ndjson: Path,
    publications: set[str],
) -> dict[str, dict]:
    patents = {}
    with raw_ndjson.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line.strip():
                continue
            patent = json.loads(line)
            publication_number = str(patent.get("publication_number") or "")
            if publication_number in publications:
                patents[publication_number] = patent
                if len(patents) == len(publications):
                    break
    return patents


def raw_patent_row(
    patent: dict,
    language: str,
    row_id: str,
    selection: str,
) -> dict[str, str]:
    title = localized_text(patent, "title_localized", language)
    abstract = localized_text(patent, "abstract_localized", language)
    context = (
        normalize_text(f"Title: {title}\n\nAbstract: {abstract}") if title and abstract else ""
    )
    return {
        "id": row_id,
        "language": language,
        "title": normalize_text(title),
        "abstract": normalize_text(abstract),
        "description": "",
        "first_claim": "",
        "context": context,
        "publication_number": str(patent.get("publication_number") or ""),
        "family_id": str(patent.get("family_id") or ""),
        "country_code": str(patent.get("country_code") or ""),
        "publication_date": str(patent.get("publication_date") or ""),
        "source": "google_patents_raw",
        "selection": selection,
    }


def localized_text(patent: dict, field: str, language: str) -> str:
    for item in patent.get(field, []):
        if item.get("language") == language:
            return str(item.get("text") or "")
    return ""


def write_language_csvs(
    output_dir: Path,
    selected: dict[str, list[tuple[dict[str, str], dict[str, str]]]],
    languages: list[str],
) -> None:
    source_rows_by_id = {
        source_row.get("publication_number", ""): source_row
        for pairs in selected.values()
        for source_row, _ in pairs
    }
    write_rows(output_dir / "en.csv", list(source_rows_by_id.values()))
    for language in languages:
        write_rows(
            output_dir / f"{language}.csv",
            [target_row for _, target_row in selected[language]],
        )


def write_rows(csv_path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        return
    fieldnames = sorted({field for row in rows for field in row})
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_generator(args: argparse.Namespace) -> DatasetTerminologyGenerator | None:
    if not (
        args.extract_terminology
        or args.iate_terminology
        or args.wikidata_terminology
        or args.wikipedia_terminology
        or args.pubchem_terminology
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
        cache_path=args.terminology_cache,
    )


def write_manifest(
    manifest_path: Path,
    selected: dict[str, list[tuple[dict[str, str], dict[str, str]]]],
    languages: list[str],
    text_field: str,
    generator: DatasetTerminologyGenerator | None,
    terminology_workers: int = 1,
) -> None:
    manifest_rows = [
        build_manifest_row(
            source_row=source_row,
            target_row=target_row,
            language=language,
            text_field=text_field,
        )
        for language in languages
        for source_row, target_row in selected[language]
    ]
    if generator:
        if terminology_workers == 1:
            manifest_rows = [add_terminology(row, generator) for row in manifest_rows]
        else:
            with ThreadPoolExecutor(max_workers=terminology_workers) as executor:
                manifest_rows = list(
                    executor.map(lambda row: add_terminology(row, generator), manifest_rows)
                )

    temp_path = manifest_path.with_suffix(manifest_path.suffix + ".tmp")
    with temp_path.open("w", encoding="utf-8") as handle:
        for row in manifest_rows:
            output_row = {
                key: value
                for key, value in row.items()
                if key not in {"_source_text", "_target_text"}
            }
            handle.write(json.dumps(output_row, ensure_ascii=False) + "\n")
    temp_path.replace(manifest_path)


def build_manifest_row(
    source_row: dict[str, str],
    target_row: dict[str, str],
    language: str,
    text_field: str,
) -> dict:
    source_text = normalize_text(source_row.get(text_field, ""))
    target_text = normalize_text(target_row.get(text_field, ""))
    publication_number = source_row.get("publication_number")
    return {
        "source_id": publication_number,
        "target_language": LANGUAGE_NAMES[language],
        "target_language_code": language,
        "source_row_id": source_row.get("id"),
        "target_row_id": target_row.get("id"),
        "publication_number": publication_number,
        "family_id": source_row.get("family_id"),
        "country_code": source_row.get("country_code"),
        "publication_date": source_row.get("publication_date"),
        "approx_source_tokens": approximate_token_count(source_text),
        "text_field": text_field,
        "selection": source_row.get("selection") or "requires_source_and_target_text_token_window",
        "_source_text": source_text,
        "_target_text": target_text,
    }


def add_terminology(row: dict, generator: DatasetTerminologyGenerator) -> dict:
    print(
        f"Generating terminology for {row['publication_number']} -> {row['target_language']}",
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


if __name__ == "__main__":
    main()
