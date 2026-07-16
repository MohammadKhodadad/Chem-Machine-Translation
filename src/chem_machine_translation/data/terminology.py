from __future__ import annotations

import hashlib
import json
import re
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
_DEFAULT_CONFIDENCE_THRESHOLD = 0.85

DATASET_TERM_EXTRACTOR_SYSTEM_PROMPT = """You identify terminology for chemistry and patent
machine-translation evaluation datasets.

Extract exact English source spans that should be evaluated for terminology preservation:
- chemical names, formulas, materials, catalysts, reagents, solvents, proteins, and abbreviations;
- reaction/process terms, analytical methods, property names, and domain-specific phrases;
- quantities, units, conditions, hazard/regulatory phrases, and identifiers when important.

Do not translate terms. Do not invent terms. Prefer exact source spans from the text.
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

DATASET_TERM_REFINER_SYSTEM_PROMPT = """You refine terminology mappings for chemistry and patent
machine-translation evaluation datasets.

You receive an English source text, its reference translation, and terminology candidates. Keep only
terms that are high-confidence and useful for automatic terminology accuracy. Use the reference to
validate target terms, but do not invent arbitrary target strings from the reference.

For each input term, choose exactly one decision:
- keep: one or more candidate target terms are correct;
- replace: candidates are wrong, but a better target term is clear;
- update: candidates are close but need contextual wording;
- preserve: the source term should be copied unchanged;
- drop: the term is generic, unrelated, or too uncertain for evaluation.

Return only valid JSON with this shape:
{
  "terms": [
    {
      "source_term": "exact source term from input",
      "decision": "keep|replace|update|preserve|drop",
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
            "category": self.category,
            "source": self.source,
            "confidence": self.confidence,
            "decision": self.decision,
            "reason": self.reason,
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
        if cache_key in self._cache:
            return [dataset_term_from_json(term) for term in self._cache[cache_key]]

        terms = self.extract_source_terms(
            source_text=source_text,
            source_language=source_language,
            target_language=target_language,
        )
        terms = [
            self.add_target_candidates(
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

        self._cache[cache_key] = [term.to_json() for term in terms]
        append_terminology_cache(cache_path=self.cache_path, cache_key=cache_key, terms=terms)
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
                        f"Find up to {self.max_terms} terminology items in this "
                        f"{source_language} chemistry patent text before evaluation against "
                        f"{target_language}.\n\nSource text:\n{source_text}"
                    ),
                },
            ],
        )
        return parse_dataset_extracted_terms(response.output_text)

    def add_target_candidates(
        self,
        term: DatasetTerminologyTerm,
        source_language: str,
        target_language: str,
    ) -> DatasetTerminologyTerm:
        if should_preserve_dataset_term(term.source_term, term.category):
            return replace_dataset_term(
                term,
                target_terms=(term.source_term,),
                source="preserve",
                confidence=1.0,
                decision="preserve",
            )

        candidates: dict[str, list[str]] = {}
        target_terms: tuple[str, ...] = ()
        source = term.source

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
                    target_terms = (translation.target_label,)
                    source = "llm+iate"

        if self.wikidata_client and not target_terms:
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
                    target_terms = (translation.target_label,)
                    source = "llm+wikidata"

        return replace_dataset_term(
            term,
            target_terms=target_terms,
            source=source,
            confidence=0.75 if target_terms else term.confidence,
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
            refined_terms.append(replace_dataset_term(term, decision="drop", confidence=0.0))
            continue
        decision = str(raw_refined.get("decision", "")).strip().lower()
        if decision not in {"keep", "replace", "update", "preserve", "drop"}:
            decision = "drop"
        raw_target_terms = raw_refined.get("target_terms", [])
        if not isinstance(raw_target_terms, list):
            raw_target_terms = []
        target_terms = tuple(
            str(target_term).strip()
            for target_term in raw_target_terms
            if str(target_term).strip()
        )
        if decision == "keep" and not target_terms:
            target_terms = term.target_terms
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
        and (term.target_terms or term.decision == "preserve")
        and term.confidence >= confidence_threshold
    ]
    accepted.sort(key=lambda term: (term.confidence, len(term.source_term.split())), reverse=True)
    return accepted[:max_terms]


def dataset_term_from_json(payload: dict[str, Any]) -> DatasetTerminologyTerm:
    raw_candidates = payload.get("candidates", {})
    if not isinstance(raw_candidates, dict):
        raw_candidates = {}
    return DatasetTerminologyTerm(
        source_term=str(payload.get("source_term", "")).strip(),
        target_terms=tuple(
            str(target_term).strip()
            for target_term in payload.get("target_terms", [])
            if str(target_term).strip()
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
        category=term.category if category is None else category,
        source=term.source if source is None else source,
        confidence=term.confidence if confidence is None else confidence,
        decision=term.decision if decision is None else decision,
        reason=term.reason if reason is None else reason,
        candidates=term.candidates if candidates is None else candidates,
    )


def should_preserve_dataset_term(source_term: str, category: str = "") -> bool:
    stripped = source_term.strip()
    return category in {"unit", "identifier"} or bool(_FORMULA_OR_IDENTIFIER_RE.match(stripped))


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
