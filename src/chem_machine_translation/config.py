from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field

DEFAULT_MODEL = "gpt-4.1-mini"
DEFAULT_MAX_INPUT_TOKENS = 256


class Settings(BaseModel):
    """Runtime settings sourced from environment variables and CLI flags."""

    openai_api_key: str | None = Field(default=None)
    openai_base_url: str | None = Field(default=None)
    default_model: str = Field(default=DEFAULT_MODEL)
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

    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_base_url=os.getenv("OPENAI_BASE_URL"),
        default_model=os.getenv("CHEM_MT_MODEL", DEFAULT_MODEL),
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
