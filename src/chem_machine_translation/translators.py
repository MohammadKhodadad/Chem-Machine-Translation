from __future__ import annotations

from abc import ABC, abstractmethod

from openai import OpenAI

from chem_machine_translation.config import Settings
from chem_machine_translation.openai_agents import OpenAITranslationAgents
from chem_machine_translation.schemas import Document, TranslationResult


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
    ) -> None:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for the openai strategy.")

        self.model = model or settings.default_model
        self.temperature = temperature
        self.client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
        self.agents = OpenAITranslationAgents(
            client=self.client,
            model=self.model,
            temperature=self.temperature,
        )


class OpenAITranslator(BaseOpenAITranslator):
    name = "openai"

    def translate(
        self,
        document: Document,
        target_language: str,
        source_language: str = "English",
    ) -> TranslationResult:
        translated_text = self.agents.translate_once(
            document=document,
            target_language=target_language,
            source_language=source_language,
        )

        return TranslationResult(
            document=document,
            source_language=source_language,
            target_language=target_language,
            translated_text=translated_text,
            strategy=self.name,
            model=self.model,
        )


class OpenAIAgenticTranslator(BaseOpenAITranslator):
    name = "openai-agentic"

    def __init__(
        self,
        settings: Settings,
        model: str | None = None,
        temperature: float = 0.0,
        max_rounds: int = 3,
    ) -> None:
        super().__init__(settings=settings, model=model, temperature=temperature)
        self.max_rounds = max_rounds

    def translate(
        self,
        document: Document,
        target_language: str,
        source_language: str = "English",
    ) -> TranslationResult:
        translated_text, review, review_rounds, review_notes = self.agents.translate_with_review(
            document=document,
            target_language=target_language,
            source_language=source_language,
            max_rounds=self.max_rounds,
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
        )


def build_translator(
    strategy: str,
    settings: Settings,
    model: str | None = None,
    temperature: float = 0.0,
    max_rounds: int = 3,
) -> Translator:
    if strategy == "dry-run":
        return DryRunTranslator()
    if strategy == "openai":
        return OpenAITranslator(settings=settings, model=model, temperature=temperature)
    if strategy == "openai-agentic":
        return OpenAIAgenticTranslator(
            settings=settings,
            model=model,
            temperature=temperature,
            max_rounds=max_rounds,
        )

    raise ValueError(f"Unknown translation strategy: {strategy}")
