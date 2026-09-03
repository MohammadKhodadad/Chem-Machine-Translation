from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

from chem_machine_translation.translation.iate import (
    first_iate_csv_value,
    iate_language_code,
    normalize_iate_column,
    normalize_iate_term,
)

BATCH_SIZE = 25_000


def build_local_iate_index(*, input_path: Path, output_path: Path) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()

    with sqlite3.connect(output_path) as connection:
        prepare_database(connection)
        inserted = load_csv_terms(connection, input_path)
        create_indexes(connection)
        connection.execute(
            "INSERT INTO metadata(key, value) VALUES (?, ?)",
            ("source_csv", str(input_path)),
        )
        connection.execute(
            "INSERT INTO metadata(key, value) VALUES (?, ?)",
            ("term_rows", str(inserted)),
        )
        connection.commit()
    return inserted


def prepare_database(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        PRAGMA journal_mode = OFF;
        PRAGMA synchronous = OFF;
        PRAGMA temp_store = MEMORY;

        CREATE TABLE terms (
            entry_id TEXT NOT NULL,
            language_code TEXT NOT NULL,
            normalized_term TEXT NOT NULL,
            term TEXT NOT NULL
        );

        CREATE TABLE metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        """
    )


def load_csv_terms(connection: sqlite3.Connection, input_path: Path) -> int:
    inserted = 0
    batch: list[tuple[str, str, str, str]] = []
    with input_path.open("r", encoding="utf-8-sig", newline="") as handle:
        sample = handle.read(4096)
        handle.seek(0)
        dialect = sniff_dialect(sample)
        reader = csv.DictReader(handle, dialect=dialect)
        for index, row in enumerate(reader, start=1):
            record = iate_record_from_csv_row(row, fallback_entry_id=f"{input_path.stem}:{index}")
            if record is None:
                continue
            batch.append(record)
            if len(batch) >= BATCH_SIZE:
                inserted += insert_batch(connection, batch)
                batch.clear()
        if batch:
            inserted += insert_batch(connection, batch)
    return inserted


def sniff_dialect(sample: str) -> csv.Dialect:
    try:
        return csv.Sniffer().sniff(sample) if sample.strip() else csv.excel
    except csv.Error:
        return csv.excel


def iate_record_from_csv_row(
    row: dict[str, str],
    *,
    fallback_entry_id: str,
) -> tuple[str, str, str, str] | None:
    normalized = {normalize_iate_column(key): value for key, value in row.items()}
    term = first_iate_csv_value(normalized, "term", "termvalue", "termtext", "label", "tterm")
    language_code = first_iate_csv_value(
        normalized,
        "languagecode",
        "language",
        "lang",
        "isocode",
        "lcode",
    ).lower()
    entry_id = first_iate_csv_value(
        normalized,
        "entryid",
        "entry",
        "id",
        "code",
        "iateid",
        "eid",
    ) or fallback_entry_id
    language_code = iate_language_code(language_code) or language_code
    normalized_term = normalize_iate_term(term)
    if not term or not language_code or not normalized_term:
        return None
    return entry_id, language_code, normalized_term, term


def insert_batch(
    connection: sqlite3.Connection,
    batch: list[tuple[str, str, str, str]],
) -> int:
    connection.executemany(
        """
        INSERT INTO terms(entry_id, language_code, normalized_term, term)
        VALUES (?, ?, ?, ?)
        """,
        batch,
    )
    return len(batch)


def create_indexes(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE INDEX idx_terms_lookup ON terms(language_code, normalized_term);
        CREATE INDEX idx_terms_entry_language ON terms(entry_id, language_code);
        """
    )
