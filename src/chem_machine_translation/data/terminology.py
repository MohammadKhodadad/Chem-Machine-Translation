from __future__ import annotations

import hashlib
import json
import re
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from chem_machine_translation.translation.iate import IATEClient, iate_language_code
from chem_machine_translation.translation.wikidata import WikidataClient, wikidata_language_code

_FORMULA_OR_IDENTIFIER_RE = re.compile(
    r"^(?:[A-Z][a-z]?\d*)+$|^[A-Z]{1,6}-?\d[\w.-]*$|^\d+(?:[.,]\d+)?\s?[A-Za-z/%]+$"
)
_COMPACT_NUMERIC_UNIT_RE = re.compile(
    r"^\d+(?:[.,]\d+)?(?:\s*(?:-|to|–|—|à)\s*\d+(?:[.,]\d+)?)?\s*"
    r"(?:%|°C|K|ppm|ppb|mol%|wt%|mg|g|kg|mL|L|cm2|cm3|mm|cm|m|nm|µm|um)$",
    re.IGNORECASE,
)
_SEQUENCE_IDENTIFIER_RE = re.compile(
    r"^(?:SEQ\s+ID\s+NO:\s*\d+|CAS\s+RN\s*[:\s]?\d[\d-]+)$",
    re.IGNORECASE,
)
_CHEMICAL_FORMULA_SCAN_RE = re.compile(r"\b(?:[A-Z][a-z]?\d*){2,}\b")
_NUMERIC_UNIT_SCAN_RE = re.compile(
    r"\b\d+(?:[.,]\d+)?(?:\s*(?:-|to|à|–|—)\s*\d+(?:[.,]\d+)?)?\s*"
    r"(?:%|°C|K|ppm|ppb|mol%|wt%|mg|g|kg|mL|L|cm2|cm3|mm|cm|m|nm|µm|um)\b",
    re.IGNORECASE,
)
_CHEMICAL_PHRASE_SCAN_RE = re.compile(
    r"\b[\wα-ωΑ-Ωµμ°-]+(?:[- ][\wα-ωΑ-Ωµμ°-]+){0,5}\s+"
    r"(?:acid|acide|oxide|oxyde|chloride|chlorure|sulfate|sulphate|phosphate|"
    r"polymer|polym[eè]re|protein|prot[eé]ine|enzyme|catalyst|catalyseur|"
    r"solvent|solvant|ester|amide|alcohol|alcool|emulsion|[eé]mulsion|"
    r"surfactant|tensioactif|compound|compos[eé])s?\b",
    re.IGNORECASE,
)
_CHEMICAL_PREFIX_SCAN_RE = re.compile(
    r"\b(?:acid|acide|oxide|oxyde|chloride|chlorure|sulfate|sulphate|phosphate|"
    r"polymer|polym[eè]re|protein|prot[eé]ine|enzyme|catalyst|catalyseur|"
    r"solvent|solvant|ester|amide|alcohol|alcool|emulsion|[eé]mulsion|"
    r"surfactant|tensioactif|compound|compos[eé])s?\s+"
    r"(?:de|d'|of)?\s*[\wα-ωΑ-Ωµμ-]+(?:[- ][\wα-ωΑ-Ωµμ-]+){0,2}\b",
    re.IGNORECASE,
)
_PUBCHEM_ENDPOINT = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name"
_USER_AGENT = "chem-machine-translation/0.1 (benchmark terminology lookup)"
_TERMINOLOGY_PIPELINE_VERSION = "target-llm-candidate-v1"
_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)

TARGET_CANDIDATE_EXTRACTOR_SYSTEM_PROMPT = """You extract terminology candidates from target
reference translations for chemistry and patent machine-translation benchmarks.

The text may be in any language. Return only exact spans that appear in the provided target text.
Do not translate, normalize, rewrite, explain, or invent terms.

Extract strict technical terminology candidates:
- chemical names, compounds, materials, formulas, reagents, solvents, polymers, proteins;
- domain-specific processes, methods, analytical terms, properties, hazards, identifiers;
- compact numeric/unit expressions when they carry technical meaning.

Avoid common prose, generic patent scaffolding, sentence fragments, whole clauses, and broad field
labels. Prefer the smallest target-text span that carries the technical meaning.

Return only valid JSON with this shape:
{
  "terms": [
    {
      "target_term": "exact target text span",
      "category": "chemical|material|process|method|unit|identifier|hazard|other",
      "confidence": 0.0,
      "reason": "short reason"
    }
  ]
}
"""

LEGAL_CANDIDATE_EXTRACTOR_SYSTEM_PROMPT = """You extract legal terminology candidates from
target/reference translations for legal machine-translation benchmarks.

The text may be in any language. Return only exact spans that appear in the provided target text.
Do not translate, normalize, rewrite, explain, or invent terms.

Extract strict legal or regulatory terminology candidates:
- legal instruments, procedures, institutions, rights, obligations, restrictions, sanctions;
- regulatory domains, administrative bodies, legal acts, committees, programmes, funds;
- multi-word noun phrases and named legal entities that would matter for translation quality.

Avoid common prose, dates, article numbers, names of people, whole clauses, generic single words,
and boilerplate unless the phrase is a recognized legal or institutional term.

Return only valid JSON with this shape:
{
  "terms": [
    {
      "target_term": "exact target text span",
      "category": "institution|legal_act|procedure|right|obligation|sanction|policy|other",
      "confidence": 0.0,
      "reason": "short reason"
    }
  ]
}
"""


@dataclass(frozen=True)
class DatasetTerminologyTerm:
    source_term: str = ""
    target_terms: tuple[str, ...] = ()
    reference_candidates: tuple[str, ...] = ()
    category: str = "other"
    source: str = "target_ner"
    term_group: str = "algorithmic"
    verified_by: tuple[str, ...] = ()
    confidence: float = 0.0
    decision: str = "keep_reference"
    reason: str = ""
    candidates: dict[str, list[str]] = field(default_factory=dict)

    def to_json(self) -> dict[str, Any]:
        return {
            "source_term": self.source_term,
            "target_terms": list(self.target_terms),
            "reference_candidates": list(self.reference_candidates),
            "category": self.category,
            "source": self.source,
            "term_group": self.term_group,
            "verified_by": list(self.verified_by),
            "confidence": self.confidence,
            "decision": self.decision,
            "reason": self.reason,
            "external_candidates": self.candidates,
            "candidates": self.candidates,
        }


class PubChemClient:
    """Checks whether a target-side term has a PubChem compound record."""

    def __init__(self, endpoint: str = _PUBCHEM_ENDPOINT, timeout_seconds: float = 5.0) -> None:
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds
        self._cache: dict[str, list[str]] = {}

    def lookup_synonyms(self, term: str) -> list[str]:
        key = term.casefold()
        if key in self._cache:
            return self._cache[key]

        request = Request(
            f"{self.endpoint}/{quote(term)}/synonyms/JSON",
            headers={"User-Agent": _USER_AGENT},
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
            self._cache[key] = []
            return []

        synonyms = []
        for item in payload.get("InformationList", {}).get("Information", []):
            raw_synonyms = item.get("Synonym", [])
            if isinstance(raw_synonyms, list):
                synonyms.extend(str(synonym).strip() for synonym in raw_synonyms if synonym)
        self._cache[key] = list(dict.fromkeys(synonyms[:20]))
        return self._cache[key]


class LLMTargetCandidateExtractor:
    """Uses an LLM only to propose exact target-side candidate spans."""

    def __init__(self, client: Any, model: str = "gpt-4.1-mini") -> None:
        self.client = client
        self.model = model

    def extract(
        self,
        text: str,
        target_language: str,
        max_terms: int,
    ) -> list[DatasetTerminologyTerm]:
        response = self.client.responses.create(
            model=self.model,
            temperature=0.0,
            input=[
                {"role": "system", "content": TARGET_CANDIDATE_EXTRACTOR_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Extract up to {max_terms} strict technical terminology candidates from "
                        f"this {target_language} target/reference text.\n\nTarget text:\n{text}"
                    ),
                },
            ],
        )
        return parse_llm_target_candidates(response.output_text, text)


class LLMLegalCandidateExtractor:
    """Uses an LLM only to propose exact target-side legal candidate spans."""

    def __init__(self, client: Any, model: str = "gpt-4.1-mini") -> None:
        self.client = client
        self.model = model

    def extract(
        self,
        text: str,
        target_language: str,
        max_terms: int,
    ) -> list[DatasetTerminologyTerm]:
        response = self.client.responses.create(
            model=self.model,
            temperature=0.0,
            input=[
                {"role": "system", "content": LEGAL_CANDIDATE_EXTRACTOR_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Extract up to {max_terms} strict legal terminology candidates from "
                        f"this {target_language} target/reference text.\n\nTarget text:\n{text}"
                    ),
                },
            ],
        )
        return parse_llm_legal_candidates(response.output_text, text)


class UNTERMClient:
    """Best-effort UNTERM search-page verifier.

    UNTERM does not provide a documented public API. This client fails closed: it only returns
    evidence when the public search page is reachable and does not report an empty result set.
    """

    def __init__(
        self,
        endpoint: str = "https://unterm.un.org/unterm2",
        timeout_seconds: float = 5.0,
    ) -> None:
        self.endpoint = endpoint.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self._cache: dict[tuple[str, str], bool] = {}

    def term_exists(self, term: str, language_code: str) -> bool:
        if language_code not in {"ar", "zh", "en", "fr", "ru", "es"}:
            return False
        cache_key = (normalize_term_key(term), language_code)
        if cache_key in self._cache:
            return self._cache[cache_key]
        payload = self._search(term, language_code)
        exists = bool(re.search(r"Results\s+1-\d+\s+of\s+[1-9]\d*", payload))
        self._cache[cache_key] = exists
        return exists

    def _search(self, term: str, language_code: str) -> str:
        url = f"{self.endpoint}/{language_code}/search?{urlencode({'searchTerm': term})}"
        request = Request(url, headers={"User-Agent": _USER_AGENT})
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                return response.read().decode("utf-8", errors="replace")
        except (HTTPError, URLError, TimeoutError):
            return ""


class TargetTerminologyExtractor:
    """Target-side terminology extractor using optional NER models plus regex fallback."""

    def extract(self, text: str, max_terms: int) -> list[DatasetTerminologyTerm]:
        candidates: list[DatasetTerminologyTerm] = []
        candidates.extend(extract_with_chemdataextractor(text))
        candidates.extend(extract_with_chemu_biobert(text))
        candidates.extend(extract_with_regexes(text))

        by_key: dict[str, DatasetTerminologyTerm] = {}
        for candidate in candidates:
            key = normalize_term_key(candidate.target_terms[0] if candidate.target_terms else "")
            if not key:
                continue
            existing = by_key.get(key)
            if existing is None or candidate.confidence > existing.confidence:
                by_key[key] = candidate

        terms = sorted(
            by_key.values(),
            key=lambda term: (term.confidence, len(term.target_terms[0])),
            reverse=True,
        )
        return terms[:max_terms]


class DatasetTerminologyGenerator:
    """Generates target-side terminology mappings for benchmark manifests."""

    def __init__(
        self,
        client: Any | None = None,
        model: str = "gpt-4.1-mini",
        max_terms: int = 20,
        use_llm: bool = False,
        use_iate: bool = False,
        use_wikidata: bool = False,
        use_pubchem: bool = False,
        cache_path: Path | None = None,
        iate_client: IATEClient | None = None,
        wikidata_client: WikidataClient | None = None,
        pubchem_client: PubChemClient | None = None,
        llm_extractor: LLMTargetCandidateExtractor | None = None,
        extractor: TargetTerminologyExtractor | None = None,
    ) -> None:
        self.model = model
        self.max_terms = max_terms
        self.use_llm = use_llm
        self.use_iate = use_iate
        self.use_wikidata = use_wikidata
        self.use_pubchem = use_pubchem
        self.cache_path = cache_path
        self.iate_client = iate_client or (IATEClient() if use_iate else None)
        self.wikidata_client = wikidata_client or (WikidataClient() if use_wikidata else None)
        self.pubchem_client = pubchem_client or (PubChemClient() if use_pubchem else None)
        self.llm_extractor = llm_extractor or (
            LLMTargetCandidateExtractor(client=client, model=model)
            if use_llm and client is not None
            else None
        )
        self.extractor = extractor or TargetTerminologyExtractor()
        self._cache = load_terminology_cache(cache_path)
        self._cache_lock = threading.Lock()

    def generate(
        self,
        source_text: str,
        target_language: str,
        reference_text: str = "",
        source_language: str = "English",
    ) -> list[DatasetTerminologyTerm]:
        del source_text, source_language
        cache_key = terminology_cache_key(
            reference_text=reference_text,
            target_language=target_language,
            model=self.model,
            max_terms=self.max_terms,
            use_llm=self.use_llm,
            use_iate=self.use_iate,
            use_wikidata=self.use_wikidata,
            use_pubchem=self.use_pubchem,
        )
        with self._cache_lock:
            cached_terms = self._cache.get(cache_key)
        if cached_terms is not None:
            return [dataset_term_from_json(term) for term in cached_terms]

        terms = []
        if self.llm_extractor:
            terms.extend(
                self.llm_extractor.extract(
                    text=reference_text,
                    target_language=target_language,
                    max_terms=self.max_terms,
                )
            )
        terms.extend(self.extractor.extract(reference_text, max_terms=self.max_terms))
        terms = deduplicate_terms(terms)[: self.max_terms]
        terms = [
            self.add_external_candidates(term=term, target_language=target_language)
            for term in terms
        ]
        terms = select_dataset_terms(terms, max_terms=self.max_terms)

        with self._cache_lock:
            if cache_key not in self._cache:
                self._cache[cache_key] = [term.to_json() for term in terms]
                append_terminology_cache(self.cache_path, cache_key, terms)
        return terms

    def add_external_candidates(
        self,
        term: DatasetTerminologyTerm,
        target_language: str = "",
        source_language: str = "",
    ) -> DatasetTerminologyTerm:
        del source_language
        target_term = term.target_terms[0] if term.target_terms else ""
        candidates: dict[str, list[str]] = {}
        source_parts = [term.source]

        if self.pubchem_client:
            synonyms = self.pubchem_client.lookup_synonyms(target_term)
            if synonyms:
                candidates["pubchem"] = synonyms
                source_parts.append("pubchem")

        if self.iate_client:
            language_code = iate_language_code(target_language)
            if language_code:
                translation = self.iate_client.translate_term(
                    source_term=target_term,
                    source_language_code=language_code,
                    target_language_code=language_code,
                )
                if translation:
                    candidates["iate"] = [translation.target_label]
                    source_parts.append("iate")

        if self.wikidata_client:
            language_code = wikidata_language_code(target_language)
            if language_code:
                translation = self.wikidata_client.translate_term(
                    source_term=target_term,
                    source_language_code=language_code,
                    target_language_code=language_code,
                )
                if translation:
                    candidates["wikipedia"] = [translation.target_label]
                    source_parts.append("wikipedia")

        confidence = min(1.0, term.confidence + 0.05 * len(candidates))
        verified_by = tuple(candidates)
        return replace_dataset_term(
            term,
            source="+".join(dict.fromkeys(source_parts)),
            term_group="verified" if verified_by else term.term_group,
            verified_by=verified_by,
            confidence=confidence,
            candidates=candidates,
        )

    def add_target_candidates(
        self,
        term: DatasetTerminologyTerm,
        source_language: str = "",
        target_language: str = "",
    ) -> DatasetTerminologyTerm:
        return self.add_external_candidates(term, target_language, source_language)


class LegalTerminologyGenerator:
    """Generates target-side legal terminology for EuroLex-style benchmark manifests."""

    def __init__(
        self,
        client: Any,
        model: str = "gpt-4.1-mini",
        max_terms: int = 20,
        use_iate: bool = False,
        use_wikidata: bool = False,
        use_unterm: bool = False,
        cache_path: Path | None = None,
        iate_client: IATEClient | None = None,
        wikidata_client: WikidataClient | None = None,
        unterm_client: UNTERMClient | None = None,
        llm_extractor: LLMLegalCandidateExtractor | None = None,
    ) -> None:
        self.model = model
        self.max_terms = max_terms
        self.use_iate = use_iate
        self.use_wikidata = use_wikidata
        self.use_unterm = use_unterm
        self.cache_path = cache_path
        self.iate_client = iate_client or (IATEClient() if use_iate else None)
        self.wikidata_client = wikidata_client or (WikidataClient() if use_wikidata else None)
        self.unterm_client = unterm_client or (UNTERMClient() if use_unterm else None)
        self.llm_extractor = llm_extractor or LLMLegalCandidateExtractor(client, model)
        self._cache = load_terminology_cache(cache_path)
        self._cache_lock = threading.Lock()

    def generate(
        self,
        target_language: str,
        reference_text: str,
        eurovoc_descriptors: dict[str, dict[str, str]] | None = None,
    ) -> list[DatasetTerminologyTerm]:
        cache_key = legal_terminology_cache_key(
            reference_text=reference_text,
            target_language=target_language,
            model=self.model,
            max_terms=self.max_terms,
            use_iate=self.use_iate,
            use_wikidata=self.use_wikidata,
            use_unterm=self.use_unterm,
            eurovoc_descriptors=eurovoc_descriptors or {},
        )
        with self._cache_lock:
            cached_terms = self._cache.get(cache_key)
        if cached_terms is not None:
            return [dataset_term_from_json(term) for term in cached_terms]

        terms = self.llm_extractor.extract(
            text=reference_text,
            target_language=target_language,
            max_terms=self.max_terms,
        )
        terms = [
            self.add_legal_evidence(
                term=term,
                target_language=target_language,
                eurovoc_descriptors=eurovoc_descriptors or {},
            )
            for term in terms
        ]
        terms = select_legal_terms(terms, max_terms=self.max_terms)

        with self._cache_lock:
            if cache_key not in self._cache:
                self._cache[cache_key] = [term.to_json() for term in terms]
                append_terminology_cache(self.cache_path, cache_key, terms)
        return terms

    def add_legal_evidence(
        self,
        term: DatasetTerminologyTerm,
        target_language: str,
        eurovoc_descriptors: dict[str, dict[str, str]],
    ) -> DatasetTerminologyTerm:
        if not term.target_terms:
            return term
        target_term = term.target_terms[0]
        iate_code = iate_language_code(target_language)
        wikidata_code = wikidata_language_code(target_language)
        language_code = iate_code or wikidata_code
        candidates: dict[str, list[str]] = {}
        source_parts = [term.source]

        if self.iate_client and iate_code:
            translation = self.iate_client.translate_term(
                source_term=target_term,
                source_language_code=iate_code,
                target_language_code=iate_code,
            )
            if translation:
                candidates["iate"] = [translation.target_label]
                source_parts.append("iate")

        if self.wikidata_client and wikidata_code:
            translation = self.wikidata_client.translate_term(
                source_term=target_term,
                source_language_code=wikidata_code,
                target_language_code=wikidata_code,
            )
            if translation:
                candidates["wikipedia"] = [translation.target_label]
                source_parts.append("wikipedia")

        if self.unterm_client and language_code and self.unterm_client.term_exists(
            target_term,
            language_code,
        ):
            candidates["unterm"] = [target_term]
            source_parts.append("unterm")

        eurovoc_match = matching_eurovoc_descriptor(
            target_term=target_term,
            target_language_code=language_code or "",
            descriptors_by_concept_id=eurovoc_descriptors,
        )
        if eurovoc_match:
            candidates["eurovoc"] = [eurovoc_match]
            source_parts.append("eurovoc")

        if not candidates:
            return term
        return replace_dataset_term(
            term,
            source="+".join(dict.fromkeys(source_parts)),
            term_group="verified",
            verified_by=tuple(candidates),
            confidence=min(1.0, term.confidence + 0.05 * len(candidates)),
            candidates=candidates,
        )


def parse_llm_target_candidates(text: str, reference_text: str) -> list[DatasetTerminologyTerm]:
    match = _JSON_OBJECT_RE.search(text)
    try:
        payload = json.loads(match.group(0) if match else text)
    except json.JSONDecodeError:
        return []

    terms = []
    for raw_term in payload.get("terms", []):
        if not isinstance(raw_term, dict):
            continue
        candidate = clean_candidate_term(str(raw_term.get("target_term", "")))
        verified_span = find_exact_text_span(reference_text, candidate)
        if not verified_span:
            continue
        terms.append(
            make_target_term(
                target_term=verified_span,
                category=str(raw_term.get("category", "other")).strip() or "other",
                source="llm_target",
                confidence=max(parse_confidence(raw_term.get("confidence")), 0.8),
                reason=str(raw_term.get("reason", "")).strip()
                or "LLM-proposed exact target span verified in reference text.",
            )
        )
    return terms


def parse_llm_legal_candidates(text: str, reference_text: str) -> list[DatasetTerminologyTerm]:
    match = _JSON_OBJECT_RE.search(text)
    try:
        payload = json.loads(match.group(0) if match else text)
    except json.JSONDecodeError:
        return []

    terms = []
    for raw_term in payload.get("terms", []):
        if not isinstance(raw_term, dict):
            continue
        candidate = clean_candidate_term(str(raw_term.get("target_term", "")))
        verified_span = find_exact_text_span(reference_text, candidate)
        if not verified_span:
            continue
        terms.append(
            DatasetTerminologyTerm(
                source_term="",
                target_terms=(verified_span,),
                reference_candidates=(verified_span,),
                category=str(raw_term.get("category", "other")).strip() or "other",
                source="legal_llm",
                term_group="llm",
                confidence=max(parse_confidence(raw_term.get("confidence")), 0.8),
                decision="keep_reference",
                reason=str(raw_term.get("reason", "")).strip()
                or "Legal LLM-proposed exact target span verified in reference text.",
            )
        )
    return terms


def extract_with_chemdataextractor(text: str) -> list[DatasetTerminologyTerm]:
    try:
        from chemdataextractor.doc import Paragraph
    except ImportError:
        return []

    terms = []
    for mention in Paragraph(text).cems:
        term = str(mention.text).strip()
        if term:
            terms.append(make_target_term(term, "chemical", "chemdataextractor", 0.9))
    return terms


def extract_with_chemu_biobert(text: str) -> list[DatasetTerminologyTerm]:
    try:
        from transformers import pipeline
    except ImportError:
        return []

    try:
        ner = pipeline(
            "token-classification",
            model="kamalkraj/ChemBERTa-finetuned-chemical-ner",
            aggregation_strategy="simple",
        )
        entities = ner(text[:4000])
    except Exception:
        return []

    terms = []
    for entity in entities:
        term = str(entity.get("word", "")).strip()
        score = parse_confidence(entity.get("score"))
        if term:
            terms.append(make_target_term(term, "chemical", "chemu_biobert", max(score, 0.85)))
    return terms


def extract_with_regexes(text: str) -> list[DatasetTerminologyTerm]:
    terms = []
    for match in _CHEMICAL_FORMULA_SCAN_RE.finditer(text):
        terms.append(make_target_term(match.group(0), "identifier", "regex", 0.85))
    for match in _NUMERIC_UNIT_SCAN_RE.finditer(text):
        terms.append(make_target_term(match.group(0), "unit", "regex", 0.8))
    for match in _CHEMICAL_PREFIX_SCAN_RE.finditer(text):
        terms.append(make_target_term(match.group(0), "chemical", "regex", 0.78))
    for match in _CHEMICAL_PHRASE_SCAN_RE.finditer(text):
        terms.append(make_target_term(match.group(0), "chemical", "regex", 0.75))
    return terms


def make_target_term(
    target_term: str,
    category: str,
    source: str,
    confidence: float,
    reason: str = "Extracted from the target reference without source-target alignment.",
) -> DatasetTerminologyTerm:
    target_term = clean_candidate_term(target_term)
    decision = (
        "preserve" if should_preserve_dataset_term(target_term, category) else "keep_reference"
    )
    term_group = "llm" if source == "llm_target" else "algorithmic"
    return DatasetTerminologyTerm(
        source_term="",
        target_terms=(target_term,),
        reference_candidates=(target_term,),
        category=category,
        source=source,
        term_group=term_group,
        confidence=confidence,
        decision=decision,
        reason=reason,
    )


def clean_candidate_term(term: str) -> str:
    return re.sub(r"\s+", " ", term).strip(" ,.;:()[]{}")


def find_exact_text_span(text: str, candidate: str) -> str:
    if not candidate:
        return ""
    if candidate in text:
        return candidate
    match = re.search(re.escape(candidate), text, flags=re.IGNORECASE)
    return match.group(0) if match else ""


def deduplicate_terms(terms: list[DatasetTerminologyTerm]) -> list[DatasetTerminologyTerm]:
    by_key: dict[str, DatasetTerminologyTerm] = {}
    for term in terms:
        key = normalize_term_key(term.target_terms[0] if term.target_terms else "")
        if not key:
            continue
        existing = by_key.get(key)
        if existing is None or term.confidence > existing.confidence:
            by_key[key] = term
    return sorted(
        by_key.values(),
        key=lambda term: (term.confidence, len(term.target_terms[0])),
        reverse=True,
    )


def select_dataset_terms(
    terms: list[DatasetTerminologyTerm],
    max_terms: int,
    confidence_threshold: float = 0.0,
) -> list[DatasetTerminologyTerm]:
    accepted = [
        term
        for term in terms
        if term.decision != "drop"
        and term.target_terms
        and term.confidence >= confidence_threshold
    ]
    accepted.sort(key=lambda term: (term.confidence, len(term.target_terms[0])), reverse=True)
    return accepted[:max_terms]


def dataset_term_from_json(payload: dict[str, Any]) -> DatasetTerminologyTerm:
    raw_candidates = payload.get("external_candidates", payload.get("candidates", {}))
    if not isinstance(raw_candidates, dict):
        raw_candidates = {}
    return DatasetTerminologyTerm(
        source_term=str(payload.get("source_term", "")).strip(),
        target_terms=tuple(
            str(target_term).strip()
            for target_term in payload.get("target_terms", [])
            if str(target_term).strip()
        ),
        reference_candidates=tuple(
            str(candidate).strip()
            for candidate in payload.get("reference_candidates", [])
            if str(candidate).strip()
        ),
        category=str(payload.get("category", "other")).strip() or "other",
        source=str(payload.get("source", "")).strip() or "unknown",
        term_group=str(payload.get("term_group", "")).strip()
        or infer_term_group_from_source(
            str(payload.get("source", "")).strip(),
            raw_candidates,
        ),
        verified_by=tuple(
            str(source).strip()
            for source in payload.get("verified_by", [])
            if str(source).strip()
        )
        or tuple(str(source) for source in raw_candidates),
        confidence=parse_confidence(payload.get("confidence")),
        decision=str(payload.get("decision", "")).strip(),
        reason=str(payload.get("reason", "")).strip(),
        candidates={
            str(source): [str(term) for term in terms]
            for source, terms in raw_candidates.items()
            if isinstance(terms, list)
        },
    )


def replace_dataset_term(
    term: DatasetTerminologyTerm,
    target_terms: tuple[str, ...] | None = None,
    reference_candidates: tuple[str, ...] | None = None,
    category: str | None = None,
    source: str | None = None,
    term_group: str | None = None,
    verified_by: tuple[str, ...] | None = None,
    confidence: float | None = None,
    decision: str | None = None,
    reason: str | None = None,
    candidates: dict[str, list[str]] | None = None,
) -> DatasetTerminologyTerm:
    return DatasetTerminologyTerm(
        source_term=term.source_term,
        target_terms=term.target_terms if target_terms is None else target_terms,
        reference_candidates=(
            term.reference_candidates if reference_candidates is None else reference_candidates
        ),
        category=term.category if category is None else category,
        source=term.source if source is None else source,
        term_group=term.term_group if term_group is None else term_group,
        verified_by=term.verified_by if verified_by is None else verified_by,
        confidence=term.confidence if confidence is None else confidence,
        decision=term.decision if decision is None else decision,
        reason=term.reason if reason is None else reason,
        candidates=term.candidates if candidates is None else candidates,
    )


def should_preserve_dataset_term(source_term: str, category: str = "") -> bool:
    stripped = source_term.strip()
    if _FORMULA_OR_IDENTIFIER_RE.match(stripped):
        return True
    if _COMPACT_NUMERIC_UNIT_RE.match(stripped):
        return True
    if _SEQUENCE_IDENTIFIER_RE.match(stripped):
        return True
    return False


def parse_confidence(value: object) -> float:
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(confidence, 1.0))


def normalize_term_key(term: str) -> str:
    return " ".join(term.casefold().split())


def build_eurolex_descriptor_terms(
    descriptors_by_concept_id: dict[str, dict[str, str]],
    target_language_code: str,
    target_text: str,
) -> list[DatasetTerminologyTerm]:
    """Create EuroLex terminology from EuroVoc descriptors found in target text.

    EuroVoc labels are document-level metadata, not guaranteed in-text terms. This helper only
    promotes a descriptor to benchmark terminology when the target-language descriptor appears as a
    normalized substring in the target/reference text.
    """

    terms = []
    normalized_target = normalize_term_key(target_text)
    for concept_id, labels_by_language in descriptors_by_concept_id.items():
        descriptor = labels_by_language.get(target_language_code) or labels_by_language.get("en")
        if not descriptor:
            continue
        descriptor = " ".join(descriptor.split())
        if normalize_term_key(descriptor) not in normalized_target:
            continue
        terms.append(
            DatasetTerminologyTerm(
                target_terms=(descriptor,),
                reference_candidates=(descriptor,),
                category="other",
                source="eurovoc_label",
                term_group="verified",
                verified_by=("eurovoc",),
                confidence=1.0,
                decision="keep_reference",
                reason=f"EuroVoc descriptor {concept_id} appears in the target reference text.",
                candidates={"eurovoc": [descriptor]},
            )
        )
    return terms


def matching_eurovoc_descriptor(
    target_term: str,
    target_language_code: str,
    descriptors_by_concept_id: dict[str, dict[str, str]],
) -> str:
    normalized_term = normalize_term_key(target_term)
    if not normalized_term:
        return ""
    for labels_by_language in descriptors_by_concept_id.values():
        descriptor = labels_by_language.get(target_language_code) or labels_by_language.get("en")
        if descriptor and normalize_term_key(descriptor) == normalized_term:
            return " ".join(descriptor.split())
    return ""


def select_legal_terms(
    terms: list[DatasetTerminologyTerm],
    max_terms: int,
) -> list[DatasetTerminologyTerm]:
    deduplicated = deduplicate_terms(terms)
    return sorted(
        deduplicated,
        key=lambda term: (
            term.term_group == "verified",
            term.confidence,
            len(term.target_terms[0]) if term.target_terms else 0,
        ),
        reverse=True,
    )[:max_terms]


def infer_term_group_from_source(source: str, candidates: dict[str, list[str]]) -> str:
    if candidates:
        return "verified"
    if source == "llm_target" or source.startswith("llm_target+"):
        return "llm"
    return "algorithmic"


def terminology_cache_key(
    reference_text: str,
    target_language: str,
    model: str,
    max_terms: int,
    use_llm: bool,
    use_iate: bool,
    use_wikidata: bool,
    use_pubchem: bool,
) -> str:
    payload = {
        "reference_text": reference_text,
        "target_language": target_language,
        "model": model,
        "max_terms": max_terms,
        "use_llm": use_llm,
        "use_iate": use_iate,
        "use_wikidata": use_wikidata,
        "use_pubchem": use_pubchem,
        "pipeline_version": _TERMINOLOGY_PIPELINE_VERSION,
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def legal_terminology_cache_key(
    reference_text: str,
    target_language: str,
    model: str,
    max_terms: int,
    use_iate: bool,
    use_wikidata: bool,
    use_unterm: bool,
    eurovoc_descriptors: dict[str, dict[str, str]],
) -> str:
    payload = {
        "reference_text": reference_text,
        "target_language": target_language,
        "model": model,
        "max_terms": max_terms,
        "use_iate": use_iate,
        "use_wikidata": use_wikidata,
        "use_unterm": use_unterm,
        "eurovoc_descriptors": eurovoc_descriptors,
        "pipeline_version": "legal-target-llm-candidate-v2",
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_terminology_cache(cache_path: Path | None) -> dict[str, list[dict[str, Any]]]:
    if cache_path is None or not cache_path.exists():
        return {}

    cache: dict[str, list[dict[str, Any]]] = {}
    with cache_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            payload = json.loads(line)
            cache[str(payload["key"])] = list(payload.get("terminology", []))
    return cache


def append_terminology_cache(
    cache_path: Path | None,
    cache_key: str,
    terms: list[DatasetTerminologyTerm],
) -> None:
    if cache_path is None:
        return
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with cache_path.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {"key": cache_key, "terminology": [term.to_json() for term in terms]},
                ensure_ascii=False,
            )
            + "\n"
        )


def load_manifest_terminology(data_dir: Path) -> dict[tuple[str, str, str], list[dict[str, Any]]]:
    terminology_by_key: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for manifest_path in data_dir.glob("*manifest*.jsonl"):
        with manifest_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                row = json.loads(line)
                terminology = row.get("terminology")
                if not terminology:
                    continue
                source_id = str(row.get("source_id") or row.get("publication_number") or "")
                language_code = str(row.get("target_language_code") or "")
                text_field = str(row.get("text_field") or "context")
                if source_id and language_code:
                    terminology_by_key[(source_id, language_code, text_field)] = terminology
    return terminology_by_key
