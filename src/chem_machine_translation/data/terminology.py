from __future__ import annotations

import hashlib
import json
import re
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from openai import OpenAI

from chem_machine_translation.translation.iate import IATEClient, iate_language_code
from chem_machine_translation.translation.wikidata import WikidataClient, wikidata_language_code

_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)
_FORMULA_OR_IDENTIFIER_RE = re.compile(
    r"^(?:[A-Z][a-z]?\d*)+$|^[A-Z]{1,6}-?\d[\w.-]*$|^\d+(?:[.,]\d+)?\s?[A-Za-z/%]+$"
)
_COMPACT_NUMERIC_UNIT_RE = re.compile(
    r"^\d+(?:[.,]\d+)?(?:\s*(?:-|to|–|—)\s*\d+(?:[.,]\d+)?)?\s*"
    r"(?:%|°C|K|ppm|ppb|mol%|wt%|mg|g|kg|mL|L|cm2|cm3|mm|cm|m|nm|µm|um)(?:\s+or\s+less)?$",
    re.IGNORECASE,
)
_SEQUENCE_IDENTIFIER_RE = re.compile(
    r"^(?:SEQ\s+ID\s+NO:\s*\d+|CAS\s+RN\s*[:\s]?\d[\d-]+)$",
    re.IGNORECASE,
)
_DEFAULT_CONFIDENCE_THRESHOLD = 0.85
_TERMINOLOGY_PIPELINE_VERSION = "reference-first-v4"

DATASET_TERM_EXTRACTOR_SYSTEM_PROMPT = """You identify terminology for chemistry and patent
machine-translation evaluation datasets.

The source text may be in any language. Extract exact source-language spans that are technical
enough to evaluate for terminology preservation:
- chemical names, formulas, materials, catalysts, reagents, solvents, proteins, and abbreviations;
- reaction/process terms, analytical methods, property names, and domain-specific phrases;
- quantities, units, conditions, hazard/regulatory phrases, and identifiers when important.

Be strict. Extract only domain-critical terms whose translation could change scientific, legal, or
patent meaning. Every extracted term must be useful as a terminology metric item, not merely a
translated phrase.

Do not extract generic patent scaffolding, common everyday objects, broad field labels, grammatical
fragments, full clauses, or terms that are only meaningful because of surrounding sentence context.
Prefer the smallest exact span that carries the technical meaning. For quantities and conditions,
extract the compact measurement or condition itself rather than the surrounding clause.

Only extract a common word when it is part of a precise source-language technical expression. If
a term could appear unchanged in a non-technical document without changing domain meaning, leave it
out.

Do not translate terms. Do not invent terms. Prefer exact source-language spans from the text.
Return only valid JSON with this shape:
{
  "terms": [
    {
      "source_term": "exact source span",
      "category": "chemical|material|process|method|unit|identifier|hazard|other",
      "reason": "short reason this term should be measured"
    }
  ]
}
"""

DATASET_REFERENCE_CANDIDATE_SYSTEM_PROMPT = """You find target-language terminology spans in a
reference translation for chemistry and patent machine-translation evaluation datasets.

The source and target texts may be any language pair. You receive source-language terminology
terms, the full source text, and the target-language reference translation. For each source term,
find exact target-language span(s) from the reference translation that correspond to that source
term.

Use only spans that appear in the target reference. Do not use external terminology sources. Do not
invent canonical translations that are not in the reference. If the reference paraphrases the
concept and no compact terminology span is present, return an empty list for that source term.

Return only valid JSON with this shape:
{
  "terms": [
    {
      "source_term": "exact source term from input",
      "reference_candidates": ["exact target span from reference"],
      "confidence": 0.0,
      "reason": "short reason"
    }
  ]
}
"""

DATASET_TERM_REFINER_SYSTEM_PROMPT = """You refine terminology mappings for chemistry and patent
machine-translation evaluation datasets.

The source and target texts may be any language pair. You receive the source-language text, the
target-language reference translation, reference-derived candidates, and external IATE/Wikidata
candidates. Keep only terms that are high-confidence and useful for automatic terminology accuracy
or prompt-time terminology guidance.

Reference candidates are the main evidence for benchmark terminology because they are spans from the
target reference. External candidates are validation/canonicalization evidence only. Do not let an
external candidate override a correct reference candidate. If reference and external candidates both
look valid, keep both as variants.

Drop aggressively when the source term is generic, not technical, too broad, a sentence fragment,
a full clause, or only useful as normal translated prose rather than terminology. This judgment
must be language-neutral and based on the source/reference context, not on a fixed list of words.

For each input term, choose exactly one decision:
- keep_reference: reference candidate(s) are correct and should be the final target term(s);
- keep_external: external candidate(s) are correct and reference candidate(s) are absent/noisy;
- keep_both: reference and external candidate(s) are both valid variants;
- update: candidates are close but need contextual wording;
- preserve: the source term should be copied unchanged;
- drop: the term is generic, unrelated, or too uncertain for evaluation.

Return only valid JSON with this shape:
{
  "terms": [
    {
      "source_term": "exact source term from input",
      "decision": "keep_reference|keep_external|keep_both|update|preserve|drop",
      "target_terms": ["target term"],
      "confidence": 0.0,
      "reason": "short reason"
    }
  ]
}
"""


@dataclass(frozen=True)
class DatasetTerminologyTerm:
    source_term: str
    target_terms: tuple[str, ...] = ()
    reference_candidates: tuple[str, ...] = ()
    category: str = "other"
    source: str = "llm"
    confidence: float = 0.0
    decision: str = ""
    reason: str = ""
    candidates: dict[str, list[str]] = field(default_factory=dict)

    def to_json(self) -> dict[str, Any]:
        return {
            "source_term": self.source_term,
            "target_terms": list(self.target_terms),
            "reference_candidates": list(self.reference_candidates),
            "category": self.category,
            "source": self.source,
            "confidence": self.confidence,
            "decision": self.decision,
            "reason": self.reason,
            "external_candidates": self.candidates,
            "candidates": self.candidates,
        }


class DatasetTerminologyGenerator:
    """Generates structured terminology mappings for benchmark manifests."""

    def __init__(
        self,
        client: OpenAI | None = None,
        model: str = "gpt-4.1-mini",
        max_terms: int = 20,
        use_iate: bool = False,
        use_wikidata: bool = False,
        refine_terms: bool = False,
        confidence_threshold: float = _DEFAULT_CONFIDENCE_THRESHOLD,
        cache_path: Path | None = None,
        iate_client: IATEClient | None = None,
        wikidata_client: WikidataClient | None = None,
    ) -> None:
        self.client = client
        self.model = model
        self.max_terms = max_terms
        self.use_iate = use_iate
        self.use_wikidata = use_wikidata
        self.refine_terms = refine_terms
        self.confidence_threshold = confidence_threshold
        self.cache_path = cache_path
        self.iate_client = iate_client or (IATEClient() if use_iate else None)
        self.wikidata_client = wikidata_client or (WikidataClient() if use_wikidata else None)
        self._cache = load_terminology_cache(cache_path)
        self._cache_lock = threading.Lock()

    def generate(
        self,
        source_text: str,
        target_language: str,
        reference_text: str = "",
        source_language: str = "English",
    ) -> list[DatasetTerminologyTerm]:
        cache_key = terminology_cache_key(
            source_text=source_text,
            reference_text=reference_text,
            source_language=source_language,
            target_language=target_language,
            model=self.model,
            max_terms=self.max_terms,
            use_iate=self.use_iate,
            use_wikidata=self.use_wikidata,
            refine_terms=self.refine_terms,
            confidence_threshold=self.confidence_threshold,
        )
        with self._cache_lock:
            cached_terms = self._cache.get(cache_key)
        if cached_terms is not None:
            return [dataset_term_from_json(term) for term in cached_terms]

        terms = self.extract_source_terms(
            source_text=source_text,
            source_language=source_language,
            target_language=target_language,
        )
        if reference_text:
            terms = self.extract_reference_candidates(
                terms=terms,
                source_text=source_text,
                reference_text=reference_text,
                source_language=source_language,
                target_language=target_language,
            )
        terms = [
            self.add_external_candidates(
                term=term,
                source_language=source_language,
                target_language=target_language,
            )
            for term in terms
        ]
        if self.refine_terms:
            terms = self.refine_dataset_terms(
                terms=terms,
                source_text=source_text,
                reference_text=reference_text,
                source_language=source_language,
                target_language=target_language,
            )
        else:
            terms = select_dataset_terms(terms, confidence_threshold=0.0, max_terms=self.max_terms)

        with self._cache_lock:
            if cache_key not in self._cache:
                self._cache[cache_key] = [term.to_json() for term in terms]
                append_terminology_cache(
                    cache_path=self.cache_path,
                    cache_key=cache_key,
                    terms=terms,
                )
        return terms

    def extract_source_terms(
        self,
        source_text: str,
        source_language: str,
        target_language: str,
    ) -> list[DatasetTerminologyTerm]:
        if self.client is None:
            return []

        response = self.client.responses.create(
            model=self.model,
            temperature=0.0,
            input=[
                {"role": "system", "content": DATASET_TERM_EXTRACTOR_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Find up to {self.max_terms} strict technical terminology items in this "
                        f"{source_language} chemistry patent text before pairing with "
                        f"{target_language}.\n\nSource text:\n{source_text}"
                    ),
                },
            ],
        )
        return parse_dataset_extracted_terms(response.output_text)

    def extract_reference_candidates(
        self,
        terms: list[DatasetTerminologyTerm],
        source_text: str,
        reference_text: str,
        source_language: str,
        target_language: str,
    ) -> list[DatasetTerminologyTerm]:
        if self.client is None or not terms:
            return terms

        response = self.client.responses.create(
            model=self.model,
            temperature=0.0,
            input=[
                {"role": "system", "content": DATASET_REFERENCE_CANDIDATE_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Find reference terminology candidates for {source_language} to "
                        f"{target_language}.\n\n"
                        f"Source text:\n{source_text}\n\n"
                        f"Target reference:\n{reference_text}\n\n"
                        "Source terms:\n"
                        f"{json.dumps([term.to_json() for term in terms], ensure_ascii=False)}"
                    ),
                },
            ],
        )
        return parse_reference_candidate_terms(response.output_text, terms)

    def add_target_candidates(
        self,
        term: DatasetTerminologyTerm,
        source_language: str,
        target_language: str,
    ) -> DatasetTerminologyTerm:
        return self.add_external_candidates(term, source_language, target_language)

    def add_external_candidates(
        self,
        term: DatasetTerminologyTerm,
        source_language: str,
        target_language: str,
    ) -> DatasetTerminologyTerm:
        if should_preserve_dataset_term(term.source_term, term.category):
            return replace_dataset_term(
                term,
                target_terms=(term.source_term,),
                reference_candidates=term.reference_candidates,
                source="preserve",
                confidence=1.0,
                decision="preserve",
            )

        candidates: dict[str, list[str]] = {}
        source_parts = ["reference"] if term.reference_candidates else ["llm_only"]

        if self.iate_client:
            source_code = iate_language_code(source_language)
            target_code = iate_language_code(target_language)
            if source_code and target_code:
                translation = self.iate_client.translate_term(
                    source_term=term.source_term,
                    source_language_code=source_code,
                    target_language_code=target_code,
                )
                if translation:
                    candidates["iate"] = [translation.target_label]
                    source_parts.append("iate")

        if self.wikidata_client and "iate" not in candidates:
            source_code = wikidata_language_code(source_language)
            target_code = wikidata_language_code(target_language)
            if source_code and target_code:
                translation = self.wikidata_client.translate_term(
                    source_term=term.source_term,
                    source_language_code=source_code,
                    target_language_code=target_code,
                )
                if translation:
                    candidates["wikidata"] = [translation.target_label]
                    source_parts.append("wikidata")

        external_terms = flatten_candidate_terms(candidates)
        return replace_dataset_term(
            term,
            target_terms=term.reference_candidates or external_terms,
            source="+".join(source_parts),
            confidence=0.85 if term.reference_candidates else 0.75 if external_terms else 0.5,
            candidates=candidates,
        )

    def refine_dataset_terms(
        self,
        terms: list[DatasetTerminologyTerm],
        source_text: str,
        reference_text: str,
        source_language: str,
        target_language: str,
    ) -> list[DatasetTerminologyTerm]:
        if self.client is None or not terms:
            return terms

        response = self.client.responses.create(
            model=self.model,
            temperature=0.0,
            input=[
                {"role": "system", "content": DATASET_TERM_REFINER_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Refine terminology mappings for {source_language} to "
                        f"{target_language}.\n\n"
                        f"Source text:\n{source_text}\n\n"
                        f"Reference translation:\n{reference_text}\n\n"
                        "Candidates:\n"
                        f"{json.dumps([term.to_json() for term in terms], ensure_ascii=False)}"
                    ),
                },
            ],
        )
        return parse_refined_dataset_terms(
            response.output_text,
            original_terms=terms,
            confidence_threshold=self.confidence_threshold,
            max_terms=self.max_terms,
        )


def parse_dataset_extracted_terms(text: str) -> list[DatasetTerminologyTerm]:
    match = _JSON_OBJECT_RE.search(text)
    try:
        payload = json.loads(match.group(0) if match else text)
    except json.JSONDecodeError:
        return []

    terms = []
    for raw_term in payload.get("terms", []):
        if not isinstance(raw_term, dict):
            continue
        source_term = str(raw_term.get("source_term", "")).strip()
        if not source_term:
            continue
        terms.append(
            DatasetTerminologyTerm(
                source_term=source_term,
                category=str(raw_term.get("category", "other")).strip() or "other",
                reason=str(raw_term.get("reason", "")).strip(),
                source="llm",
            )
        )
    return terms


def parse_reference_candidate_terms(
    text: str,
    original_terms: list[DatasetTerminologyTerm],
) -> list[DatasetTerminologyTerm]:
    match = _JSON_OBJECT_RE.search(text)
    try:
        payload = json.loads(match.group(0) if match else text)
    except json.JSONDecodeError:
        return original_terms

    reference_by_source = {
        str(raw_term.get("source_term", "")).strip(): raw_term
        for raw_term in payload.get("terms", [])
        if isinstance(raw_term, dict) and str(raw_term.get("source_term", "")).strip()
    }
    updated_terms = []
    for term in original_terms:
        raw_reference = reference_by_source.get(term.source_term)
        if raw_reference is None:
            updated_terms.append(term)
            continue
        raw_candidates = raw_reference.get("reference_candidates", [])
        if not isinstance(raw_candidates, list):
            raw_candidates = []
        reference_candidates = tuple(
            str(candidate).strip()
            for candidate in raw_candidates
            if str(candidate).strip()
        )
        updated_terms.append(
            replace_dataset_term(
                term,
                target_terms=reference_candidates,
                reference_candidates=reference_candidates,
                confidence=max(term.confidence, parse_confidence(raw_reference.get("confidence"))),
                reason=str(raw_reference.get("reason", "")).strip() or term.reason,
                source="reference" if reference_candidates else term.source,
            )
        )
    return updated_terms


def parse_refined_dataset_terms(
    text: str,
    original_terms: list[DatasetTerminologyTerm],
    confidence_threshold: float = _DEFAULT_CONFIDENCE_THRESHOLD,
    max_terms: int = 20,
) -> list[DatasetTerminologyTerm]:
    match = _JSON_OBJECT_RE.search(text)
    try:
        payload = json.loads(match.group(0) if match else text)
    except json.JSONDecodeError:
        return select_dataset_terms(
            original_terms,
            confidence_threshold=confidence_threshold,
            max_terms=max_terms,
        )

    refined_by_source = {
        str(raw_term.get("source_term", "")).strip(): raw_term
        for raw_term in payload.get("terms", [])
        if isinstance(raw_term, dict) and str(raw_term.get("source_term", "")).strip()
    }

    refined_terms = []
    for term in original_terms:
        raw_refined = refined_by_source.get(term.source_term)
        if raw_refined is None:
            refined_terms.append(
                replace_dataset_term(
                    term,
                    decision=term.decision or "llm_only",
                    confidence=term.confidence,
                    reason=term.reason or "No refinement decision returned for this LLM-only term.",
                )
            )
            continue
        decision = str(raw_refined.get("decision", "")).strip().lower()
        valid_decisions = {
            "keep",
            "keep_reference",
            "keep_external",
            "keep_both",
            "replace",
            "update",
            "preserve",
            "drop",
        }
        if decision not in valid_decisions:
            decision = "drop"
        raw_target_terms = raw_refined.get("target_terms", [])
        if not isinstance(raw_target_terms, list):
            raw_target_terms = []
        target_terms = tuple(
            str(target_term).strip()
            for target_term in raw_target_terms
            if str(target_term).strip()
        )
        if decision in {"keep", "keep_reference"} and not target_terms:
            target_terms = term.reference_candidates or term.target_terms
        if decision == "keep_external" and not target_terms:
            target_terms = external_candidate_terms(term)
        if decision == "keep_both" and not target_terms:
            target_terms = tuple(
                dict.fromkeys([*term.reference_candidates, *external_candidate_terms(term)])
            )
        if decision == "preserve" and not target_terms:
            target_terms = (term.source_term,)
        if decision == "drop":
            target_terms = ()
        refined_terms.append(
            replace_dataset_term(
                term,
                target_terms=target_terms,
                confidence=parse_confidence(raw_refined.get("confidence")),
                decision=decision,
                reason=str(raw_refined.get("reason", "")).strip() or term.reason,
                source=f"{term.source}+refined" if "+refined" not in term.source else term.source,
            )
        )

    return select_dataset_terms(
        refined_terms,
        confidence_threshold=confidence_threshold,
        max_terms=max_terms,
    )


def select_dataset_terms(
    terms: list[DatasetTerminologyTerm],
    confidence_threshold: float,
    max_terms: int,
) -> list[DatasetTerminologyTerm]:
    accepted = [
        term
        for term in terms
        if term.decision != "drop"
        and (term.target_terms or term.decision == "preserve" or term.source == "llm_only")
        and (term.confidence >= confidence_threshold or term.source == "llm_only")
    ]
    accepted.sort(key=lambda term: (term.confidence, len(term.source_term.split())), reverse=True)
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
        confidence=term.confidence if confidence is None else confidence,
        decision=term.decision if decision is None else decision,
        reason=term.reason if reason is None else reason,
        candidates=term.candidates if candidates is None else candidates,
    )


def external_candidate_terms(term: DatasetTerminologyTerm) -> tuple[str, ...]:
    return flatten_candidate_terms(term.candidates)


def flatten_candidate_terms(candidates_by_source: dict[str, list[str]]) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            candidate
            for candidates in candidates_by_source.values()
            for candidate in candidates
            if candidate
        )
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


def terminology_cache_key(
    source_text: str,
    reference_text: str,
    source_language: str,
    target_language: str,
    model: str,
    max_terms: int,
    use_iate: bool,
    use_wikidata: bool,
    refine_terms: bool,
    confidence_threshold: float,
) -> str:
    payload = {
        "source_text": source_text,
        "reference_text": reference_text,
        "source_language": source_language,
        "target_language": target_language,
        "model": model,
        "max_terms": max_terms,
        "use_iate": use_iate,
        "use_wikidata": use_wikidata,
        "refine_terms": refine_terms,
        "confidence_threshold": confidence_threshold,
        "pipeline_version": _TERMINOLOGY_PIPELINE_VERSION,
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
