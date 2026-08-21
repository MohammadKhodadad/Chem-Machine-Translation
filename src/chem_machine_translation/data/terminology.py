from __future__ import annotations

import hashlib
import json
import re
import threading
from collections.abc import Iterable
from dataclasses import dataclass, field
from http.client import RemoteDisconnected
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
_CANDIDATE_TOKEN_RE = re.compile(r"\b[^\W_][\w'’.-]*\b", re.UNICODE)
_COMPACT_NUMERIC_UNIT_RE = re.compile(
    r"^\d+(?:[.,]\d+)?(?:\s*(?:-|to|–|—|à)\s*\d+(?:[.,]\d+)?)?\s*"
    r"(?:%|°C|K|ppm|ppb|mol%|wt%|mg|g|kg|mL|L|cm2|cm3|mm|cm|m|nm|µm|um)$",
    re.IGNORECASE,
)
_SEQUENCE_IDENTIFIER_RE = re.compile(
    r"^(?:SEQ\s+ID\s+NO:\s*\d+|CAS\s+RN\s*[:\s]?\d[\d-]+)$",
    re.IGNORECASE,
)
_PUBCHEM_ENDPOINT = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name"
_CHEBI_ENDPOINT = "https://www.ebi.ac.uk/chebi/backend/api/public"
_CHEMBL_ENDPOINT = "https://www.ebi.ac.uk/chembl/api/data"
_MESH_LOOKUP_ENDPOINT = "https://id.nlm.nih.gov/mesh/lookup/descriptor"
_NCI_ENDPOINT = "https://api-evsrest.nci.nih.gov/api/v1"
_AGROVOC_ENDPOINT = "https://agrovoc.fao.org/browse/rest/v1"
_USER_AGENT = "chem-machine-translation/0.1 (benchmark terminology lookup)"
_TERMINOLOGY_PIPELINE_VERSION = "target-llm-stanza-ud-candidate-v5"
_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)
_UD_HEAD_UPOS = {"NOUN", "PROPN", "NUM", "SYM", "X"}
_UD_CONTENT_UPOS = {"ADJ", "NOUN", "NUM", "PROPN", "SYM", "X"}
_UD_EXPANSION_DEPRELS = {
    "amod",
    "appos",
    "case",
    "compound",
    "fixed",
    "flat",
    "nmod",
    "nummod",
}
_UD_BLOCKED_BOUNDARY_UPOS = {"ADP", "AUX", "CCONJ", "DET", "PART", "PRON", "SCONJ"}
_SPAN_SEPARATOR_RE = re.compile(r"[,;:]")
_LEGAL_CITATION_RE = re.compile(
    r"\b(?:articles?|artikels?|articulos?|artículos?|artigos?|paragraphs?|"
    r"paragraphes?|absatz|absätze|apartados?|sections?)\s+\d+\b|"
    r"\b\d+\s+(?:of|de|del|des|do|du|von)\s+"
    r"(?:this|the|present|cet|cette|dies(?:es|em|er)?|el|la|le|o)?\s*"
    r"(?:articles?|artikels?|articulos?|artículos?|artigos?|paragraphs?|"
    r"paragraphes?|absatz|absätze|apartados?)\b",
    re.IGNORECASE,
)
_DATE_FRAGMENT_RE = re.compile(
    r"\b(?:from|of|de|del|des|do|du|von|vom)\s+\d{1,2}\b|"
    r"\b\d{1,2}\.?\s+"
    r"(?:january|february|march|april|may|june|july|august|september|october|"
    r"november|december|janvier|fevrier|février|mars|avril|mai|juin|juillet|"
    r"aout|août|septembre|octobre|novembre|decembre|décembre|januar|februar|"
    r"marz|märz|april|mai|juni|juli|august|september|oktober|november|dezember|"
    r"enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|"
    r"noviembre|diciembre|janeiro|fevereiro|marco|março|abril|maio|junho|"
    r"julho|agosto|setembro|outubro|novembro|dezembro)\b|"
    r"\b(?:19|20)\d{2}\b",
    re.IGNORECASE,
)
_MONTH_NAME_RE = re.compile(
    r"^(?:january|february|march|april|may|june|july|august|september|october|"
    r"november|december|janvier|fevrier|février|mars|avril|mai|juin|juillet|"
    r"aout|août|septembre|octobre|novembre|decembre|décembre|januar|februar|"
    r"marz|märz|april|mai|juni|juli|august|september|oktober|november|dezember|"
    r"enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|"
    r"noviembre|diciembre|janeiro|fevereiro|marco|março|abril|maio|junho|"
    r"julho|agosto|setembro|outubro|novembro|dezembro)$",
    re.IGNORECASE,
)
_MAX_STANZA_TERM_TOKENS = 6
_NOBI_LABEL_MAP = {
    "LABEL_0": "O",
    "LABEL_1": "B",
    "LABEL_2": "BN",
    "LABEL_3": "IN",
    "LABEL_4": "I",
}
DEFAULT_MSPLADE_MODEL = "naver/splade-cocondenser-ensembledistil"
DEFAULT_SPACY_MODEL = ""
DEFAULT_SPACY_MODELS = {
    "de": "de_core_news_sm",
    "en": "en_core_web_sm",
    "es": "es_core_news_sm",
    "fr": "fr_core_news_sm",
    "ja": "ja_core_news_sm",
    "pt": "pt_core_news_sm",
    "ru": "ru_core_news_sm",
    "zh": "zh_core_web_sm",
}
_SPACY_LANGUAGE_ALIASES = {
    "chinese": "zh",
    "english": "en",
    "french": "fr",
    "german": "de",
    "japanese": "ja",
    "portuguese": "pt",
    "russian": "ru",
    "spanish": "es",
}
_SPACY_BLOCKED_BOUNDARY_LEMMAS = {
    "apply",
    "be",
    "become",
    "comprise",
    "concern",
    "consist",
    "contain",
    "include",
    "make",
    "provide",
    "relate",
    "said",
    "thereof",
    "use",
}
_NLTK_STOPWORD_LANGUAGES = {
    "de": "german",
    "en": "english",
    "es": "spanish",
    "fr": "french",
    "pt": "portuguese",
}
_BOUNDARY_STOPWORDS = {
    "a",
    "an",
    "and",
    "as",
    "by",
    "da",
    "das",
    "de",
    "del",
    "des",
    "do",
    "dos",
    "du",
    "e",
    "en",
    "et",
    "for",
    "für",
    "in",
    "la",
    "le",
    "les",
    "of",
    "or",
    "the",
    "to",
    "und",
    "y",
}

TARGET_CANDIDATE_EXTRACTOR_SYSTEM_PROMPT = """You extract terminology candidates from target
reference translations for chemistry and patent machine-translation benchmarks.

The text may be in any language. Return only exact spans that appear in the provided target text.
Do not translate, normalize, rewrite, lemmatize, abbreviate, explain, or invent terms.

Extract only terms that a domain translator should preserve consistently:
- chemical names, compounds, materials, formulas, reagents, solvents, polymers, proteins;
- technical processes, methods, assay/analytical terms, properties, hazards, identifiers;
- compact numeric/unit expressions only when the quantity itself is technically meaningful.

Reject:
- common prose, generic verbs/adjectives, boilerplate patent wording, and broad field labels;
- whole clauses, sentence fragments, headings, dates, citations, inventor/applicant names;
- single common words unless they are unambiguous domain terms in the target language.

Prefer the smallest exact span that carries the technical meaning. If a longer phrase contains a
specific chemical/material term, return the specific term, not the whole phrase. Return no terms
when the text does not contain strong technical terminology.

Confidence calibration:
- 0.90-1.00: precise named chemical/material/process/identifier.
- 0.70-0.89: likely domain term but context-dependent.
- below 0.70: do not return it.

Allowed categories: chemical, material, formulation, process, method, property, unit, identifier,
hazard, biological, equipment, other.

Return only valid JSON with this shape:
{
  "terms": [
    {
      "target_term": "exact target text span",
      "category": "allowed category",
      "confidence": 0.0,
      "reason": "short reason"
    }
  ]
}
"""

LEGAL_CANDIDATE_EXTRACTOR_SYSTEM_PROMPT = """You extract legal terminology candidates from
target/reference translations for legal machine-translation benchmarks.

The text may be in any language. Return only exact spans that appear in the provided target text.
Do not translate, normalize, rewrite, lemmatize, abbreviate, explain, or invent terms.

Extract only terms that a legal translator should preserve consistently:
- legal instruments, institutions, committees, agencies, programmes, funds, and named bodies;
- procedures, rights, obligations, restrictions, sanctions, remedies, legal effects;
- regulatory domains and named legal acts when they are not just generic prose;
- defined terms introduced by definition wording, such as "shall mean" or "for the purposes of".

Reject:
- dates, article numbers alone, paragraph references alone, names of people, signatures;
- whole clauses, sentence fragments, generic single words, and ordinary administrative prose;
- repeated treaty boilerplate unless the phrase is a recognized legal or institutional term;
- full titles when a shorter legal act, institution, or defined term inside the title is better.

Prefer the smallest exact span that carries the legal meaning. In definition-heavy text, prefer the
defined term itself over the full definition. Return no terms when the text does not contain strong
legal terminology.

Confidence calibration:
- 0.90-1.00: precise legal/institutional term or explicit defined term.
- 0.70-0.89: likely legal term but context-dependent.
- below 0.70: do not return it.

Allowed categories: institution, legal_act, defined_term, procedure, right, obligation,
restriction, sanction, remedy, policy, regulatory_domain, programme, fund, other.

Return only valid JSON with this shape:
{
  "terms": [
    {
      "target_term": "exact target text span",
      "category": "allowed category",
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


@dataclass(frozen=True)
class CandidateToken:
    surface: str
    start_char: int
    end_char: int


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
        except (
            HTTPError,
            URLError,
            TimeoutError,
            RemoteDisconnected,
            OSError,
            json.JSONDecodeError,
        ):
            self._cache[key] = []
            return []

        synonyms = []
        for item in payload.get("InformationList", {}).get("Information", []):
            raw_synonyms = item.get("Synonym", [])
            if isinstance(raw_synonyms, list):
                synonyms.extend(str(synonym).strip() for synonym in raw_synonyms if synonym)
        self._cache[key] = list(dict.fromkeys(synonyms[:20]))
        return self._cache[key]


class ChEBIClient:
    """Best-effort ChEBI verifier using the public EBI search API."""

    def __init__(self, endpoint: str = _CHEBI_ENDPOINT, timeout_seconds: float = 5.0) -> None:
        self.endpoint = endpoint.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self._cache: dict[str, list[str]] = {}

    def lookup_synonyms(self, term: str) -> list[str]:
        key = term.casefold()
        if key in self._cache:
            return self._cache[key]
        payload = get_json(
            f"{self.endpoint}/es_search/?{urlencode({'query': term})}",
            self.timeout_seconds,
        )
        names = collect_string_values(
            payload,
            {"name", "ascii_name", "chebi_accession"},
        )
        self._cache[key] = names[:20] if term_matches_any(term, names) else []
        return self._cache[key]


class ChEMBLClient:
    """Best-effort ChEMBL verifier for molecules and synonyms."""

    def __init__(self, endpoint: str = _CHEMBL_ENDPOINT, timeout_seconds: float = 5.0) -> None:
        self.endpoint = endpoint.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self._cache: dict[str, list[str]] = {}

    def lookup_synonyms(self, term: str) -> list[str]:
        key = term.casefold()
        if key in self._cache:
            return self._cache[key]
        payload = get_json(
            f"{self.endpoint}/molecule/search.json?{urlencode({'q': term})}",
            self.timeout_seconds,
        )
        names = collect_string_values(
            payload,
            {"pref_name", "molecule_synonym", "synonyms", "molecule_chembl_id"},
        )
        self._cache[key] = names[:20] if term_matches_any(term, names) else []
        return self._cache[key]


class MeSHClient:
    """Best-effort MeSH RDF verifier via the NLM lookup API."""

    def __init__(
        self,
        endpoint: str = _MESH_LOOKUP_ENDPOINT,
        timeout_seconds: float = 5.0,
    ) -> None:
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds
        self._cache: dict[str, list[str]] = {}

    def lookup_synonyms(self, term: str) -> list[str]:
        key = term.casefold()
        if key in self._cache:
            return self._cache[key]
        payload = get_json(
            f"{self.endpoint}?{urlencode({'label': term, 'match': 'contains', 'limit': 10})}",
            self.timeout_seconds,
        )
        names = collect_string_values(payload, {"label", "resource"})
        self._cache[key] = names[:20] if term_matches_any(term, names) else []
        return self._cache[key]


class NCIThesaurusClient:
    """Best-effort NCI Thesaurus verifier using EVS REST."""

    def __init__(self, endpoint: str = _NCI_ENDPOINT, timeout_seconds: float = 5.0) -> None:
        self.endpoint = endpoint.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self._cache: dict[str, list[str]] = {}

    def lookup_synonyms(self, term: str) -> list[str]:
        key = term.casefold()
        if key in self._cache:
            return self._cache[key]
        payload = get_json(
            f"{self.endpoint}/concept/ncit/search?"
            f"{urlencode({'term': term, 'type': 'match', 'include': 'minimal', 'pageSize': 10})}",
            self.timeout_seconds,
        )
        names = collect_string_values(payload, {"name", "label", "termName"})
        self._cache[key] = names[:20] if term_matches_any(term, names) else []
        return self._cache[key]


class AGROVOCClient:
    """Best-effort multilingual AGROVOC verifier via Skosmos REST."""

    def __init__(self, endpoint: str = _AGROVOC_ENDPOINT, timeout_seconds: float = 5.0) -> None:
        self.endpoint = endpoint.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self._cache: dict[tuple[str, str], list[str]] = {}

    def lookup_synonyms(self, term: str, language_code: str = "") -> list[str]:
        key = (term.casefold(), language_code)
        if key in self._cache:
            return self._cache[key]
        query = {
            "query": f"*{term}*",
            "lang": language_code or "en",
        }
        payload = get_json(
            f"{self.endpoint}/search/?{urlencode(query)}",
            self.timeout_seconds,
        )
        names = collect_string_values(payload, {"prefLabel", "altLabel", "label"})
        self._cache[key] = names[:20] if term_matches_any(term, names) else []
        return self._cache[key]


def get_json(url: str, timeout_seconds: float) -> Any:
    request = Request(url, headers={"User-Agent": _USER_AGENT, "Accept": "application/json"})
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))
    except (
        HTTPError,
        URLError,
        TimeoutError,
        RemoteDisconnected,
        OSError,
        json.JSONDecodeError,
    ):
        return {}


def post_json(url: str, payload: dict[str, Any], timeout_seconds: float) -> Any:
    data = json.dumps(payload).encode("utf-8")
    request = Request(
        url,
        data=data,
        headers={
            "User-Agent": _USER_AGENT,
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return {}


def collect_string_values(payload: Any, keys: set[str]) -> list[str]:
    values: list[str] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in keys:
                values.extend(flatten_strings(value))
            elif isinstance(value, dict | list):
                values.extend(collect_string_values(value, keys))
    elif isinstance(payload, list):
        for item in payload:
            values.extend(collect_string_values(item, keys))
    return list(dict.fromkeys(value.strip() for value in values if value.strip()))


def flatten_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return collect_string_values(value, set(value))
    if isinstance(value, list):
        values: list[str] = []
        for item in value:
            values.extend(flatten_strings(item))
        return values
    return []


def term_matches_any(term: str, names: list[str]) -> bool:
    key = normalize_term_key(term)
    return any(
        key and (key == normalize_term_key(name) or key in normalize_term_key(name))
        for name in names
    )


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
        except (HTTPError, URLError, TimeoutError, RemoteDisconnected, OSError):
            return ""


class TargetTerminologyExtractor:
    """Target-side candidate extractor based on language-generic Universal Dependencies."""

    def __init__(self) -> None:
        self._stanza_pipelines: dict[str, Any] = {}

    def extract(
        self,
        text: str,
        max_terms: int,
        target_language: str = "",
    ) -> list[DatasetTerminologyTerm]:
        language_code = terminology_language_code(target_language)
        if not language_code:
            return []

        doc = self.parse_with_stanza(text=text, language_code=language_code)
        if doc is None:
            return []

        candidates = [
            *self.ud_dependency_candidates(text=text, doc=doc),
            *self.ud_relaxed_ngram_candidates(text=text, doc=doc),
            *self.ud_proper_name_candidates(text=text, doc=doc),
        ]
        return deduplicate_terms(candidates)[:max_terms]

    def parse_with_stanza(self, text: str, language_code: str) -> Any | None:
        try:
            import stanza
        except ImportError:
            return None

        try:
            if language_code not in self._stanza_pipelines:
                self._stanza_pipelines[language_code] = stanza.Pipeline(
                    lang=language_code,
                    processors="tokenize,pos,lemma,depparse",
                    verbose=False,
                )
            return self._stanza_pipelines[language_code](text)
        except Exception:
            return None

    def ud_dependency_candidates(self, text: str, doc: Any) -> list[DatasetTerminologyTerm]:
        candidates = []
        for sentence in doc.sentences:
            words = list(sentence.words)
            for head in words:
                if head.upos not in _UD_HEAD_UPOS:
                    continue
                candidates.extend(
                    make_stanza_terms(
                        text=text,
                        words=dependency_span_words(head, words),
                        source="stanza_ud_dependency",
                        confidence=0.72,
                        reason="Noun-headed Universal Dependencies span from target reference.",
                    )
                )
        return candidates

    def ud_relaxed_ngram_candidates(self, text: str, doc: Any) -> list[DatasetTerminologyTerm]:
        candidates = []
        for sentence in doc.sentences:
            words = list(sentence.words)
            for size in range(1, 7):
                for index in range(0, max(len(words) - size + 1, 0)):
                    span_words = words[index : index + size]
                    if not stanza_ngram_is_plausible(span_words):
                        continue
                    candidates.extend(
                        make_stanza_terms(
                            text=text,
                            words=span_words,
                            source="stanza_ud_ngram",
                            confidence=stanza_candidate_confidence(span_words),
                            reason=(
                                "Plausible Universal Dependencies content span "
                                "from target reference."
                            ),
                        )
                    )
        return candidates

    def ud_proper_name_candidates(self, text: str, doc: Any) -> list[DatasetTerminologyTerm]:
        candidates = []
        for sentence in doc.sentences:
            current = []
            for word in sentence.words:
                if word.upos == "PROPN":
                    current.append(word)
                    continue
                candidates.extend(make_proper_name_terms(text, current))
                current = []
            candidates.extend(make_proper_name_terms(text, current))
        return candidates


class XLMRNOBITerminologyExtractor:
    """XLM-R/NOBI token-classification candidate extractor."""

    def __init__(self, model_name: str = "tthhanh/xlm-ate-nobi-en-nes") -> None:
        self.model_name = model_name
        self._pipeline: Any | None = None

    def extract(
        self,
        text: str,
        max_terms: int,
        target_language: str = "",
    ) -> list[DatasetTerminologyTerm]:
        del target_language
        pipeline = self.load_pipeline()
        if pipeline is None:
            return []
        try:
            outputs = pipeline(text[:4000])
        except Exception:
            return []
        terms = decode_nobi_terms(text=text[:4000], outputs=outputs)
        return deduplicate_terms(terms)[:max_terms]

    def load_pipeline(self) -> Any | None:
        if self._pipeline is not None:
            return self._pipeline
        try:
            from transformers import pipeline
        except ImportError:
            return None
        try:
            self._pipeline = pipeline(
                "token-classification",
                model=self.model_name,
                aggregation_strategy="none",
            )
        except Exception:
            return None
        return self._pipeline


class NLTKTerminologyExtractor:
    """Lightweight NLTK n-gram candidate extractor for exact target spans."""

    def __init__(self, max_ngram_tokens: int = 5) -> None:
        self.max_ngram_tokens = max_ngram_tokens
        self._stopwords_by_language: dict[str, set[str]] = {}

    def extract(
        self,
        text: str,
        max_terms: int,
        target_language: str = "",
    ) -> list[DatasetTerminologyTerm]:
        if not self.load_nltk():
            return []
        tokens = candidate_token_spans(text)
        if not tokens:
            return []

        language_code = terminology_language_code(target_language)
        stopwords = self.stopwords_for_language(language_code)
        candidates = []
        for size in range(1, self.max_ngram_tokens + 1):
            for index in range(0, max(len(tokens) - size + 1, 0)):
                window = tokens[index : index + size]
                if not token_window_is_plausible(window, stopwords):
                    continue
                surface = clean_candidate_term(text[window[0].start_char : window[-1].end_char])
                if not candidate_surface_is_clean(surface):
                    continue
                candidates.append(
                    make_target_term(
                        target_term=surface,
                        category="other",
                        source="nltk_ngram",
                        confidence=nltk_ngram_confidence(window),
                        reason="NLTK token n-gram candidate from target reference.",
                    )
                )
        return deduplicate_terms(candidates)[:max_terms]

    def load_nltk(self) -> bool:
        try:
            import nltk  # noqa: F401
        except ImportError:
            return False
        return True

    def stopwords_for_language(self, language_code: str) -> set[str]:
        if language_code in self._stopwords_by_language:
            return self._stopwords_by_language[language_code]
        stopwords = set(_BOUNDARY_STOPWORDS)
        nltk_language = _NLTK_STOPWORD_LANGUAGES.get(language_code)
        if nltk_language:
            try:
                from nltk.corpus import stopwords as nltk_stopwords

                stopwords.update(word.casefold() for word in nltk_stopwords.words(nltk_language))
            except LookupError:
                pass
        self._stopwords_by_language[language_code] = stopwords
        return stopwords


class SpaCyTerminologyExtractor:
    """spaCy exact-span extractor using trained linguistic spans when available."""

    def __init__(
        self,
        model_name: str = DEFAULT_SPACY_MODEL,
        max_ngram_tokens: int = 5,
    ) -> None:
        self.model_name = model_name
        self.max_ngram_tokens = max_ngram_tokens
        self._pipelines: dict[str, Any] = {}

    def extract(
        self,
        text: str,
        max_terms: int,
        target_language: str = "",
    ) -> list[DatasetTerminologyTerm]:
        pipeline = self.load_pipeline(target_language)
        if pipeline is None:
            return []
        try:
            doc = pipeline(text[:4000])
        except Exception:
            return []

        candidates = []
        candidates.extend(self.entity_terms(doc))
        candidates.extend(self.noun_chunk_terms(doc))
        candidates.extend(self.ngram_terms(text[:4000], doc, target_language))
        return deduplicate_terms(candidates)[:max_terms]

    def load_pipeline(self, target_language: str) -> Any | None:
        language_code = spacy_language_code(target_language)
        cache_key = self.model_name or language_code or "xx"
        if cache_key in self._pipelines:
            return self._pipelines[cache_key]
        try:
            import spacy
        except ImportError:
            return None
        try:
            if self.model_name:
                pipeline = spacy.load(self.model_name)
            elif default_model := DEFAULT_SPACY_MODELS.get(language_code):
                try:
                    pipeline = spacy.load(default_model)
                except OSError:
                    pipeline = spacy.blank(language_code)
            else:
                pipeline = spacy.blank(cache_key)
        except Exception:
            return None
        self._pipelines[cache_key] = pipeline
        return pipeline

    def entity_terms(self, doc: Any) -> list[DatasetTerminologyTerm]:
        terms = []
        for entity in getattr(doc, "ents", ()):
            surface = clean_candidate_term(entity.text)
            if candidate_surface_is_clean(surface) and spacy_span_has_content(entity):
                terms.append(
                    make_target_term(
                        target_term=surface,
                        category="other",
                        source="spacy_entity",
                        confidence=0.74,
                        reason="spaCy named-entity candidate from target reference.",
                    )
                )
        return terms

    def noun_chunk_terms(self, doc: Any) -> list[DatasetTerminologyTerm]:
        try:
            noun_chunks = list(doc.noun_chunks)
        except (NotImplementedError, ValueError):
            return []
        terms = []
        for chunk in noun_chunks:
            chunk = trim_spacy_span(chunk)
            surface = clean_candidate_term(chunk.text)
            if candidate_surface_is_clean(surface):
                terms.append(
                    make_target_term(
                        target_term=surface,
                        category="other",
                        source="spacy_noun_chunk",
                        confidence=0.7,
                        reason="spaCy noun-chunk candidate from target reference.",
                    )
                )
        return terms

    def ngram_terms(
        self,
        text: str,
        doc: Any,
        target_language: str,
    ) -> list[DatasetTerminologyTerm]:
        language_code = spacy_language_code(target_language)
        has_pos = spacy_doc_has_pos(doc)
        stopwords = set(_BOUNDARY_STOPWORDS) | _SPACY_BLOCKED_BOUNDARY_LEMMAS
        candidates = []
        spans = list(doc.sents) if spacy_doc_has_sentences(doc) else [doc]
        max_ngram_tokens = self.max_ngram_tokens if has_pos else min(self.max_ngram_tokens, 3)
        for span in spans:
            spacy_tokens = [token for token in span if spacy_token_is_candidate(token)]
            candidate_tokens = [
                CandidateToken(token.text, token.idx, token.idx + len(token.text))
                for token in spacy_tokens
            ]
            for size in range(1, max_ngram_tokens + 1):
                for index in range(0, max(len(spacy_tokens) - size + 1, 0)):
                    token_window = spacy_tokens[index : index + size]
                    window = candidate_tokens[index : index + size]
                    if not token_window_is_plausible(window, stopwords):
                        continue
                    if not spacy_window_is_plausible(token_window, has_pos):
                        continue
                    surface = clean_candidate_term(text[window[0].start_char : window[-1].end_char])
                    if not candidate_surface_is_clean(surface):
                        continue
                    candidates.append(
                        make_target_term(
                            target_term=surface,
                            category="other",
                            source="spacy_ngram",
                            confidence=spacy_ngram_confidence(
                                token_window,
                                language_code,
                                has_pos=has_pos,
                            ),
                            reason="spaCy token n-gram candidate from target reference.",
                        )
                    )
        return candidates


class MSPLADETerminologyExtractor:
    """SPLADE/mSPLADE sparse-activation candidate extractor for exact target spans."""

    def __init__(
        self,
        model_name: str = DEFAULT_MSPLADE_MODEL,
        max_activated_tokens: int = 128,
        max_ngram_tokens: int = 5,
    ) -> None:
        self.model_name = model_name
        self.max_activated_tokens = max_activated_tokens
        self.max_ngram_tokens = max_ngram_tokens
        self._model_bundle: tuple[Any, Any, Any, str] | None = None

    def extract(
        self,
        text: str,
        max_terms: int,
        target_language: str = "",
    ) -> list[DatasetTerminologyTerm]:
        del target_language
        weights = self.activated_token_weights(text)
        if not weights:
            return []
        tokens = candidate_token_spans(text)
        if not tokens:
            return []

        candidates = []
        for size in range(1, self.max_ngram_tokens + 1):
            for index in range(0, max(len(tokens) - size + 1, 0)):
                window = tokens[index : index + size]
                if not token_window_is_plausible(window, set(_BOUNDARY_STOPWORDS)):
                    continue
                score = msplade_window_score(window, weights)
                if score <= 0:
                    continue
                surface = clean_candidate_term(text[window[0].start_char : window[-1].end_char])
                if not candidate_surface_is_clean(surface):
                    continue
                candidates.append(
                    make_target_term(
                        target_term=surface,
                        category="other",
                        source="msplade_sparse",
                        confidence=msplade_confidence(window, score),
                        reason="SPLADE sparse lexical activation candidate from target reference.",
                    )
                )
        return deduplicate_terms(candidates)[:max_terms]

    def activated_token_weights(self, text: str) -> dict[str, float]:
        bundle = self.load_model_bundle()
        if bundle is None:
            return {}
        tokenizer, model, torch, device = bundle
        try:
            encoded = tokenizer(
                text[:4000],
                return_tensors="pt",
                truncation=True,
                max_length=512,
            )
            encoded = {key: value.to(device) for key, value in encoded.items()}
            with torch.no_grad():
                outputs = model(**encoded)
            logits = outputs.logits
            attention_mask = encoded["attention_mask"].unsqueeze(-1)
            weighted_logits = torch.log1p(torch.relu(logits)) * attention_mask
            sparse_vector = torch.max(weighted_logits, dim=1).values
            sparse_vector = sparse_vector.squeeze(0)
            positive_indices = torch.nonzero(sparse_vector > 0, as_tuple=False).flatten()
            if positive_indices.numel() == 0:
                return {}
            top_k = min(self.max_activated_tokens, int(positive_indices.numel()))
            values, indices = torch.topk(sparse_vector, k=top_k)
        except Exception:
            return {}

        weights: dict[str, float] = {}
        for token_id, value in zip(indices.tolist(), values.tolist(), strict=False):
            raw_token = tokenizer.convert_ids_to_tokens(int(token_id))
            token = clean_sparse_vocabulary_token(raw_token)
            if not token:
                continue
            weights[token.casefold()] = max(weights.get(token.casefold(), 0.0), float(value))
        return weights

    def load_model_bundle(self) -> tuple[Any, Any, Any, str] | None:
        if self._model_bundle is not None:
            return self._model_bundle
        try:
            import torch
            from transformers import AutoModelForMaskedLM, AutoTokenizer
        except ImportError:
            return None
        try:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            model = AutoModelForMaskedLM.from_pretrained(self.model_name)
            model.to(device)
            model.eval()
        except Exception:
            return None
        self._model_bundle = (tokenizer, model, torch, device)
        return self._model_bundle


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
        use_chebi: bool = False,
        use_chembl: bool = False,
        use_mesh: bool = False,
        use_nci: bool = False,
        use_agrovoc: bool = False,
        use_unterm: bool = False,
        cache_path: Path | None = None,
        iate_client: IATEClient | None = None,
        wikidata_client: WikidataClient | None = None,
        pubchem_client: PubChemClient | None = None,
        chebi_client: ChEBIClient | None = None,
        chembl_client: ChEMBLClient | None = None,
        mesh_client: MeSHClient | None = None,
        nci_client: NCIThesaurusClient | None = None,
        agrovoc_client: AGROVOCClient | None = None,
        unterm_client: UNTERMClient | None = None,
        llm_extractor: LLMTargetCandidateExtractor | None = None,
        extractor: TargetTerminologyExtractor | None = None,
        extractors: tuple[Any, ...] | None = None,
        use_stanza_extractor: bool = True,
        use_nobi_extractor: bool = False,
        nobi_model: str = "tthhanh/xlm-ate-nobi-en-nes",
        use_nltk_extractor: bool = False,
        use_msplade_extractor: bool = False,
        msplade_model: str = DEFAULT_MSPLADE_MODEL,
        use_spacy_extractor: bool = False,
        spacy_model: str = DEFAULT_SPACY_MODEL,
    ) -> None:
        self.model = model
        self.max_terms = max_terms
        self.use_llm = use_llm
        self.use_iate = use_iate
        self.use_wikidata = use_wikidata
        self.use_pubchem = use_pubchem
        self.use_chebi = use_chebi
        self.use_chembl = use_chembl
        self.use_mesh = use_mesh
        self.use_nci = use_nci
        self.use_agrovoc = use_agrovoc
        self.use_unterm = use_unterm
        self.cache_path = cache_path
        self.iate_client = iate_client or (IATEClient() if use_iate else None)
        self.wikidata_client = wikidata_client or (WikidataClient() if use_wikidata else None)
        self.pubchem_client = pubchem_client or (PubChemClient() if use_pubchem else None)
        self.chebi_client = chebi_client or (ChEBIClient() if use_chebi else None)
        self.chembl_client = chembl_client or (ChEMBLClient() if use_chembl else None)
        self.mesh_client = mesh_client or (MeSHClient() if use_mesh else None)
        self.nci_client = nci_client or (NCIThesaurusClient() if use_nci else None)
        self.agrovoc_client = agrovoc_client or (AGROVOCClient() if use_agrovoc else None)
        self.unterm_client = unterm_client or (UNTERMClient() if use_unterm else None)
        self.llm_extractor = llm_extractor or (
            LLMTargetCandidateExtractor(client=client, model=model)
            if use_llm and client is not None
            else None
        )
        if extractors is not None:
            self.extractors = list(extractors)
        else:
            self.extractors = []
            if use_stanza_extractor:
                self.extractors.append(extractor or TargetTerminologyExtractor())
            elif extractor is not None:
                self.extractors.append(extractor)
        if use_nobi_extractor:
            self.extractors.append(XLMRNOBITerminologyExtractor(model_name=nobi_model))
        if use_nltk_extractor:
            self.extractors.append(NLTKTerminologyExtractor())
        if use_spacy_extractor:
            self.extractors.append(SpaCyTerminologyExtractor(model_name=spacy_model))
        if use_msplade_extractor:
            self.extractors.append(MSPLADETerminologyExtractor(model_name=msplade_model))
        self.extractor = self.extractors[0] if self.extractors else TargetTerminologyExtractor()
        self.extractor_names = tuple(type(extractor).__name__ for extractor in self.extractors)
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
            use_chebi=self.use_chebi,
            use_chembl=self.use_chembl,
            use_mesh=self.use_mesh,
            use_nci=self.use_nci,
            use_agrovoc=self.use_agrovoc,
            use_unterm=self.use_unterm,
            extractor_names=self.extractor_names,
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
        for extractor in self.extractors:
            terms.extend(
                extractor.extract(
                    reference_text,
                    max_terms=self.max_terms,
                    target_language=target_language,
                )
            )
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

        if self.chebi_client:
            synonyms = self.chebi_client.lookup_synonyms(target_term)
            if synonyms:
                candidates["chebi"] = synonyms
                source_parts.append("chebi")

        if self.chembl_client:
            synonyms = self.chembl_client.lookup_synonyms(target_term)
            if synonyms:
                candidates["chembl"] = synonyms
                source_parts.append("chembl")

        if self.mesh_client:
            synonyms = self.mesh_client.lookup_synonyms(target_term)
            if synonyms:
                candidates["mesh"] = synonyms
                source_parts.append("mesh")

        if self.nci_client:
            synonyms = self.nci_client.lookup_synonyms(target_term)
            if synonyms:
                candidates["nci"] = synonyms
                source_parts.append("nci")

        if self.agrovoc_client:
            language_code = wikidata_language_code(target_language) or iate_language_code(
                target_language,
            )
            synonyms = self.agrovoc_client.lookup_synonyms(target_term, language_code)
            if synonyms:
                candidates["agrovoc"] = synonyms
                source_parts.append("agrovoc")

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

        if self.unterm_client:
            language_code = iate_language_code(target_language)
            if language_code and self.unterm_client.term_exists(target_term, language_code):
                candidates["unterm"] = [target_term]
                source_parts.append("unterm")

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


def terminology_language_code(language: str) -> str:
    language = language.strip()
    if not language:
        return ""
    return iate_language_code(language) or language.lower()


def dependency_span_words(head: Any, words: list[Any]) -> list[Any]:
    selected = [head]
    for word in words:
        if word.head == head.id and dependency_relation(word.deprel) in _UD_EXPANSION_DEPRELS:
            selected.append(word)
            selected.extend(
                child
                for child in words
                if child.head == word.id
                and dependency_relation(child.deprel) in _UD_EXPANSION_DEPRELS
            )
    return sorted({word.id: word for word in selected}.values(), key=lambda word: word.id)


def dependency_relation(deprel: str) -> str:
    return deprel.split(":", 1)[0]


def make_stanza_terms(
    text: str,
    words: list[Any],
    source: str,
    confidence: float,
    reason: str,
) -> list[DatasetTerminologyTerm]:
    if not words:
        return []
    words = sorted(words, key=lambda word: word.id)
    if len(words) > _MAX_STANZA_TERM_TOKENS:
        return []
    if words[0].upos in _UD_BLOCKED_BOUNDARY_UPOS or words[-1].upos in _UD_BLOCKED_BOUNDARY_UPOS:
        return []
    offsets = [
        (word.start_char, word.end_char)
        for word in words
        if word.start_char is not None and word.end_char is not None
    ]
    if not offsets:
        return []
    start_char = min(start for start, _ in offsets)
    end_char = max(end for _, end in offsets)
    target_term = clean_candidate_term(text[start_char:end_char])
    if not target_term:
        return []
    if not stanza_candidate_surface_is_clean(target_term):
        return []
    return [
        make_target_term(
            target_term=target_term,
            category="other",
            source=source,
            confidence=stanza_span_confidence(words, confidence),
            reason=reason,
        )
    ]


def stanza_ngram_is_plausible(words: list[Any]) -> bool:
    if not words:
        return False
    if words[0].upos in _UD_BLOCKED_BOUNDARY_UPOS or words[-1].upos in _UD_BLOCKED_BOUNDARY_UPOS:
        return False
    if any(word.upos in {"CCONJ", "SCONJ"} for word in words):
        return False
    if any(dependency_relation(word.deprel) == "punct" for word in words):
        return False
    if any(word.upos in {"VERB", "AUX"} for word in words):
        return False
    return any(word.upos in _UD_CONTENT_UPOS for word in words)


def stanza_candidate_confidence(words: list[Any]) -> float:
    content_words = sum(1 for word in words if word.upos in _UD_CONTENT_UPOS)
    return min(0.7, 0.45 + 0.05 * content_words)


def stanza_candidate_surface_is_clean(surface: str) -> bool:
    if _SPAN_SEPARATOR_RE.search(surface):
        return False
    if _LEGAL_CITATION_RE.search(surface):
        return False
    if _DATE_FRAGMENT_RE.search(surface):
        return False
    if surface.isdecimal():
        return False
    if _MONTH_NAME_RE.match(surface):
        return False
    if len(surface) <= 3 and surface.isupper():
        return False
    return True


def stanza_span_confidence(words: list[Any], base_confidence: float) -> float:
    token_count = len(words)
    if token_count == 1:
        surface = str(getattr(words[0], "text", "") or "")
        base_confidence = 0.6 if "-" in surface and len(surface) > 4 else 0.5
    confidence = base_confidence - max(0, token_count - 3) * 0.04
    if token_count > 1 and any(word.upos == "PROPN" for word in words):
        confidence += 0.03
    return max(0.4, min(0.78, confidence))


def make_proper_name_terms(text: str, words: list[Any]) -> list[DatasetTerminologyTerm]:
    if len(words) < 2:
        return []
    return make_stanza_terms(
        text=text,
        words=words,
        source="stanza_ud_proper_name",
        confidence=0.7,
        reason="Proper-name sequence from target reference.",
    )


def decode_nobi_terms(text: str, outputs: list[dict[str, Any]]) -> list[DatasetTerminologyTerm]:
    terms = []
    current: list[dict[str, Any]] = []

    def flush_current() -> None:
        if not current:
            return
        start_char = int(current[0]["start"])
        end_char = int(current[-1]["end"])
        surface = clean_candidate_term(text[start_char:end_char])
        if surface and candidate_has_word_boundaries(text, start_char, end_char):
            if stanza_candidate_surface_is_clean(surface):
                score = sum(parse_confidence(token.get("score")) for token in current) / len(
                    current
                )
                terms.append(
                    make_target_term(
                        target_term=surface,
                        category="other",
                        source="xlmr_nobi",
                        confidence=score,
                        reason="XLM-R/NOBI token-classification exact target span.",
                    )
                )
        current.clear()

    for output in outputs:
        raw_label = str(output.get("entity") or output.get("entity_group") or "")
        label = _NOBI_LABEL_MAP.get(raw_label, raw_label).upper()
        is_subword_continuation = (
            current
            and not str(output.get("word", "")).startswith("▁")
            and int(output.get("start", -1)) == int(current[-1].get("end", -2))
        )
        if label == "O":
            flush_current()
            continue
        if label in {"B", "BN"} and current and not is_subword_continuation:
            flush_current()
        current.append(output)
    flush_current()
    return terms


def candidate_has_word_boundaries(text: str, start_char: int, end_char: int) -> bool:
    left_ok = start_char <= 0 or not text[start_char - 1].isalnum()
    right_ok = end_char >= len(text) or not text[end_char].isalnum()
    return left_ok and right_ok


def candidate_token_spans(text: str) -> list[CandidateToken]:
    tokens = []
    for match in _CANDIDATE_TOKEN_RE.finditer(text):
        surface = match.group(0)
        if not any(character.isalpha() for character in surface):
            continue
        tokens.append(
            CandidateToken(
                surface=surface,
                start_char=match.start(),
                end_char=match.end(),
            )
        )
    return tokens


def token_window_is_plausible(tokens: list[CandidateToken], stopwords: set[str]) -> bool:
    if not tokens:
        return False
    first = normalize_candidate_token(tokens[0].surface)
    last = normalize_candidate_token(tokens[-1].surface)
    if not first or not last or first in stopwords or last in stopwords:
        return False
    if len(tokens) == 1:
        surface = tokens[0].surface
        if len(surface) < 4 and not surface.isupper():
            return False
    normalized_tokens = [normalize_candidate_token(token.surface) for token in tokens]
    if all(token in stopwords for token in normalized_tokens if token):
        return False
    return True


def candidate_surface_is_clean(surface: str) -> bool:
    if not surface:
        return False
    if not stanza_candidate_surface_is_clean(surface):
        return False
    if _FORMULA_OR_IDENTIFIER_RE.match(surface):
        return True
    if len(surface) < 4:
        return False
    if not any(character.isalpha() for character in surface):
        return False
    return True


def nltk_ngram_confidence(tokens: list[CandidateToken]) -> float:
    token_count = len(tokens)
    confidence = 0.46 + min(token_count, 5) * 0.04
    if token_count > 1:
        confidence += 0.04
    if any(token.surface[:1].isupper() for token in tokens):
        confidence += 0.02
    return min(0.72, confidence)


def msplade_window_score(
    tokens: list[CandidateToken],
    sparse_token_weights: dict[str, float],
) -> float:
    weights = [
        sparse_token_weights.get(normalize_candidate_token(token.surface), 0.0)
        for token in tokens
    ]
    if not any(weight > 0 for weight in weights):
        return 0.0
    return max(weights) + sum(weights) / max(len(tokens), 1)


def msplade_confidence(tokens: list[CandidateToken], score: float) -> float:
    token_count = len(tokens)
    confidence = 0.48 + min(score, 5.0) * 0.03
    if token_count > 1:
        confidence += 0.07
    return min(0.78, confidence)


def spacy_language_code(language: str) -> str:
    language_code = terminology_language_code(language).lower()
    return _SPACY_LANGUAGE_ALIASES.get(language_code, language_code) or "xx"


def spacy_doc_has_pos(doc: Any) -> bool:
    try:
        return bool(doc.has_annotation("POS"))
    except Exception:
        return False


def spacy_doc_has_sentences(doc: Any) -> bool:
    try:
        return bool(doc.has_annotation("SENT_START"))
    except Exception:
        return False


def spacy_token_is_candidate(token: Any) -> bool:
    surface = str(token.text or "").strip()
    if not surface:
        return False
    if getattr(token, "is_space", False) or getattr(token, "is_punct", False):
        return False
    if getattr(token, "is_stop", False):
        return False
    if getattr(token, "like_url", False) or getattr(token, "like_email", False):
        return False
    if not any(character.isalpha() for character in surface):
        return False
    return True


def spacy_span_has_content(span: Any) -> bool:
    return any(spacy_token_is_candidate(token) for token in span)


def trim_spacy_span(span: Any) -> Any:
    start = 0
    end = len(span)
    while start < end and not spacy_token_is_candidate(span[start]):
        start += 1
    while end > start and not spacy_token_is_candidate(span[end - 1]):
        end -= 1
    return span[start:end]


def spacy_window_is_plausible(tokens: list[Any], has_pos: bool) -> bool:
    if not tokens:
        return False
    first = normalize_candidate_token(str(tokens[0].lemma_ or tokens[0].text))
    last = normalize_candidate_token(str(tokens[-1].lemma_ or tokens[-1].text))
    if first in _SPACY_BLOCKED_BOUNDARY_LEMMAS or last in _SPACY_BLOCKED_BOUNDARY_LEMMAS:
        return False
    if has_pos:
        pos_tags = {str(token.pos_) for token in tokens}
        if pos_tags & {"AUX", "CCONJ", "DET", "PRON", "SCONJ", "VERB"}:
            return False
        if not (pos_tags & {"ADJ", "NOUN", "NUM", "PROPN", "SYM", "X"}):
            return False
        if len(tokens) == 1 and str(tokens[0].pos_) not in {"NOUN", "PROPN", "SYM", "X"}:
            return False
    return True


def spacy_ngram_confidence(tokens: list[Any], language_code: str, has_pos: bool) -> float:
    token_count = len(tokens)
    confidence = 0.48 + min(token_count, 5) * 0.04
    if has_pos:
        confidence += 0.08
    if token_count > 1:
        confidence += 0.04
    if any(str(getattr(token, "pos_", "")) == "PROPN" for token in tokens):
        confidence += 0.03
    if language_code in {"ja", "zh"} and token_count == 1:
        confidence += 0.04
    return min(0.76, confidence)


def normalize_candidate_token(token: str) -> str:
    return clean_candidate_term(token).casefold()


def clean_sparse_vocabulary_token(token: str) -> str:
    if not token:
        return ""
    if token.startswith("##"):
        return ""
    token = token.removeprefix("▁").removeprefix("Ġ").strip()
    token = clean_candidate_term(token)
    if len(token) < 3:
        return ""
    if not any(character.isalpha() for character in token):
        return ""
    return token


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
        if existing is None:
            by_key[key] = term
        else:
            by_key[key] = merge_duplicate_dataset_terms(existing, term)
    return sorted(
        by_key.values(),
        key=lambda term: (term.confidence, len(term.target_terms[0])),
        reverse=True,
    )


def merge_duplicate_dataset_terms(
    left: DatasetTerminologyTerm,
    right: DatasetTerminologyTerm,
) -> DatasetTerminologyTerm:
    base = left if left.confidence >= right.confidence else right
    source = "+".join(merge_source_tags(left.source, right.source))
    verified_by = merge_unique_strings(left.verified_by, right.verified_by)
    candidates = merge_external_candidate_maps(left.candidates, right.candidates)
    term_group = merged_term_group(left, right, verified_by)
    decision = "preserve" if "preserve" in {left.decision, right.decision} else base.decision
    return replace_dataset_term(
        base,
        target_terms=merge_unique_strings(base.target_terms, left.target_terms, right.target_terms),
        reference_candidates=merge_unique_strings(
            base.reference_candidates,
            left.reference_candidates,
            right.reference_candidates,
        ),
        source=source,
        term_group=term_group,
        verified_by=verified_by,
        confidence=max(left.confidence, right.confidence),
        decision=decision,
        candidates=candidates,
    )


def merge_source_tags(*sources: str) -> tuple[str, ...]:
    tags: list[str] = []
    for source in sources:
        tags.extend(part.strip() for part in source.split("+") if part.strip())
    return merge_unique_strings(tags)


def merge_unique_strings(*groups: Iterable[str]) -> tuple[str, ...]:
    merged: list[str] = []
    seen: set[str] = set()
    for group in groups:
        for value in group:
            stripped = str(value).strip()
            if not stripped:
                continue
            key = stripped.casefold()
            if key in seen:
                continue
            seen.add(key)
            merged.append(stripped)
    return tuple(merged)


def merge_external_candidate_maps(
    left: dict[str, list[str]],
    right: dict[str, list[str]],
) -> dict[str, list[str]]:
    merged: dict[str, list[str]] = {}
    for source, terms in [*left.items(), *right.items()]:
        existing = merged.get(source, [])
        merged[source] = list(merge_unique_strings(existing, terms))
    return merged


def merged_term_group(
    left: DatasetTerminologyTerm,
    right: DatasetTerminologyTerm,
    verified_by: tuple[str, ...],
) -> str:
    if verified_by:
        return "verified"
    if "llm" in {left.term_group, right.term_group}:
        return "llm"
    return left.term_group if left.confidence >= right.confidence else right.term_group


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
    use_chebi: bool = False,
    use_chembl: bool = False,
    use_mesh: bool = False,
    use_nci: bool = False,
    use_agrovoc: bool = False,
    use_unterm: bool = False,
    extractor_names: tuple[str, ...] = (),
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
        "use_chebi": use_chebi,
        "use_chembl": use_chembl,
        "use_mesh": use_mesh,
        "use_nci": use_nci,
        "use_agrovoc": use_agrovoc,
        "use_unterm": use_unterm,
        "extractor_names": extractor_names,
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
        "pipeline_version": "legal-target-llm-candidate-v4",
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
