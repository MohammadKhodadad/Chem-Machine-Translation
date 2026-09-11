from __future__ import annotations

import argparse
from pathlib import Path

from huggingface_hub import HfApi

from chem_machine_translation.config import load_settings

DEFAULT_ARTICLES_JSONL = Path(
    "benchmark_sources/jrc_acquis_anchored_articles_250_per_language_pair.jsonl"
)
DEFAULT_ARTICLES_METADATA = Path(
    "benchmark_sources/jrc_acquis_anchored_articles_250_per_language_pair_metadata.json"
)
DEFAULT_DEFINITIONS_JSONL = Path(
    "benchmark_sources/jrc_acquis_anchored_definitions_250_per_language_pair.jsonl"
)
DEFAULT_DEFINITIONS_METADATA = Path(
    "benchmark_sources/jrc_acquis_anchored_definitions_250_per_language_pair_metadata.json"
)
DEFAULT_ARTICLES_HF_REPO_ID = "BASF-AI/ai4chem-clir-jrc-acquis-articles-benchmark-sources"
DEFAULT_DEFINITIONS_HF_REPO_ID = (
    "BASF-AI/ai4chem-clir-jrc-acquis-definitions-benchmark-sources"
)
DEFAULT_HF_REPO_ID = "BASF-AI/ai4chem-clir-jrc-acquis-benchmark-sources"
DEFAULT_HF_COLLECTION = "BASF-AI/ai4chem-clir"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Upload existing JRC-Acquis benchmark source files to Hugging Face "
            "without regenerating them."
        ),
    )
    parser.add_argument(
        "--hf-repo-id",
        default=None,
        help=(
            "Legacy fallback repo ID used for both source sets when no per-set repo is set. "
            f"Defaults to CHEM_MT_HF_REPO_ID/HF_REPO_ID, then {DEFAULT_HF_REPO_ID}."
        ),
    )
    parser.add_argument(
        "--articles-hf-repo-id",
        default=None,
        help=(
            "Hugging Face dataset repo ID for the article source set. Defaults to the "
            "legacy repo ID or the article-specific baseline."
        ),
    )
    parser.add_argument(
        "--definitions-hf-repo-id",
        default=None,
        help=(
            "Hugging Face dataset repo ID for the definition source set. Defaults to the "
            "legacy repo ID or the definitions-specific baseline."
        ),
    )
    parser.add_argument(
        "--hf-collection",
        default=DEFAULT_HF_COLLECTION,
        help="Collection slug to update after each source set is uploaded. Use an empty value to skip.",
    )
    parser.add_argument(
        "--skip-collection",
        action="store_true",
        help="Skip collection update entirely; useful when the token lacks collection permissions.",
    )
    parser.add_argument(
        "--hf-path-prefix",
        default="benchmark_sources",
        help="Repository directory under which the two source sets are stored.",
    )
    parser.add_argument("--articles-jsonl", type=Path, default=DEFAULT_ARTICLES_JSONL)
    parser.add_argument("--articles-metadata", type=Path, default=DEFAULT_ARTICLES_METADATA)
    parser.add_argument("--definitions-jsonl", type=Path, default=DEFAULT_DEFINITIONS_JSONL)
    parser.add_argument("--definitions-metadata", type=Path, default=DEFAULT_DEFINITIONS_METADATA)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    articles_repo_id = args.articles_hf_repo_id or args.hf_repo_id or DEFAULT_ARTICLES_HF_REPO_ID
    definitions_repo_id = (
        args.definitions_hf_repo_id or args.hf_repo_id or DEFAULT_DEFINITIONS_HF_REPO_ID
    )
    collection_slug = None if args.skip_collection else args.hf_collection

    upload_jrc_source_set(
        name="jrc_acquis_anchored_articles",
        jsonl_path=args.articles_jsonl,
        metadata_path=args.articles_metadata,
        repo_id=articles_repo_id,
        path_prefix=args.hf_path_prefix,
        collection_slug=collection_slug,
    )
    upload_jrc_source_set(
        name="jrc_acquis_anchored_definitions",
        jsonl_path=args.definitions_jsonl,
        metadata_path=args.definitions_metadata,
        repo_id=definitions_repo_id,
        path_prefix=args.hf_path_prefix,
        collection_slug=collection_slug,
    )


def upload_jrc_source_set(
    *,
    name: str,
    jsonl_path: Path,
    metadata_path: Path,
    repo_id: str | None,
    path_prefix: str,
    collection_slug: str | None,
) -> None:
    settings = load_settings()
    resolved_repo_id = repo_id or settings.hf_repo_id or DEFAULT_HF_REPO_ID
    if not resolved_repo_id:
        raise ValueError(
            "--hf-repo-id, CHEM_MT_HF_REPO_ID, or HF_REPO_ID is required for Hugging Face upload."
        )
    if not settings.hf_token:
        raise ValueError("CHEM_MT_HF_TOKEN or HF_TOKEN is required for Hugging Face upload.")

    source_paths = (jsonl_path, metadata_path)
    missing_paths = [path for path in source_paths if not path.is_file()]
    if missing_paths:
        missing = ", ".join(str(path) for path in missing_paths)
        raise FileNotFoundError(f"JRC benchmark source files do not exist: {missing}")

    api = HfApi(token=settings.hf_token)
    api.create_repo(
        repo_id=resolved_repo_id,
        repo_type="dataset",
        exist_ok=True,
    )
    normalized_prefix = path_prefix.strip("/")
    source_prefix = f"{normalized_prefix}/{name}" if normalized_prefix else name
    for local_path in source_paths:
        path_in_repo = f"{source_prefix}/{local_path.name}"
        api.upload_file(
            path_or_fileobj=local_path,
            path_in_repo=path_in_repo,
            repo_id=resolved_repo_id,
            repo_type="dataset",
            commit_message=f"Upload {name} benchmark source {local_path.name}",
        )
        print(f"Uploaded {local_path} to {resolved_repo_id}/{path_in_repo}")

    if collection_slug:
        api.add_collection_item(
            collection_slug=collection_slug,
            item_id=resolved_repo_id,
            item_type="dataset",
            exists_ok=True,
        )
        print(f"Added {resolved_repo_id} to collection {collection_slug}")


if __name__ == "__main__":
    main()
