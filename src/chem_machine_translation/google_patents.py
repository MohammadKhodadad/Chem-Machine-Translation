from __future__ import annotations

import csv
from collections.abc import Iterator
from pathlib import Path

from chem_machine_translation.schemas import Document
from chem_machine_translation.text import approximate_token_count, normalize_text

LANGUAGE_CODES = {
    "chinese": "zh",
    "french": "fr",
    "german": "de",
    "portuguese": "pt",
    "spanish": "es",
    "zh": "zh",
    "fr": "fr",
    "de": "de",
    "pt": "pt",
    "es": "es",
}

LANGUAGE_NAMES = {
    "zh": "Chinese",
    "fr": "French",
    "de": "German",
    "pt": "Portuguese",
    "es": "Spanish",
}


def normalize_language_code(language: str) -> str:
    key = language.strip().lower()
    if key not in LANGUAGE_CODES:
        allowed = ", ".join(sorted(LANGUAGE_CODES))
        raise ValueError(f"Unsupported Google Patents language '{language}'. Use one of: {allowed}")
    return LANGUAGE_CODES[key]


def load_preprocessed_patents_by_publication(
    data_dir: Path,
    language: str,
) -> dict[str, dict[str, str]]:
    language_code = normalize_language_code(language) if language != "en" else "en"
    csv_path = data_dir / f"{language_code}.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"Google Patents CSV not found: {csv_path}")

    rows: dict[str, dict[str, str]] = {}
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            publication_number = row.get("publication_number")
            if publication_number:
                rows[publication_number] = row

    return rows


def iter_google_patent_translation_documents(
    data_dir: Path = Path("data/preprocessed"),
    target_language: str = "French",
    limit: int = 10,
    min_input_tokens: int = 192,
    max_input_tokens: int = 256,
    text_field: str = "context",
) -> Iterator[Document]:
    target_language_code = normalize_language_code(target_language)
    source_rows = load_preprocessed_patents_by_publication(data_dir, "en")
    target_rows = load_preprocessed_patents_by_publication(data_dir, target_language_code)
    target_language_name = LANGUAGE_NAMES[target_language_code]
    yielded = 0

    for publication_number in sorted(source_rows):
        target_row = target_rows.get(publication_number)
        if not target_row:
            continue

        source_text = normalize_text(source_rows[publication_number].get(text_field, ""))
        target_text = normalize_text(target_row.get(text_field, ""))
        token_count = approximate_token_count(source_text)
        if (
            not source_text
            or not target_text
            or token_count < min_input_tokens
            or token_count > max_input_tokens
        ):
            continue

        yield Document(
            dataset="google_patents",
            source_id=publication_number,
            text=source_text,
            ground_truth=target_text,
            metadata={
                "target_language": target_language_name,
                "target_language_code": target_language_code,
                "source_language": "English",
                "source_row_id": source_rows[publication_number].get("id"),
                "target_row_id": target_row.get("id"),
                "publication_number": publication_number,
                "country_code": source_rows[publication_number].get("country_code"),
                "publication_date": source_rows[publication_number].get("publication_date"),
                "text_field": text_field,
            },
        )
        yielded += 1
        if yielded >= limit:
            break
