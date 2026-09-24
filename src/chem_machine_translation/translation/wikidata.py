from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

WIKIDATA_API_ENDPOINT = "https://www.wikidata.org/w/api.php"
USER_AGENT = "chem-machine-translation/0.1 (chemistry terminology lookup)"

LANGUAGE_CODES = {
    "chinese": "zh",
    "zh": "zh",
    "english": "en",
    "en": "en",
    "french": "fr",
    "fr": "fr",
    "german": "de",
    "de": "de",
    "dutch": "nl",
    "nl": "nl",
    "portuguese": "pt",
    "pt": "pt",
    "spanish": "es",
    "es": "es",
}


@dataclass(frozen=True)
class WikidataTermTranslation:
    source_term: str
    target_label: str
    entity_id: str
    source_label: str = ""
    description: str = ""


@dataclass(frozen=True)
class WikidataEntityMetadata:
    entity_id: str
    description: str = ""
    instance_of: tuple[str, ...] = ()
    subclass_of: tuple[str, ...] = ()


class WikidataClient:
    """Looks up candidate target-language labels for terms through Wikidata."""

    def __init__(self, endpoint: str = WIKIDATA_API_ENDPOINT, timeout_seconds: float = 5.0) -> None:
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds
        self._cache: dict[tuple[str, str, str], WikidataTermTranslation | None] = {}
        self._synonym_cache: dict[tuple[str, str], list[str]] = {}
        self._metadata_cache: dict[tuple[str, str], WikidataEntityMetadata | None] = {}

    def translate_term(
        self,
        source_term: str,
        source_language_code: str,
        target_language_code: str,
    ) -> WikidataTermTranslation | None:
        cache_key = (source_term.lower(), source_language_code, target_language_code)
        if cache_key in self._cache:
            return self._cache[cache_key]

        entity_id = self._find_entity_id(source_term, source_language_code)
        if not entity_id:
            self._cache[cache_key] = None
            return None

        translation = self._get_entity_label(
            source_term=source_term,
            entity_id=entity_id,
            source_language_code=source_language_code,
            target_language_code=target_language_code,
        )
        self._cache[cache_key] = translation
        return translation

    def lookup_synonyms(self, term: str, language_code: str) -> list[str]:
        cache_key = (_normalize_label(term), language_code)
        if cache_key in self._synonym_cache:
            return self._synonym_cache[cache_key]

        entity_id = self._find_entity_id(term, language_code)
        if not entity_id:
            self._synonym_cache[cache_key] = []
            return []
        entity = self._get_entity(entity_id, {language_code})
        synonyms = _same_language_entity_terms(entity, term, language_code)
        self._synonym_cache[cache_key] = synonyms
        return synonyms

    def lookup_metadata(self, term: str, language_code: str) -> WikidataEntityMetadata | None:
        cache_key = (_normalize_label(term), language_code)
        if cache_key in self._metadata_cache:
            return self._metadata_cache[cache_key]
        entity_id = self._find_entity_id(term, language_code)
        if not entity_id:
            self._metadata_cache[cache_key] = None
            return None
        entity = self._get_entity(entity_id, {language_code, "en"}, include_claims=True)
        if not _same_language_entity_terms(entity, term, language_code):
            self._metadata_cache[cache_key] = None
            return None
        claims = entity.get("claims", {})
        instance_ids = _claim_entity_ids(claims.get("P31", []))
        subclass_ids = _claim_entity_ids(claims.get("P279", []))
        class_labels = self._get_entity_labels(set(instance_ids) | set(subclass_ids), language_code)
        metadata = WikidataEntityMetadata(
            entity_id=entity_id,
            description=str(entity.get("descriptions", {}).get("en", {}).get("value", "")),
            instance_of=tuple(class_labels.get(item_id, item_id) for item_id in instance_ids),
            subclass_of=tuple(class_labels.get(item_id, item_id) for item_id in subclass_ids),
        )
        self._metadata_cache[cache_key] = metadata
        return metadata

    def _find_entity_id(self, source_term: str, source_language_code: str) -> str | None:
        payload = self._get_json(
            {
                "action": "wbsearchentities",
                "format": "json",
                "language": source_language_code,
                "uselang": "en",
                "search": source_term,
                "limit": "1",
            }
        )
        if not payload:
            return None
        matches = payload.get("search", [])
        if not matches:
            return None
        entity_id = matches[0].get("id")
        return str(entity_id) if entity_id else None

    def _get_entity_label(
        self,
        source_term: str,
        entity_id: str,
        source_language_code: str,
        target_language_code: str,
    ) -> WikidataTermTranslation | None:
        entity = self._get_entity(entity_id, {source_language_code, target_language_code, "en"})
        target_label = _get_label_or_alias(entity, target_language_code)
        if not target_label:
            return None

        source_label = _get_label_or_alias(entity, source_language_code)
        if not _labels_match(source_term, source_label):
            return None
        description = entity.get("descriptions", {}).get("en", {}).get("value", "")
        return WikidataTermTranslation(
            source_term=source_term,
            target_label=target_label,
            entity_id=entity_id,
            source_label=source_label,
            description=description,
        )

    def _get_entity(
        self,
        entity_id: str,
        languages: set[str],
        *,
        include_claims: bool = False,
    ) -> dict[str, Any]:
        payload = self._get_json(
            {
                "action": "wbgetentities",
                "format": "json",
                "ids": entity_id,
                "props": "labels|aliases|descriptions|claims" if include_claims else "labels|aliases|descriptions",
                "languages": "|".join(sorted(languages)),
                "languagefallback": "1",
            }
        )
        entity = payload.get("entities", {}).get(entity_id, {})
        return entity if isinstance(entity, dict) else {}

    def _get_entity_labels(self, entity_ids: set[str], language_code: str) -> dict[str, str]:
        if not entity_ids:
            return {}
        payload = self._get_json(
            {
                "action": "wbgetentities",
                "format": "json",
                "ids": "|".join(sorted(entity_ids)),
                "props": "labels",
                "languages": f"{language_code}|en",
                "languagefallback": "1",
            }
        )
        return {
            entity_id: _get_label_or_alias(entity, language_code) or entity_id
            for entity_id, entity in payload.get("entities", {}).items()
            if isinstance(entity, dict)
        }

    def _get_json(self, params: dict[str, str]) -> dict[str, Any]:
        url = f"{self.endpoint}?{urlencode(params)}"
        request = Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
            return {}


def wikidata_language_code(language: str) -> str | None:
    return LANGUAGE_CODES.get(language.strip().lower())


def _get_label_or_alias(entity: dict[str, Any], language_code: str) -> str:
    label = entity.get("labels", {}).get(language_code, {}).get("value")
    if label:
        return str(label)

    aliases = entity.get("aliases", {}).get(language_code, [])
    if aliases:
        alias = aliases[0].get("value")
        if alias:
            return str(alias)

    return ""


def _same_language_entity_terms(
    entity: dict[str, Any],
    queried_term: str,
    language_code: str,
) -> list[str]:
    label = entity.get("labels", {}).get(language_code, {}).get("value")
    aliases = entity.get("aliases", {}).get(language_code, [])
    terms = [str(label).strip()] if label else []
    terms.extend(
        str(alias.get("value", "")).strip()
        for alias in aliases
        if isinstance(alias, dict) and str(alias.get("value", "")).strip()
    )
    if _normalize_label(queried_term) not in {_normalize_label(term) for term in terms}:
        return []
    return list(dict.fromkeys(terms))


def _labels_match(source_term: str, source_label: str) -> bool:
    return _normalize_label(source_term) == _normalize_label(source_label)


def _normalize_label(label: str) -> str:
    return " ".join(label.casefold().split())


def _claim_entity_ids(claims: list[dict[str, Any]]) -> tuple[str, ...]:
    entity_ids = []
    for claim in claims:
        value = claim.get("mainsnak", {}).get("datavalue", {}).get("value", {})
        entity_id = value.get("id") if isinstance(value, dict) else None
        if entity_id:
            entity_ids.append(str(entity_id))
    return tuple(dict.fromkeys(entity_ids))
