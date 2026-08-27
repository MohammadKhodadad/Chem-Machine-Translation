from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field

DEFAULT_MODEL = "gpt-4.1-mini"
DEFAULT_MAX_INPUT_TOKENS = 256
DEFAULT_LLM_API_MODE = "responses"
DEFAULT_LLM_MAX_OUTPUT_TOKENS = 1024


class Settings(BaseModel):
    """Runtime settings sourced from environment variables and CLI flags."""

    openai_api_key: str | None = Field(default=None)
    openai_base_url: str | None = Field(default=None)
    default_model: str = Field(default=DEFAULT_MODEL)
    llm_api_mode: str = Field(default=DEFAULT_LLM_API_MODE)
    llm_max_output_tokens: int = Field(default=DEFAULT_LLM_MAX_OUTPUT_TOKENS)
    llm_thinking: str | None = Field(default=None)
    llm_reasoning_effort: str | None = Field(default=None)
    default_max_input_tokens: int = Field(default=DEFAULT_MAX_INPUT_TOKENS)
    reports_dir: Path = Field(default=Path("reports"))
    hf_token: str | None = Field(default=None)
    hf_repo_id: str | None = Field(default=None)
    hf_repo_type: str = Field(default="dataset")
    hf_path_prefix: str = Field(default="translations")


def load_settings(env_file: Path | None = None) -> Settings:
    if env_file:
        load_dotenv(env_file)
    else:
        load_dotenv()

    provider_api_key, provider_base_url = resolve_openai_compatible_provider()

    return Settings(
        openai_api_key=provider_api_key,
        openai_base_url=provider_base_url,
        default_model=os.getenv("CHEM_MT_MODEL") or os.getenv("OPENCODE_MODEL") or DEFAULT_MODEL,
        llm_api_mode=resolve_llm_api_mode(),
        llm_max_output_tokens=int(
            os.getenv("CHEM_MT_LLM_MAX_OUTPUT_TOKENS")
            or os.getenv("OPENCODE_MAX_OUTPUT_TOKENS")
            or str(DEFAULT_LLM_MAX_OUTPUT_TOKENS)
        ),
        llm_thinking=resolve_llm_thinking(),
        llm_reasoning_effort=resolve_llm_reasoning_effort(),
        default_max_input_tokens=int(
            os.getenv("CHEM_MT_MAX_INPUT_TOKENS", str(DEFAULT_MAX_INPUT_TOKENS))
        ),
        reports_dir=Path(os.getenv("CHEM_MT_REPORTS_DIR", "reports")),
        hf_token=(
            os.getenv("CHEM_MT_HF_TOKEN")
            or os.getenv("HF_TOKEN")
            or os.getenv("HUGGINGFACE_HUB_TOKEN")
            or os.getenv("HUGGINGFACE_TOKEN")
        ),
        hf_repo_id=(
            os.getenv("CHEM_MT_HF_REPO_ID")
            or os.getenv("HF_REPO_ID")
            or os.getenv("HUGGINGFACE_REPO_ID")
        ),
        hf_repo_type=os.getenv("CHEM_MT_HF_REPO_TYPE", "dataset"),
        hf_path_prefix=os.getenv("CHEM_MT_HF_PATH_PREFIX", "translations"),
    )


def resolve_openai_compatible_provider() -> tuple[str | None, str | None]:
    """Resolve API credentials without mixing keys across configured provider URLs."""
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_base_url = os.getenv("OPENAI_BASE_URL")
    opencode_api_key = os.getenv("OPENCODE_API_KEY")
    opencode_base_url = os.getenv("OPENCODE_BASE_URL")

    if openai_base_url:
        return openai_api_key or opencode_api_key, openai_base_url
    if opencode_base_url:
        return opencode_api_key or openai_api_key, opencode_base_url
    return openai_api_key or opencode_api_key, None


def resolve_llm_api_mode() -> str:
    explicit_mode = os.getenv("CHEM_MT_LLM_API_MODE") or os.getenv("OPENCODE_API_MODE")
    if explicit_mode:
        return explicit_mode
    if os.getenv("OPENCODE_BASE_URL") and not os.getenv("OPENAI_BASE_URL"):
        return "chat_completions"
    return DEFAULT_LLM_API_MODE


def resolve_llm_thinking() -> str | None:
    explicit_thinking = os.getenv("CHEM_MT_LLM_THINKING") or os.getenv("OPENCODE_THINKING")
    if explicit_thinking:
        return explicit_thinking
    if os.getenv("OPENCODE_BASE_URL") and not os.getenv("OPENAI_BASE_URL"):
        return "disabled"
    return None


def resolve_llm_reasoning_effort() -> str | None:
    explicit_effort = os.getenv("CHEM_MT_LLM_REASONING_EFFORT") or os.getenv(
        "OPENCODE_REASONING_EFFORT"
    )
    return explicit_effort or None
