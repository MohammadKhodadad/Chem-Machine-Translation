from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from openai import OpenAI

from chem_machine_translation.config import Settings


class TextGenerationProvider(Protocol):
    name: str

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        model: str,
        temperature: float = 0.0,
    ) -> str:
        raise NotImplementedError


@dataclass
class OpenAIResponsesProvider:
    api_key: str
    base_url: str | None = None
    timeout: float | None = None
    name: str = "openai"

    def __post_init__(self) -> None:
        self._client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout,
        )

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        model: str,
        temperature: float = 0.0,
    ) -> str:
        response = self._client.responses.create(
            model=model,
            temperature=temperature,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.output_text.strip()


def build_text_generation_provider(
    *,
    provider: str,
    settings: Settings,
    base_url: str | None = None,
    timeout: float | None = None,
) -> TextGenerationProvider:
    if provider not in {"openai", "openai-compatible"}:
        raise ValueError(f"Unknown text generation provider: {provider}")

    resolved_base_url = base_url or settings.openai_base_url
    api_key = settings.openai_api_key
    if not api_key and resolved_base_url:
        api_key = "local"
    if not api_key:
        raise ValueError("OPENAI_API_KEY is required for the OpenAI text generation provider.")

    return OpenAIResponsesProvider(
        api_key=api_key,
        base_url=resolved_base_url,
        timeout=timeout,
        name=provider,
    )
