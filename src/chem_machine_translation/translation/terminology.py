from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from openai import OpenAI

from chem_machine_translation.config import Settings
from chem_machine_translation.core.schemas import Document
from chem_machine_translation.translation.iate import (
    IATEClient,
    IATETermTranslation,
    iate_language_code,
)
from chem_machine_translation.translation.wikidata import (
    WikidataClient,
    WikidataTermTranslation,
    wikidata_language_code,
)

_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)
_DEFAULT_MAX_TERMS = 20
_ELEMENT_SYMBOLS = {
    "H",
    "He",
    "Li",
    "Be",
    "B",
    "C",
    "N",
    "O",
    "F",
    "Ne",
    "Na",
    "Mg",
    "Al",
    "Si",
    "P",
    "S",
    "Cl",
    "Ar",
    "K",
    "Ca",
    "Sc",
    "Ti",
    "V",
    "Cr",
    "Mn",
    "Fe",
    "Co",
    "Ni",
    "Cu",
    "Zn",
    "Ga",
    "Ge",
    "As",
    "Se",
    "Br",
    "Kr",
    "Rb",
    "Sr",
    "Y",
    "Zr",
    "Nb",
    "Mo",
    "Tc",
    "Ru",
    "Rh",
    "Pd",
    "Ag",
    "Cd",
    "In",
    "Sn",
    "Sb",
    "Te",
    "I",
    "Xe",
    "Cs",
    "Ba",
    "La",
    "Ce",
    "Pr",
    "Nd",
    "Pm",
    "Sm",
    "Eu",
    "Gd",
    "Tb",
    "Dy",
    "Ho",
    "Er",
    "Tm",
    "Yb",
    "Lu",
    "Hf",
    "Ta",
    "W",
    "Re",
    "Os",
    "Ir",
    "Pt",
    "Au",
    "Hg",
    "Tl",
    "Pb",
    "Bi",
    "Po",
    "At",
    "Rn",
    "Fr",
    "Ra",
    "Ac",
    "Th",
    "Pa",
    "U",
    "Np",
    "Pu",
    "Am",
    "Cm",
    "Bk",
    "Cf",
    "Es",
    "Fm",
    "Md",
    "No",
    "Lr",
    "Rf",
    "Db",
    "Sg",
    "Bh",
    "Hs",
    "Mt",
    "Ds",
    "Rg",
    "Cn",
    "Nh",
    "Fl",
    "Mc",
    "Lv",
    "Ts",
    "Og",
}


TERM_EXTRACTOR_SYSTEM_PROMPT = """You identify terminology that needs special handling before
chemistry translation.

Extract exact source-language spans that are important for preserving scientific meaning:
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
      "reason": "short reason this term needs care"
    }
  ]
}
"""


@dataclass(frozen=True)
class TerminologyContext:
    document: Document
    target_language: str
    source_language: str


class TerminologyLayer(Protocol):
    """Builds optional terminology instructions for a translation prompt."""

    def build_prompt_section(self, context: TerminologyContext) -> str:
        """Return prompt text to inject, or an empty string when no terms apply."""


class EmptyTerminologyLayer:
    """Default terminology layer that keeps prompts unchanged."""

    def build_prompt_section(self, context: TerminologyContext) -> str:
        return ""


class CompositeTerminologyLayer:
    """Combines multiple terminology layers into one prompt section."""

    def __init__(self, layers: list[TerminologyLayer]) -> None:
        self.layers = layers

    def build_prompt_section(self, context: TerminologyContext) -> str:
        sections = [
            section
            for layer in self.layers
            if (section := layer.build_prompt_section(context).strip())
        ]
        return "\n\n".join(sections)


@dataclass(frozen=True)
class StaticTerminologyLayer:
    """Injects a fixed terminology instruction block for every translated document."""

    prompt_text: str

    def build_prompt_section(self, context: TerminologyContext) -> str:
        text = self.prompt_text.strip()
        if not text:
            return ""
        return "Approved terminology instructions:\n" + text


@dataclass(frozen=True)
class ExtractedTerm:
    source_term: str
    category: str
    reason: str
    wikidata_target_label: str = ""
    wikidata_entity_id: str = ""
    wikidata_description: str = ""
    iate_target_label: str = ""
    iate_entry_id: str = ""


class LLMTerminologyLayer:
    """Uses an LLM to extract source terms that the translator should handle carefully."""

    def __init__(
        self,
        client: OpenAI,
        model: str,
        max_terms: int = _DEFAULT_MAX_TERMS,
        wikidata_client: WikidataClient | None = None,
        iate_client: IATEClient | None = None,
    ) -> None:
        self.client = client
        self.model = model
        self.max_terms = max_terms
        self.wikidata_client = wikidata_client
        self.iate_client = iate_client
        self._cache: dict[tuple[str, str, str, str, str], str] = {}

    def build_prompt_section(self, context: TerminologyContext) -> str:
        cache_key = (
            context.document.dataset,
            context.document.source_id,
            context.document.text,
            context.source_language,
            context.target_language,
        )
        if cache_key in self._cache:
            return self._cache[cache_key]

        terms = self.extract_terms(context)
        terms = self.add_iate_translations(terms, context)
        terms = self.add_wikidata_translations(terms, context)
        section = format_extracted_terms(terms)
        self._cache[cache_key] = section
        return section

    def extract_terms(self, context: TerminologyContext) -> list[ExtractedTerm]:
        response = self.client.responses.create(
            model=self.model,
            temperature=0.0,
            input=[
                {"role": "system", "content": TERM_EXTRACTOR_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": build_term_extraction_prompt(
                        context=context,
                        max_terms=self.max_terms,
                    ),
                },
            ],
        )
        return parse_extracted_terms(response.output_text)

    def add_wikidata_translations(
        self,
        terms: list[ExtractedTerm],
        context: TerminologyContext,
    ) -> list[ExtractedTerm]:
        if not self.wikidata_client:
            return terms

        source_language_code = wikidata_language_code(context.source_language)
        target_language_code = wikidata_language_code(context.target_language)
        if not source_language_code or not target_language_code:
            return terms

        enriched_terms = []
        for term in terms:
            if should_preserve_without_external_lookup(term):
                enriched_terms.append(term)
                continue
            if term.iate_target_label:
                enriched_terms.append(term)
                continue
            translation = self.wikidata_client.translate_term(
                source_term=term.source_term,
                source_language_code=source_language_code,
                target_language_code=target_language_code,
            )
            enriched_terms.append(enrich_term_with_wikidata(term, translation))

        return enriched_terms

    def add_iate_translations(
        self,
        terms: list[ExtractedTerm],
        context: TerminologyContext,
    ) -> list[ExtractedTerm]:
        if not self.iate_client:
            return terms

        source_language_code = iate_language_code(context.source_language)
        target_language_code = iate_language_code(context.target_language)
        if not source_language_code or not target_language_code:
            return terms

        enriched_terms = []
        for term in terms:
            if should_preserve_without_external_lookup(term):
                enriched_terms.append(term)
                continue
            translation = self.iate_client.translate_term(
                source_term=term.source_term,
                source_language_code=source_language_code,
                target_language_code=target_language_code,
            )
            enriched_terms.append(enrich_term_with_iate(term, translation))

        return enriched_terms


def load_static_terminology_layer(path: Path | None) -> TerminologyLayer:
    if path is None:
        return EmptyTerminologyLayer()

    return StaticTerminologyLayer(path.read_text(encoding="utf-8"))


def build_terminology_layer(
    settings: Settings,
    static_prompt_path: Path | None = None,
    extract_terms: bool = False,
    extraction_model: str | None = None,
    max_terms: int = _DEFAULT_MAX_TERMS,
    use_wikidata: bool = False,
    use_iate: bool = False,
) -> TerminologyLayer:
    layers: list[TerminologyLayer] = []

    if static_prompt_path is not None:
        layers.append(StaticTerminologyLayer(static_prompt_path.read_text(encoding="utf-8")))

    if extract_terms:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for LLM terminology extraction.")
        layers.append(
            LLMTerminologyLayer(
                client=OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url),
                model=extraction_model or settings.default_model,
                max_terms=max_terms,
                wikidata_client=WikidataClient() if use_wikidata else None,
                iate_client=IATEClient() if use_iate else None,
            )
        )

    if not layers:
        return EmptyTerminologyLayer()
    if len(layers) == 1:
        return layers[0]
    return CompositeTerminologyLayer(layers)


def build_term_extraction_prompt(context: TerminologyContext, max_terms: int) -> str:
    return (
        f"Find up to {max_terms} terminology items in this {context.source_language} chemistry "
        f"document before translation into {context.target_language}.\n\n"
        "Source document:\n"
        f"{context.document.text}"
    )


def parse_extracted_terms(text: str) -> list[ExtractedTerm]:
    match = _JSON_OBJECT_RE.search(text)
    payload = json.loads(match.group(0) if match else text)
    raw_terms = payload.get("terms", [])
    terms: list[ExtractedTerm] = []

    for raw_term in raw_terms:
        if not isinstance(raw_term, dict):
            continue
        source_term = str(raw_term.get("source_term", "")).strip()
        if not source_term:
            continue
        terms.append(
            ExtractedTerm(
                source_term=source_term,
                category=str(raw_term.get("category", "other")).strip() or "other",
                reason=str(raw_term.get("reason", "")).strip(),
            )
        )

    return terms


def format_extracted_terms(terms: list[ExtractedTerm]) -> str:
    if not terms:
        return ""

    lines = [
        "LLM-extracted terminology focus list:",
        "Use these exact source terms as terms that require careful, consistent translation. "
        "This is not an approved bilingual glossary.",
    ]
    for term in terms:
        detail = f" ({term.reason})" if term.reason else ""
        wikidata_detail = ""
        if term.wikidata_target_label:
            wikidata_detail = (
                f" | Wikidata candidate: {term.wikidata_target_label}"
                f" ({term.wikidata_entity_id})"
            )
        iate_detail = ""
        if term.iate_target_label:
            iate_detail = f" | IATE candidate: {term.iate_target_label} ({term.iate_entry_id})"
        lines.append(
            f"- {term.source_term} [{term.category}]{wikidata_detail}{iate_detail}{detail}"
        )

    return "\n".join(lines)


def enrich_term_with_wikidata(
    term: ExtractedTerm,
    translation: WikidataTermTranslation | None,
) -> ExtractedTerm:
    if translation is None:
        return term

    return ExtractedTerm(
        source_term=term.source_term,
        category=term.category,
        reason=term.reason,
        wikidata_target_label=translation.target_label,
        wikidata_entity_id=translation.entity_id,
        wikidata_description=translation.description,
        iate_target_label=term.iate_target_label,
        iate_entry_id=term.iate_entry_id,
    )


def enrich_term_with_iate(
    term: ExtractedTerm,
    translation: IATETermTranslation | None,
) -> ExtractedTerm:
    if translation is None:
        return term

    return ExtractedTerm(
        source_term=term.source_term,
        category=term.category,
        reason=term.reason,
        wikidata_target_label=term.wikidata_target_label,
        wikidata_entity_id=term.wikidata_entity_id,
        wikidata_description=term.wikidata_description,
        iate_target_label=translation.target_label,
        iate_entry_id=translation.entry_id,
    )


def should_preserve_without_external_lookup(term: ExtractedTerm) -> bool:
    source_term = term.source_term.strip()
    if source_term in _ELEMENT_SYMBOLS:
        return True
    if term.category in {"unit", "identifier"}:
        return True
    return False
