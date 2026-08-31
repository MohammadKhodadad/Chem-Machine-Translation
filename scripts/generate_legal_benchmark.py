from __future__ import annotations

from pathlib import Path

from chem_machine_translation.benchmark_generation.pipeline import run_benchmark_config_file

CONFIG_PATH = Path("config/benchmark_generation/legal.toml")


def main() -> None:
    result = run_benchmark_config_file(CONFIG_PATH)
    print(f"Generated benchmark: {result.name}")
    for build in result.builds:
        print(
            f"- {build.name}: {build.row_count} rows across {build.direction_count} directions; "
            f"manifest={build.combined_manifest_path}; metadata={build.metadata_path}"
        )


if __name__ == "__main__":
    main()

