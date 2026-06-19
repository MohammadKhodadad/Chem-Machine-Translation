from __future__ import annotations

from abc import ABC, abstractmethod

from openai import OpenAI

from chem_machine_translation.config import Settings
from chem_machine_translation.core.schemas import Document, TranslationResult
from chem_machine_translation.translation.agents import OpenAITranslationAgents
from chem_machine_translation.translation.terminology import EmptyTerminologyLayer, TerminologyLayer


class Translator(ABC):
    name: str

    @abstractmethod
    def translate(
        self,
        document: Document,
        target_language: str,
        source_language: str = "English",
    ) -> TranslationResult:
        raise NotImplementedError


class DryRunTranslator(Translator):
    name = "dry-run"

    def translate(
        self,
        document: Document,
        target_language: str,
        source_language: str = "English",
    ) -> TranslationResult:
        return TranslationResult(
            document=document,
            source_language=source_language,
            target_language=target_language,
            translated_text=document.text,
            strategy=self.name,
        )


class BaseOpenAITranslator(Translator):
    def __init__(
        self,
        settings: Settings,
        model: str | None = None,
        temperature: float = 0.0,
        terminology_layer: TerminologyLayer | None = None,
    ) -> None:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for the openai strategy.")

        self.model = model or settings.default_model
        self.temperature = temperature
        self.terminology_layer = terminology_layer or EmptyTerminologyLayer()
        self.client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
        self.agents = OpenAITranslationAgents(
            client=self.client,
            model=self.model,
            temperature=self.temperature,
            terminology_layer=self.terminology_layer,
        )


class OpenAITranslator(BaseOpenAITranslator):
    name = "openai"

    def translate(
        self,
        document: Document,
        target_language: str,
        source_language: str = "English",
    ) -> TranslationResult:
        terminology_section = self.agents.build_terminology_section(
            document=document,
            target_language=target_language,
            source_language=source_language,
        )
        translated_text = self.agents.translate_once(
            document=document,
            target_language=target_language,
            source_language=source_language,
            terminology_section=terminology_section,
        )

        return TranslationResult(
            document=document,
            source_language=source_language,
            target_language=target_language,
            translated_text=translated_text,
            strategy=self.name,
            model=self.model,
            terminology_section=terminology_section,
        )


class OpenAIAgenticTranslator(BaseOpenAITranslator):
    name = "openai-agentic"

    def __init__(
        self,
        settings: Settings,
        model: str | None = None,
        temperature: float = 0.0,
        max_rounds: int = 3,
        terminology_layer: TerminologyLayer | None = None,
    ) -> None:
        super().__init__(
            settings=settings,
            model=model,
            temperature=temperature,
            terminology_layer=terminology_layer,
        )
        self.max_rounds = max_rounds

    def translate(
        self,
        document: Document,
        target_language: str,
        source_language: str = "English",
    ) -> TranslationResult:
        terminology_section = self.agents.build_terminology_section(
            document=document,
            target_language=target_language,
            source_language=source_language,
        )
        translated_text, review, review_rounds, review_notes = self.agents.translate_with_review(
            document=document,
            target_language=target_language,
            source_language=source_language,
            max_rounds=self.max_rounds,
            terminology_section=terminology_section,
        )

        return TranslationResult(
            document=document,
            source_language=source_language,
            target_language=target_language,
            translated_text=translated_text,
            strategy=self.name,
            model=self.model,
            approved=review.approved,
            review_rounds=review_rounds,
            review_notes=review_notes,
            terminology_section=terminology_section,
        )


def build_translator(
    strategy: str,
    settings: Settings,
    model: str | None = None,
    temperature: float = 0.0,
    max_rounds: int = 3,
    terminology_layer: TerminologyLayer | None = None,
) -> Translator:
    if strategy == "dry-run":
        return DryRunTranslator()
    if strategy == "openai":
        return OpenAITranslator(
            settings=settings,
            model=model,
            temperature=temperature,
            terminology_layer=terminology_layer,
        )
    if strategy == "openai-agentic":
        return OpenAIAgenticTranslator(
            settings=settings,
            model=model,
            temperature=temperature,
            max_rounds=max_rounds,
            terminology_layer=terminology_layer,
        )

    raise ValueError(f"Unknown translation strategy: {strategy}")
