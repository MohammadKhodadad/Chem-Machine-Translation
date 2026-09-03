from __future__ import annotations

import csv
import json
import os
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

IATE_API_ENDPOINT = "https://iate.europa.eu/em-api/entries/_search"
USER_AGENT = "chem-machine-translation/0.1 (chemistry terminology lookup)"

LANGUAGE_CODES = {
    "bulgarian": "bg",
    "bg": "bg",
    "chinese": "zh",
    "zh": "zh",
    "croatian": "hr",
    "hr": "hr",
    "czech": "cs",
    "cs": "cs",
    "danish": "da",
    "da": "da",
    "dutch": "nl",
    "nl": "nl",
    "english": "en",
    "en": "en",
    "estonian": "et",
    "et": "et",
    "finnish": "fi",
    "fi": "fi",
    "french": "fr",
    "fr": "fr",
    "german": "de",
    "de": "de",
    "greek": "el",
    "el": "el",
    "hungarian": "hu",
    "hu": "hu",
    "irish": "ga",
    "ga": "ga",
    "italian": "it",
    "it": "it",
    "latvian": "lv",
    "lv": "lv",
    "lithuanian": "lt",
    "lt": "lt",
    "polish": "pl",
    "pl": "pl",
    "portuguese": "pt",
    "pt": "pt",
    "romanian": "ro",
    "ro": "ro",
    "slovak": "sk",
    "sk": "sk",
    "slovenian": "sl",
    "sl": "sl",
    "spanish": "es",
    "es": "es",
    "swedish": "sv",
    "sv": "sv",
}


@dataclass(frozen=True)
class IATETermTranslation:
    source_term: str
    target_label: str
    entry_id: str = ""
    reliability: str = ""


class IATEClient:
    """Looks up candidate target-language terms through the IATE public API."""

    def __init__(self, endpoint: str = IATE_API_ENDPOINT, timeout_seconds: float = 5.0) -> None:
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds
        self._cache: dict[tuple[str, str, str], IATETermTranslation | None] = {}

    def translate_term(
        self,
        source_term: str,
        source_language_code: str,
        target_language_code: str,
    ) -> IATETermTranslation | None:
        cache_key = (source_term.lower(), source_language_code, target_language_code)
        if cache_key in self._cache:
            return self._cache[cache_key]

        payload = self._search(source_term, source_language_code, target_language_code)
        translation = parse_iate_translation(
            payload=payload,
            source_term=source_term,
            target_language_code=target_language_code,
        )
        self._cache[cache_key] = translation
        return translation

    def _search(
        self,
        source_term: str,
        source_language_code: str,
        target_language_code: str,
    ) -> dict[str, Any]:
        payload = {
            "query": source_term,
            "source": source_language_code,
            "targets": [target_language_code],
            "search_in_fields": [0],
            "search_in_term_types": [0, 1, 2, 3, 4, 5],
            "query_operator": 3,
        }
        request = Request(
            f"{self.endpoint}?expand=true&offset=0&limit=5",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "User-Agent": USER_AGENT,
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
            return {}


class LocalIATEClient:
    """Looks up IATE terms from a local CSV export.

    The official export column names can vary by export mode. This client accepts common variants
    for entry ID, language, and term columns, then groups terms by IATE entry.
    """

    def __init__(
        self,
        path: Path | str = Path("data/iate"),
        *,
        auto_build_index: bool = True,
        build_wait_seconds: float = 600.0,
    ) -> None:
        self.path = Path(path)
        self.auto_build_index = auto_build_index
        self.build_wait_seconds = build_wait_seconds
        self._loaded = False
        self._entries: dict[str, dict[str, list[str]]] = {}
        self._term_index: dict[tuple[str, str], list[str]] = {}
        self._cache: dict[tuple[str, str, str], IATETermTranslation | None] = {}

    def translate_term(
        self,
        source_term: str,
        source_language_code: str,
        target_language_code: str,
    ) -> IATETermTranslation | None:
        sqlite_path = self._sqlite_path()
        if sqlite_path is None and self.auto_build_index:
            sqlite_path = self._build_sqlite_index_if_possible()
        if sqlite_path is not None:
            return self._lookup_sqlite(source_term, source_language_code, target_language_code)

        self._ensure_loaded()
        cache_key = (
            normalize_iate_term(source_term),
            source_language_code,
            target_language_code,
        )
        if cache_key in self._cache:
            return self._cache[cache_key]

        translation = self._lookup(source_term, source_language_code, target_language_code)
        self._cache[cache_key] = translation
        return translation

    def _lookup_sqlite(
        self,
        source_term: str,
        source_language_code: str,
        target_language_code: str,
    ) -> IATETermTranslation | None:
        source_key = normalize_iate_term(source_term)
        if not source_key:
            return None
        cache_key = (source_key, source_language_code, target_language_code)
        if cache_key in self._cache:
            return self._cache[cache_key]

        sqlite_path = self._sqlite_path()
        if sqlite_path is None:
            return None
        try:
            with sqlite3.connect(sqlite_path) as connection:
                if source_language_code == target_language_code:
                    exact_row = connection.execute(
                        """
                        SELECT entry_id, term
                        FROM terms
                        WHERE language_code = ? AND normalized_term = ?
                        ORDER BY rowid
                        LIMIT 1
                        """,
                        (target_language_code, source_key),
                    ).fetchone()
                    if exact_row:
                        translation = IATETermTranslation(
                            source_term=source_term,
                            target_label=str(exact_row[1]),
                            entry_id=str(exact_row[0]),
                        )
                        self._cache[cache_key] = translation
                        return translation

                entry_rows = connection.execute(
                    """
                    SELECT entry_id
                    FROM terms
                    WHERE language_code = ? AND normalized_term = ?
                    LIMIT 20
                    """,
                    (source_language_code, source_key),
                ).fetchall()
                for (entry_id,) in entry_rows:
                    target_row = connection.execute(
                        """
                        SELECT term
                        FROM terms
                        WHERE entry_id = ? AND language_code = ?
                        ORDER BY rowid
                        LIMIT 1
                        """,
                        (entry_id, target_language_code),
                    ).fetchone()
                    if target_row:
                        translation = IATETermTranslation(
                            source_term=source_term,
                            target_label=str(target_row[0]),
                            entry_id=str(entry_id),
                        )
                        self._cache[cache_key] = translation
                        return translation
        except sqlite3.Error:
            pass
        self._cache[cache_key] = None
        return None

    def _sqlite_path(self) -> Path | None:
        if self.path.is_file() and self.path.suffix.lower() in {".sqlite", ".sqlite3", ".db"}:
            return self.path
        if not self.path.is_dir():
            return None
        for pattern in ("*.sqlite", "*.sqlite3", "*.db"):
            matches = sorted(self.path.glob(pattern))
            if matches:
                return matches[0]
        return None

    def _build_sqlite_index_if_possible(self) -> Path | None:
        csv_path = self._index_source_csv_path()
        output_path = self._default_sqlite_output_path(csv_path)
        if csv_path is None or output_path is None:
            return None
        if output_path.exists():
            return output_path

        lock_path = output_path.with_suffix(output_path.suffix + ".lock")
        lock_handle = self._try_acquire_build_lock(lock_path)
        if lock_handle is None:
            return self._wait_for_sqlite_index(output_path, lock_path)

        try:
            from chem_machine_translation.translation.iate_index import build_local_iate_index

            print(f"Building local IATE index: {output_path}", flush=True)
            build_local_iate_index(input_path=csv_path, output_path=output_path)
            return output_path if output_path.exists() else None
        except Exception:
            return None
        finally:
            os.close(lock_handle)
            try:
                lock_path.unlink()
            except OSError:
                pass

    def _index_source_csv_path(self) -> Path | None:
        if self.path.is_file() and self.path.suffix.lower() == ".csv":
            return self.path
        if not self.path.is_dir():
            return None
        matches = sorted(self.path.glob("*.csv"))
        return matches[0] if matches else None

    def _default_sqlite_output_path(self, csv_path: Path | None) -> Path | None:
        if csv_path is None:
            return None
        if self.path.is_dir():
            return self.path / "iate.sqlite"
        return csv_path.with_suffix(".sqlite")

    def _try_acquire_build_lock(self, lock_path: Path) -> int | None:
        try:
            lock_path.parent.mkdir(parents=True, exist_ok=True)
            return os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except OSError:
            return None

    def _wait_for_sqlite_index(self, output_path: Path, lock_path: Path) -> Path | None:
        deadline = time.monotonic() + self.build_wait_seconds
        while time.monotonic() < deadline:
            if output_path.exists():
                return output_path
            if not lock_path.exists():
                return output_path if output_path.exists() else None
            time.sleep(1.0)
        return output_path if output_path.exists() else None

    def _lookup(
        self,
        source_term: str,
        source_language_code: str,
        target_language_code: str,
    ) -> IATETermTranslation | None:
        source_key = normalize_iate_term(source_term)
        if not source_key:
            return None
        entry_ids = self._term_index.get((source_language_code, source_key), [])
        if not entry_ids and source_language_code == target_language_code:
            entry_ids = self._term_index.get((target_language_code, source_key), [])
        for entry_id in entry_ids:
            target_terms = self._entries.get(entry_id, {}).get(target_language_code, [])
            if source_language_code == target_language_code:
                for target_term in target_terms:
                    if normalize_iate_term(target_term) == source_key:
                        return IATETermTranslation(
                            source_term=source_term,
                            target_label=target_term,
                            entry_id=entry_id,
                        )
            if target_terms:
                return IATETermTranslation(
                    source_term=source_term,
                    target_label=target_terms[0],
                    entry_id=entry_id,
                )
        return None

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        for csv_path in self._csv_paths():
            self._load_csv(csv_path)
        self._loaded = True

    def _csv_paths(self) -> list[Path]:
        if self.path.is_file():
            return [self.path]
        if not self.path.exists():
            return []
        return sorted(self.path.glob("*.csv"))

    def _load_csv(self, csv_path: Path) -> None:
        try:
            with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
                sample = handle.read(4096)
                handle.seek(0)
                try:
                    dialect = csv.Sniffer().sniff(sample) if sample.strip() else csv.excel
                except csv.Error:
                    dialect = csv.excel
                reader = csv.DictReader(handle, dialect=dialect)
                for index, row in enumerate(reader, start=1):
                    self._add_csv_row(row, fallback_entry_id=f"{csv_path.stem}:{index}")
        except (csv.Error, OSError, UnicodeError):
            return

    def _add_csv_row(self, row: dict[str, str], *, fallback_entry_id: str) -> None:
        normalized = {normalize_iate_column(key): value for key, value in row.items()}
        term = first_iate_csv_value(
            normalized,
            "term",
            "termvalue",
            "termtext",
            "label",
            "tterm",
        )
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
        if not term or not language_code:
            return
        self._entries.setdefault(entry_id, {}).setdefault(language_code, [])
        if term not in self._entries[entry_id][language_code]:
            self._entries[entry_id][language_code].append(term)
        self._term_index.setdefault((language_code, normalize_iate_term(term)), [])
        if entry_id not in self._term_index[(language_code, normalize_iate_term(term))]:
            self._term_index[(language_code, normalize_iate_term(term))].append(entry_id)


def iate_language_code(language: str) -> str | None:
    return LANGUAGE_CODES.get(language.strip().lower())


def parse_iate_translation(
    payload: dict[str, Any],
    source_term: str,
    target_language_code: str,
) -> IATETermTranslation | None:
    for item in payload.get("items", []):
        if not isinstance(item, dict):
            continue
        entry_id = str(item.get("code", ""))
        target_language = item.get("language", {}).get(target_language_code, {})
        if not isinstance(target_language, dict):
            continue
        term = _first_term_value(target_language.get("term_entries", []))
        if not term:
            continue
        return IATETermTranslation(
            source_term=source_term,
            target_label=term,
            entry_id=entry_id,
        )

    return None


def _first_term_value(term_entries: Any) -> str:
    if not isinstance(term_entries, list):
        return ""
    for term_entry in term_entries:
        if not isinstance(term_entry, dict):
            continue
        term_value = str(term_entry.get("term_value", "")).strip()
        if term_value:
            return term_value
    return ""


def normalize_iate_column(column: str | None) -> str:
    if column is None:
        return ""
    return "".join(character for character in column.lower() if character.isalnum())


def normalize_iate_term(term: str) -> str:
    return " ".join(term.casefold().split())


def first_iate_csv_value(row: dict[str, str], *keys: str) -> str:
    for key in keys:
        value = str(row.get(key) or "").strip()
        if value:
            return value
    return ""
