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
    default_headers: dict[str, str] | None = None
    timeout: float | None = None
    api_mode: str = "responses"
    max_output_tokens: int | None = 1024
    thinking: str | None = None
    reasoning_effort: str | None = None
    name: str = "openai"

    def __post_init__(self) -> None:
        self._client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            default_headers=self.default_headers,
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
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        if self.api_mode == "responses":
            request: dict[str, object] = {
                "model": model,
                "temperature": temperature,
                "input": messages,
                "max_output_tokens": self.max_output_tokens,
            }
            if normalized_llm_thinking(self.thinking) == "disabled":
                request["reasoning"] = {"effort": "none"}
            elif self.reasoning_effort:
                request["reasoning"] = {"effort": self.reasoning_effort}
            response = self._client.responses.create(**request)
            return response.output_text.strip()
        if self.api_mode == "chat_completions":
            request = {
                "model": model,
                "temperature": temperature,
                "messages": messages,
                "max_tokens": self.max_output_tokens,
            }
            extra_body = llm_chat_extra_body(self.thinking)
            if extra_body:
                request["extra_body"] = extra_body
            if normalized_llm_thinking(self.thinking) == "enabled" and self.reasoning_effort:
                request["reasoning_effort"] = self.reasoning_effort
            response = self._client.chat.completions.create(**request)
            return (response.choices[0].message.content or "").strip()
        raise ValueError(f"Unknown LLM API mode: {self.api_mode}")


def build_text_generation_provider(
    *,
    provider: str,
    settings: Settings,
    base_url: str | None = None,
    timeout: float | None = None,
    thinking: str | None = None,
    reasoning_effort: str | None = None,
) -> TextGenerationProvider:
    if provider not in {"openai", "opencode", "openai-compatible"}:
        raise ValueError(f"Unknown text generation provider: {provider}")

    api_key, resolved_base_url, api_mode, provider_thinking = resolve_provider_settings(
        provider=provider,
        settings=settings,
        base_url=base_url,
    )
    if not api_key and resolved_base_url:
        api_key = "local"
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY or OPENCODE_API_KEY is required for the OpenAI-compatible text "
            "generation provider."
        )

    return OpenAIResponsesProvider(
        api_key=api_key,
        base_url=resolved_base_url,
        default_headers=(
            {
                "User-Agent": "chem-machine-translation/1.0",
                "x-opencode-session": settings.opencode_session_id,
            }
            if provider == "opencode"
            else None
        ),
        timeout=timeout,
        api_mode=api_mode,
        max_output_tokens=settings.llm_max_output_tokens,
        thinking=thinking if thinking is not None else provider_thinking,
        reasoning_effort=(
            reasoning_effort if reasoning_effort is not None else settings.llm_reasoning_effort
        ),
        name=provider,
    )


def resolve_provider_settings(
    *,
    provider: str,
    settings: Settings,
    base_url: str | None,
) -> tuple[str | None, str | None, str, str | None]:
    if provider == "openai":
        return settings.openai_api_key, base_url or settings.openai_base_url, "responses", None
    if provider == "opencode":
        return (
            settings.opencode_api_key,
            base_url or settings.opencode_base_url,
            "chat_completions",
            "disabled",
        )
    return (
        settings.openai_api_key or settings.opencode_api_key,
        base_url or settings.openai_base_url or settings.opencode_base_url,
        settings.llm_api_mode,
        settings.llm_thinking,
    )


def normalized_llm_thinking(thinking: str | None) -> str | None:
    if thinking is None:
        return None
    normalized = thinking.strip().lower()
    if normalized in {"false", "off", "none", "non-thinking", "non_thinking", "disabled"}:
        return "disabled"
    if normalized in {"true", "on", "thinking", "enabled"}:
        return "enabled"
    return normalized


def llm_chat_extra_body(thinking: str | None) -> dict[str, object]:
    normalized = normalized_llm_thinking(thinking)
    if normalized == "disabled":
        return {"thinking": {"type": "disabled"}}
    if normalized == "enabled":
        return {"thinking": {"type": "enabled"}}
    return {}
