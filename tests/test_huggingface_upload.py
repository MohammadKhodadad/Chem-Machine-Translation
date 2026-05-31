from pathlib import Path

from chem_machine_translation.config import Settings
from chem_machine_translation.huggingface_upload import (
    build_huggingface_path,
    is_huggingface_upload_configured,
)


def test_huggingface_upload_requires_repo_and_token() -> None:
    assert not is_huggingface_upload_configured(Settings())
    assert not is_huggingface_upload_configured(Settings(hf_repo_id="org/repo"))
    assert is_huggingface_upload_configured(Settings(hf_repo_id="org/repo", hf_token="token"))


def test_build_huggingface_path_uses_configured_prefix() -> None:
    settings = Settings(hf_path_prefix="chem-translations/reports")

    assert (
        build_huggingface_path(settings, Path("reports/translation-sample.jsonl"))
        == "chem-translations/reports/translation-sample.jsonl"
    )


def test_build_huggingface_path_allows_empty_prefix() -> None:
    settings = Settings(hf_path_prefix="")

    assert build_huggingface_path(settings, Path("report.jsonl")) == "report.jsonl"
