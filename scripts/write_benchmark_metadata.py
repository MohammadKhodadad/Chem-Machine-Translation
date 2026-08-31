from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from chem_machine_translation.benchmark_generation.config import load_benchmark_config
from chem_machine_translation.benchmark_generation.metadata import write_benchmark_metadata


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Write metadata.json files for generated benchmark manifests."
    )
    parser.add_argument("--config", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_benchmark_config(args.config)
    for build in config.builds:
        manifest_path = find_combined_manifest(build.output_dir)
        rows = load_jsonl(manifest_path)
        metadata_path = build.output_dir / "metadata.json"
        write_benchmark_metadata(metadata_path, rows=rows, build=build)
        print(f"Wrote {metadata_path} from {manifest_path}")


def find_combined_manifest(output_dir: Path) -> Path:
    manifests = sorted(output_dir.glob("*-directions-*-manifest.jsonl"))
    if len(manifests) != 1:
        raise ValueError(
            f"Expected one combined manifest in {output_dir}, found {len(manifests)}."
        )
    return manifests[0]


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


if __name__ == "__main__":
    main()
