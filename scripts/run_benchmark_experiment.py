from __future__ import annotations

import argparse
from pathlib import Path

from chem_machine_translation.experiment.pipeline import run_experiment_config_file


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run benchmark generation, model prediction, evaluation, and aggregation."
    )
    parser.add_argument("--config", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = run_experiment_config_file(args.config)
    print(f"Completed experiment: {result.name}")
    print(f"Run directory: {result.run_dir}")
    for build in result.benchmark_builds:
        print(
            f"- Benchmark {build.name}: {build.row_count} rows, "
            f"manifest={build.combined_manifest_path}, metadata={build.metadata_path}"
        )
    for model_result in result.model_results:
        print(
            f"- {model_result.model_run}/{model_result.build_name}: "
            f"{model_result.row_count} scored rows, errors={model_result.error_count}, "
            f"predictions={model_result.predictions_path}, scores={model_result.scores_path}"
        )
    print(f"Summary JSON: {result.summary_json_path}")
    print(f"Summary Markdown: {result.summary_markdown_path}")


if __name__ == "__main__":
    main()
