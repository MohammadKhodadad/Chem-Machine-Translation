from __future__ import annotations

import argparse
import zipfile
from pathlib import Path
from urllib.request import urlretrieve

from huggingface_hub import hf_hub_download

DEFAULT_REPO_ID = "nlpaueb/multi_eurlex"
DEFAULT_ARCHIVE = "multi_eurlex_translated.zip"
DEFAULT_DESCRIPTOR_URL = (
    "https://raw.githubusercontent.com/nlpaueb/multi-eurlex/master/"
    "data/eurovoc_descriptors.json"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download and extract MultiEURLEX data into the ignored data folder.",
    )
    parser.add_argument("--output-dir", type=Path, default=Path("data/multi_eurlex"))
    parser.add_argument("--repo-id", default=DEFAULT_REPO_ID)
    parser.add_argument("--archive-name", default=DEFAULT_ARCHIVE)
    parser.add_argument("--descriptor-url", default=DEFAULT_DESCRIPTOR_URL)
    parser.add_argument("--skip-archive", action="store_true")
    parser.add_argument("--skip-descriptors", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    if not args.skip_archive:
        archive_path = download_archive(
            repo_id=args.repo_id,
            archive_name=args.archive_name,
            output_dir=args.output_dir,
        )
        extracted = extract_jsonl_splits(archive_path=archive_path, output_dir=args.output_dir)
        print(f"Extracted {len(extracted)} JSONL files:")
        for path in extracted:
            print(f"- {path}")

    if not args.skip_descriptors:
        descriptor_path = args.output_dir / "eurovoc_descriptors.json"
        if descriptor_path.exists():
            print(f"Descriptor map already exists: {descriptor_path}")
        else:
            print(f"Downloading EuroVoc descriptors to {descriptor_path}")
            urlretrieve(args.descriptor_url, descriptor_path)
            print(f"Descriptor map: {descriptor_path}")


def download_archive(repo_id: str, archive_name: str, output_dir: Path) -> Path:
    archive_path = output_dir / archive_name
    if archive_path.exists():
        print(f"Archive already exists: {archive_path}")
        return archive_path

    print(f"Downloading {repo_id}/{archive_name} to {output_dir}")
    downloaded = hf_hub_download(
        repo_id=repo_id,
        filename=archive_name,
        repo_type="dataset",
        local_dir=output_dir,
    )
    downloaded_path = Path(downloaded)
    if downloaded_path != archive_path and downloaded_path.exists():
        downloaded_path.replace(archive_path)
    print(f"Archive: {archive_path}")
    return archive_path


def extract_jsonl_splits(archive_path: Path, output_dir: Path) -> list[Path]:
    extracted = []
    with zipfile.ZipFile(archive_path) as archive:
        jsonl_members = [
            member
            for member in archive.namelist()
            if member.endswith(".jsonl") and not member.endswith("/")
        ]
        if not jsonl_members:
            raise ValueError(f"No JSONL files found in {archive_path}")
        for member in jsonl_members:
            target_path = output_dir / Path(member).name
            if target_path.exists():
                extracted.append(target_path)
                continue
            print(f"Extracting {member} -> {target_path}")
            with archive.open(member) as source, target_path.open("wb") as target:
                target.write(source.read())
            extracted.append(target_path)
    return extracted


if __name__ == "__main__":
    main()
