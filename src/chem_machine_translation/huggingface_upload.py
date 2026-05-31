from __future__ import annotations

from pathlib import Path

from huggingface_hub import HfApi

from chem_machine_translation.config import Settings


def is_huggingface_upload_configured(settings: Settings) -> bool:
    return bool(settings.hf_repo_id and settings.hf_token)


def build_huggingface_path(settings: Settings, local_path: Path) -> str:
    prefix = settings.hf_path_prefix.strip("/")
    if not prefix:
        return local_path.name
    return f"{prefix}/{local_path.name}"


def upload_report_to_huggingface(settings: Settings, local_path: Path) -> str:
    if not settings.hf_repo_id:
        raise ValueError("CHEM_MT_HF_REPO_ID or HF_REPO_ID is required for Hugging Face upload.")
    if not settings.hf_token:
        raise ValueError("CHEM_MT_HF_TOKEN or HF_TOKEN is required for Hugging Face upload.")

    path_in_repo = build_huggingface_path(settings, local_path)
    api = HfApi(token=settings.hf_token)
    api.create_repo(
        repo_id=settings.hf_repo_id,
        repo_type=settings.hf_repo_type,
        exist_ok=True,
    )
    commit_info = api.upload_file(
        path_or_fileobj=local_path,
        path_in_repo=path_in_repo,
        repo_id=settings.hf_repo_id,
        repo_type=settings.hf_repo_type,
        commit_message=f"Upload translation report {local_path.name}",
    )

    return getattr(commit_info, "commit_url", str(commit_info))
