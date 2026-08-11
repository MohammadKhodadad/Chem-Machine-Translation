from __future__ import annotations

from abc import ABC, abstractmethod

from chem_machine_translation.config import Settings
from chem_machine_translation.core.schemas import Document, TranslationResult
from chem_machine_translation.translation.prompts import (
    TranslationDomain,
    build_initial_translation_prompt,
    normalize_translation_domain,
    translator_system_prompt,
)
from chem_machine_translation.translation.providers import (
    TextGenerationProvider,
    build_text_generation_provider,
)
from chem_machine_translation.translation.terminology import (
    EmptyTerminologyLayer,
    TerminologyContext,
    TerminologyLayer,
)


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


class OneShotTranslator(Translator):
    name = "one-shot"

    def __init__(
        self,
        *,
        provider: TextGenerationProvider,
        model: str,
        temperature: float = 0.0,
        terminology_layer: TerminologyLayer | None = None,
        translation_domain: str = "chemistry",
    ) -> None:
        self.provider = provider
        self.model = model
        self.temperature = temperature
        self.terminology_layer = terminology_layer or EmptyTerminologyLayer()
        self.translation_domain: TranslationDomain = normalize_translation_domain(
            translation_domain
        )

    def translate(
        self,
        document: Document,
        target_language: str,
        source_language: str = "English",
    ) -> TranslationResult:
        terminology_section = self.terminology_layer.build_prompt_section(
            TerminologyContext(
                document=document,
                target_language=target_language,
                source_language=source_language,
            )
        )
        translated_text = self.provider.generate(
            system_prompt=translator_system_prompt(self.translation_domain),
            user_prompt=build_initial_translation_prompt(
                document=document,
                target_language=target_language,
                source_language=source_language,
                terminology_section=terminology_section,
                translation_domain=self.translation_domain,
            ),
            model=self.model,
            temperature=self.temperature,
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


def build_translator(
    *,
    translator: str | None = None,
    strategy: str | None = None,
    settings: Settings,
    model: str | None = None,
    temperature: float = 0.0,
    terminology_layer: TerminologyLayer | None = None,
    provider: str = "openai",
    provider_base_url: str | None = None,
    provider_timeout: float | None = None,
    translation_domain: str = "chemistry",
) -> Translator:
    selected_translator = normalize_translator_name(translator or strategy or "one-shot")
    if selected_translator == "dry-run":
        return DryRunTranslator()
    if selected_translator == "one-shot":
        text_provider = build_text_generation_provider(
            provider=provider,
            settings=settings,
            base_url=provider_base_url,
            timeout=provider_timeout,
        )
        return OneShotTranslator(
            provider=text_provider,
            model=model or settings.default_model,
            temperature=temperature,
            terminology_layer=terminology_layer,
            translation_domain=translation_domain,
        )

    raise ValueError(f"Unknown translator: {selected_translator}")


def normalize_translator_name(translator: str) -> str:
    normalized = translator.strip().lower()
    if normalized == "openai":
        return "one-shot"
    if normalized in {"dry-run", "one-shot"}:
        return normalized
    raise ValueError(f"Unknown translator: {translator}")
