from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from openai import OpenAI

from chem_machine_translation.config import DEFAULT_MODEL, load_settings
from chem_machine_translation.data.epo import LANGUAGE_NAMES, normalize_language_code
from chem_machine_translation.data.terminology import DatasetTerminologyGenerator
from chem_machine_translation.utils.text import approximate_token_count, normalize_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build an EPO evaluation subset.")
    parser.add_argument("--source-csv", type=Path, default=Path("data/EPO.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("examples/epo_eval_subset_100"))
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument(
        "--language",
        action="append",
        dest="languages",
        choices=sorted(LANGUAGE_NAMES),
    )
    parser.add_argument("--min-input-tokens", type=int, default=128)
    parser.add_argument("--max-input-tokens", type=int, default=384)
    parser.add_argument(
        "--text-field",
        default="context",
        choices=["context", "first_claim", "title"],
    )
    parser.add_argument("--extract-terminology", action="store_true")
    parser.add_argument("--terminology-model", default=DEFAULT_MODEL)
    parser.add_argument("--terminology-max-terms", type=int, default=20)
    parser.add_argument("--iate-terminology", action="store_true")
    parser.add_argument("--wikidata-terminology", action="store_true")
    parser.add_argument("--refine-terminology", action="store_true")
    parser.add_argument("--terminology-confidence-threshold", type=float, default=0.85)
    parser.add_argument("--terminology-cache", type=Path, default=None)
    parser.add_argument("--terminology-workers", type=int, default=1)
    parser.add_argument("--openai-timeout", type=float, default=120.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    languages = args.languages or ["fr", "de"]
    rows_by_language = load_rows_by_language(args.source_csv)
    selected = select_publications(
        rows_by_language=rows_by_language,
        languages=languages,
        limit=args.limit,
        text_field=args.text_field,
        min_input_tokens=args.min_input_tokens,
        max_input_tokens=args.max_input_tokens,
    )
    generator = build_generator(args)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_language_csvs(args.output_dir, selected, languages)
    manifest_path = args.output_dir / f"epo-subset-{len(selected) * len(languages)}-manifest.jsonl"
    write_manifest(
        manifest_path=manifest_path,
        selected=selected,
        languages=languages,
        text_field=args.text_field,
        generator=generator,
        terminology_workers=max(1, args.terminology_workers),
    )
    print(f"Wrote {len(selected)} source rows and {len(selected) * len(languages)} pairs.")
    print(f"Manifest: {manifest_path}")


def load_rows_by_language(source_csv: Path) -> dict[str, dict[str, dict[str, str]]]:
    rows_by_language: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
    with source_csv.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            language_code = normalize_raw_language_code(row.get("language", ""))
            publication_number = row.get("publication_number", "")
            if language_code and publication_number:
                rows_by_language[language_code][publication_number] = row
    return rows_by_language


def normalize_raw_language_code(language: str) -> str:
    key = language.strip().lower()
    if key in {"en", "eng", "english"}:
        return "en"
    try:
        return normalize_language_code(key)
    except ValueError:
        return ""


def select_publications(
    rows_by_language: dict[str, dict[str, dict[str, str]]],
    languages: list[str],
    limit: int,
    text_field: str,
    min_input_tokens: int,
    max_input_tokens: int,
) -> list[dict[str, dict[str, str]]]:
    selected = []
    source_rows = rows_by_language.get("en", {})
    for publication_number in sorted(source_rows):
        if any(
            publication_number not in rows_by_language.get(language, {})
            for language in languages
        ):
            continue
        source_text = normalize_text(source_rows[publication_number].get(text_field, ""))
        token_count = approximate_token_count(source_text)
        if not source_text or token_count < min_input_tokens or token_count > max_input_tokens:
            continue
        selected.append(
            {
                "en": source_rows[publication_number],
                **{
                    language: rows_by_language[language][publication_number]
                    for language in languages
                },
            }
        )
        if len(selected) >= limit:
            break
    return selected


def write_language_csvs(
    output_dir: Path,
    selected: list[dict[str, dict[str, str]]],
    languages: list[str],
) -> None:
    for language in ["en", *languages]:
        rows = [selection[language] for selection in selected]
        if not rows:
            continue
        fieldnames = sorted({field for row in rows for field in row})
        with (output_dir / f"{language}.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)


def build_generator(args: argparse.Namespace) -> DatasetTerminologyGenerator | None:
    if not (
        args.extract_terminology
        or args.iate_terminology
        or args.wikidata_terminology
        or args.refine_terminology
    ):
        return None
    settings = load_settings()
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is required to generate dataset terminology.")
    return DatasetTerminologyGenerator(
        client=OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            timeout=args.openai_timeout,
        ),
        model=args.terminology_model,
        max_terms=args.terminology_max_terms,
        use_iate=args.iate_terminology,
        use_wikidata=args.wikidata_terminology,
        refine_terms=args.refine_terminology,
        confidence_threshold=args.terminology_confidence_threshold,
        cache_path=args.terminology_cache,
    )


def write_manifest(
    manifest_path: Path,
    selected: list[dict[str, dict[str, str]]],
    languages: list[str],
    text_field: str,
    generator: DatasetTerminologyGenerator | None,
    terminology_workers: int = 1,
) -> None:
    manifest_rows = [
        build_manifest_row(
            source_row=selection["en"],
            target_row=selection[language],
            language=language,
            text_field=text_field,
        )
        for selection in selected
        for language in languages
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
    return {
        "source_id": source_row.get("publication_number"),
        "target_language": LANGUAGE_NAMES[language],
        "target_language_code": language,
        "source_row_id": source_row.get("id"),
        "target_row_id": target_row.get("id"),
        "publication_number": source_row.get("publication_number"),
        "country_code": source_row.get("country_code"),
        "publication_date": source_row.get("publication_date"),
        "approx_source_tokens": approximate_token_count(source_text),
        "text_field": text_field,
        "selection": "requires_en_targets_context_token_window",
        "ipc_codes": source_row.get("ipc_codes"),
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
