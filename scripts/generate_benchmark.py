from __future__ import annotations

import argparse
from pathlib import Path

from chem_machine_translation.benchmark_generation.pipeline import run_benchmark_config_file


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate benchmark datasets from a TOML config.")
    parser.add_argument("--config", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = run_benchmark_config_file(args.config)
    print_result(result)


def print_result(result: object) -> None:
    print(f"Generated benchmark: {result.name}")
    for build in result.builds:
        print(
            f"- {build.name}: {build.row_count} rows across {build.direction_count} directions; "
            f"manifest={build.combined_manifest_path}"
        )


if __name__ == "__main__":
    main()

