from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from openai import OpenAI

from chem_machine_translation.config import DEFAULT_MODEL, load_settings
from chem_machine_translation.data.google_patents import LANGUAGE_NAMES
from chem_machine_translation.data.terminology import DatasetTerminologyGenerator
from chem_machine_translation.utils.text import approximate_token_count, normalize_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a Google Patents evaluation subset.")
    parser.add_argument("--source-dir", type=Path, default=Path("data/preprocessed"))
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("examples/google_patents_eval_subset_300"),
    )
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument(
        "--language",
        action="append",
        dest="languages",
        choices=sorted(LANGUAGE_NAMES),
    )
    parser.add_argument("--min-input-tokens", type=int, default=128)
    parser.add_argument("--max-input-tokens", type=int, default=384)
    parser.add_argument("--text-field", default="context", choices=["context", "abstract", "title"])
    parser.add_argument("--extract-terminology", action="store_true")
    parser.add_argument("--terminology-model", default=DEFAULT_MODEL)
    parser.add_argument("--terminology-max-terms", type=int, default=20)
    parser.add_argument("--iate-terminology", action="store_true")
    parser.add_argument("--wikidata-terminology", action="store_true")
    parser.add_argument("--refine-terminology", action="store_true")
    parser.add_argument("--terminology-confidence-threshold", type=float, default=0.85)
    parser.add_argument("--terminology-cache", type=Path, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    languages = args.languages or ["fr", "de", "es", "pt", "nl", "zh"]
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
    generator = build_generator(args)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_language_csvs(args.output_dir, selected, languages)
    pair_count = sum(len(v) for v in selected.values())
    manifest_path = args.output_dir / f"google-patents-subset-{pair_count}-manifest.jsonl"
    write_manifest(
        manifest_path=manifest_path,
        selected=selected,
        languages=languages,
        text_field=args.text_field,
        generator=generator,
    )
    print(f"Wrote {pair_count} source-target pairs.")
    print(f"Manifest: {manifest_path}")


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
        or args.refine_terminology
    ):
        return None
    settings = load_settings()
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is required to generate dataset terminology.")
    return DatasetTerminologyGenerator(
        client=OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url),
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
    selected: dict[str, list[tuple[dict[str, str], dict[str, str]]]],
    languages: list[str],
    text_field: str,
    generator: DatasetTerminologyGenerator | None,
) -> None:
    with manifest_path.open("w", encoding="utf-8") as handle:
        for language in languages:
            for source_row, target_row in selected[language]:
                source_text = normalize_text(source_row.get(text_field, ""))
                target_text = normalize_text(target_row.get(text_field, ""))
                publication_number = source_row.get("publication_number")
                row = {
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
                    "selection": "requires_source_and_target_text_token_window",
                }
                if generator:
                    row["terminology"] = [
                        term.to_json()
                        for term in generator.generate(
                            source_text=source_text,
                            target_language=LANGUAGE_NAMES[language],
                            reference_text=target_text,
                        )
                    ]
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
