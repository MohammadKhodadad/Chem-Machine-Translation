from __future__ import annotations

import json
from dataclasses import dataclass
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
