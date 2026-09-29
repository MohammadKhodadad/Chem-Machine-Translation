from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from chem_machine_translation.benchmark.config import load_benchmark_config
from chem_machine_translation.benchmark.metadata import numeric_summary
from chem_machine_translation.benchmark.pipeline import (
    BenchmarkBuildResult,
    run_benchmark_config_file,
)
from chem_machine_translation.config import Settings, load_settings
from chem_machine_translation.core.schemas import Document
from chem_machine_translation.evaluation.metrics import (
    OpenAIMqmJudge,
    UnbabelCometScorer,
    compute_translation_metrics,
    compute_target_term_coverage,
    compute_variant_aware_target_term_coverage,
    select_terminology_terms,
)
from chem_machine_translation.experiment.config import (
    EvaluationRunConfig,
    ExperimentPipelineConfig,
    ModelRunConfig,
    load_experiment_config,
)
from chem_machine_translation.translation.terminology import ManifestTerminologyLayer
from chem_machine_translation.translation.translators import build_translator
from chem_machine_translation.utils.text import approximate_token_count, normalize_text


@dataclass(frozen=True)
class ExperimentModelResult:
    model_run: str
    build_name: str
    predictions_path: Path
    scores_path: Path
    row_count: int
    error_count: int


@dataclass(frozen=True)
class ExperimentPipelineResult:
    name: str
    run_dir: Path
    benchmark_builds: tuple[BenchmarkBuildResult, ...]
    model_results: tuple[ExperimentModelResult, ...]
    summary_json_path: Path
    summary_markdown_path: Path


def run_experiment_config_file(path: Path | str) -> ExperimentPipelineResult:
    return run_experiment(load_experiment_config(path))


def run_experiment(
    config: ExperimentPipelineConfig,
    *,
    settings: Settings | None = None,
) -> ExperimentPipelineResult:
    settings = settings or load_settings()
    config.output.run_dir.mkdir(parents=True, exist_ok=True)
    benchmark_builds = resolve_benchmark_builds(config)
    model_results = []
    score_paths = []
    for build in benchmark_builds:
        for model_run in config.model_runs:
            predictions_path = predictions_output_path(config, model_run, build)
            scores_path = scores_output_path(config, model_run, build)
            prediction_rows = write_predictions(
                build=build,
                model_run=model_run,
                predictions_path=predictions_path,
                settings=settings,
            )
            score_rows = write_scores(
                prediction_rows=prediction_rows,
                evaluation=config.evaluation,
                scores_path=scores_path,
                settings=settings,
                overwrite=config.output.overwrite_scores,
            )
            score_paths.append(scores_path)
            model_results.append(
                ExperimentModelResult(
                    model_run=model_run.name,
                    build_name=build.name,
                    predictions_path=predictions_path,
                    scores_path=scores_path,
                    row_count=len(score_rows),
                    error_count=sum(bool(row.get("error")) for row in score_rows),
                )
            )
    summary = build_experiment_summary(
        config=config,
        benchmark_builds=benchmark_builds,
        score_paths=score_paths,
    )
    summary_json_path = config.output.run_dir / "summary.json"
    summary_markdown_path = config.output.run_dir / "summary.md"
    write_json(summary_json_path, summary)
    summary_markdown_path.write_text(render_summary_markdown(summary), encoding="utf-8")
    return ExperimentPipelineResult(
        name=config.name,
        run_dir=config.output.run_dir,
        benchmark_builds=tuple(benchmark_builds),
        model_results=tuple(model_results),
        summary_json_path=summary_json_path,
        summary_markdown_path=summary_markdown_path,
    )


def resolve_benchmark_builds(config: ExperimentPipelineConfig) -> tuple[BenchmarkBuildResult, ...]:
    if config.benchmark.run_generation:
        return run_benchmark_config_file(config.benchmark.config_path).builds
    benchmark_config = load_benchmark_config(config.benchmark.config_path)
    return tuple(existing_build_result(build) for build in benchmark_config.builds)


def existing_build_result(build: Any) -> BenchmarkBuildResult:
    manifest_path = discover_combined_manifest(build.output_dir)
    rows = load_jsonl(manifest_path)
    return BenchmarkBuildResult(
        name=build.name,
        output_dir=build.output_dir,
        direction_count=len({row.get("direction") for row in rows}),
        row_count=len(rows),
        combined_manifest_path=manifest_path,
        metadata_path=build.output_dir / "metadata.json",
    )


def write_predictions(
    *,
    build: BenchmarkBuildResult,
    model_run: ModelRunConfig,
    predictions_path: Path,
    settings: Settings,
) -> list[dict[str, Any]]:
    manifest_rows = load_jsonl(build.combined_manifest_path)
    loaded_rows = (
        load_jsonl(predictions_path) if model_run.resume and predictions_path.exists() else []
    )
    existing_rows = [row for row in loaded_rows if not row.get("error")]
    if len(existing_rows) != len(loaded_rows):
        predictions_path.write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in existing_rows),
            encoding="utf-8",
        )
    completed_keys = {prediction_key(row) for row in existing_rows}
    missing_manifest_rows = [
        row for row in manifest_rows if manifest_key(row) not in completed_keys
    ]
    if not missing_manifest_rows:
        return existing_rows

    predictions_path.parent.mkdir(parents=True, exist_ok=True)
    if not model_run.resume and predictions_path.exists():
        predictions_path.unlink()
        existing_rows = []

    terminology_layer = (
        ManifestTerminologyLayer(
            term_groups=model_run.terminology_groups,
            max_terms=model_run.max_manifest_terminology_terms,
        )
        if model_run.use_manifest_terminology
        else None
    )
    translation_domain = resolve_translation_domain(model_run.translation_domain, manifest_rows)

    def build_row_translator() -> Any:
        return build_translator(
            translator=model_run.translator,
            settings=settings,
            model=model_run.model,
            temperature=model_run.temperature,
            terminology_layer=terminology_layer,
            provider=model_run.provider,
            provider_base_url=model_run.provider_base_url,
            provider_timeout=model_run.provider_timeout,
            llm_thinking=model_run.llm_thinking,
            llm_reasoning_effort=model_run.llm_reasoning_effort,
            translation_domain=translation_domain,
        )

    def translate_row(manifest_row: dict[str, Any]) -> dict[str, Any]:
        return translate_manifest_row(
            manifest_row=manifest_row,
            build_name=build.name,
            model_run=model_run,
            translator=build_row_translator(),
            row_loader=ParallelRowsLoader(build.output_dir),
        )

    with predictions_path.open("a", encoding="utf-8") as handle:
        if model_run.prediction_workers == 1:
            prediction_rows = map(translate_row, missing_manifest_rows)
            for prediction_row in prediction_rows:
                existing_rows.append(prediction_row)
                handle.write(json.dumps(prediction_row, ensure_ascii=False) + "\n")
        else:
            with ThreadPoolExecutor(max_workers=model_run.prediction_workers) as executor:
                for prediction_row in executor.map(translate_row, missing_manifest_rows):
                    existing_rows.append(prediction_row)
                    handle.write(json.dumps(prediction_row, ensure_ascii=False) + "\n")
    return existing_rows


def translate_manifest_row(
    *,
    manifest_row: dict[str, Any],
    build_name: str,
    model_run: ModelRunConfig,
    translator: Any,
    row_loader: ParallelRowsLoader,
) -> dict[str, Any]:
    source_row, target_row = row_loader.rows_for_manifest(manifest_row)
    text_field = str(manifest_row.get("text_field") or "context")
    source_text = normalize_text(source_row[text_field])
    target_text = normalize_text(target_row[text_field])
    base_row = {
        "build_name": build_name,
        "model_run": model_run.name,
        "direction": manifest_row.get("direction"),
        "source_id": manifest_row.get("source_id"),
        "source_language": manifest_row.get("source_language"),
        "target_language": manifest_row.get("target_language"),
        "source_language_code": manifest_row.get("source_language_code"),
        "target_language_code": manifest_row.get("target_language_code"),
        "provider": model_run.provider if model_run.translator == "one-shot" else "",
        "model": model_run.model if model_run.translator == "one-shot" else "",
        "translator": model_run.translator,
        "approx_source_tokens": approximate_token_count(source_text),
        "source_text": source_text,
        "ground_truth_translation": target_text,
        "metadata": manifest_row,
    }
    try:
        document = Document(
            dataset="parallel_manifest",
            source_id=str(manifest_row["source_id"]),
            text=source_text,
            ground_truth=target_text,
            metadata=manifest_row,
        )
        result = translator.translate(
            document=document,
            target_language=str(manifest_row["target_language"]),
            source_language=str(manifest_row["source_language"]),
        )
        return {
            **base_row,
            "predicted_translation": result.translated_text,
            "approved": result.approved,
            "review_rounds": result.review_rounds,
            "review_notes": result.review_notes,
            "terminology_section": result.terminology_section,
            "error": "",
        }
    except Exception as exc:  # pragma: no cover - exercised in real interrupted API runs
        return {
            **base_row,
            "predicted_translation": "",
            "approved": None,
            "review_rounds": 0,
            "review_notes": [],
            "terminology_section": "",
            "error": f"{type(exc).__name__}: {exc}",
        }


def write_scores(
    *,
    prediction_rows: list[dict[str, Any]],
    evaluation: EvaluationRunConfig,
    scores_path: Path,
    settings: Settings,
    overwrite: bool,
) -> list[dict[str, Any]]:
    if scores_path.exists() and not overwrite:
        return load_jsonl(scores_path)

    scores_path.parent.mkdir(parents=True, exist_ok=True)
    comet_scorer = (
        UnbabelCometScorer(
            model_name=evaluation.comet_model,
            batch_size=evaluation.comet_batch_size,
            gpus=evaluation.comet_gpus,
        )
        if "comet" in evaluation.metrics
        else None
    )
    mqm_judge = (
        OpenAIMqmJudge(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            model=evaluation.fsp_mqm_model,
            timeout=evaluation.fsp_mqm_timeout,
        )
        if "fsp_mqm" in evaluation.metrics
        else None
    )

    score_rows = []
    with scores_path.open("w", encoding="utf-8") as handle:
        for prediction_row in prediction_rows:
            score_row = score_prediction_row(
                prediction_row,
                evaluation=evaluation,
                comet_scorer=comet_scorer,
                mqm_judge=mqm_judge,
            )
            score_rows.append(score_row)
            handle.write(json.dumps(score_row, ensure_ascii=False) + "\n")
    return score_rows


def score_prediction_row(
    prediction_row: dict[str, Any],
    *,
    evaluation: EvaluationRunConfig,
    comet_scorer: Any | None,
    mqm_judge: Any | None,
) -> dict[str, Any]:
    if prediction_row.get("error"):
        return {**prediction_row, "metrics": {}, "evaluation_error": "prediction_error"}
    try:
        metric_names = evaluation.metrics
        if evaluation.terminology_metric_sets:
            metric_names = tuple(
                name
                for name in evaluation.metrics
                if name
                not in {"target_term_coverage", "variant_aware_target_term_coverage"}
            )
        metrics = compute_translation_metrics(
            prediction=str(prediction_row["predicted_translation"]),
            reference=str(prediction_row["ground_truth_translation"]),
            source=str(prediction_row["source_text"]),
            metric_names=metric_names,
            comet_scorer=comet_scorer,
            terminology=prediction_row.get("metadata", {}).get("terminology"),
            terminology_term_groups=evaluation.terminology_groups,
            mqm_judge=mqm_judge,
        )
        terminology = prediction_row.get("metadata", {}).get("terminology") or []
        for metric_set in evaluation.terminology_metric_sets:
            selected_terms = select_terminology_terms(
                terminology,
                term_groups=metric_set.term_groups,
                require_verified=metric_set.require_verified,
            )
            coverage = compute_target_term_coverage(
                prediction=str(prediction_row["predicted_translation"]),
                reference=str(prediction_row["ground_truth_translation"]),
                terminology=selected_terms,
                term_groups=(),
            )
            if coverage is not None:
                metrics[f"{metric_set.name}_target_term_coverage"] = coverage
            variant_coverage = compute_variant_aware_target_term_coverage(
                prediction=str(prediction_row["predicted_translation"]),
                reference=str(prediction_row["ground_truth_translation"]),
                terminology=selected_terms,
                term_groups=(),
            )
            if variant_coverage is not None:
                metrics[f"{metric_set.name}_variant_aware_target_term_coverage"] = (
                    variant_coverage
                )
        return {**prediction_row, "metrics": metrics, "evaluation_error": ""}
    except Exception as exc:
        return {
            **prediction_row,
            "metrics": {},
            "evaluation_error": f"{type(exc).__name__}: {exc}",
        }


class ParallelRowsLoader:
    def __init__(self, dataset_dir: Path) -> None:
        self.dataset_dir = dataset_dir
        self._cache: dict[Path, tuple[dict[str, dict[str, str]], dict[str, dict[str, str]]]] = {}

    def rows_for_manifest(
        self,
        manifest_row: dict[str, Any],
    ) -> tuple[dict[str, str], dict[str, str]]:
        direction = str(manifest_row.get("direction") or "")
        direction_dir = self.dataset_dir / direction if direction else self.dataset_dir
        source_rows, target_rows = self._rows_for_dir(direction_dir)
        return (
            source_rows[str(manifest_row["source_row_id"])],
            target_rows[str(manifest_row["target_row_id"])],
        )

    def _rows_for_dir(
        self,
        direction_dir: Path,
    ) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]]]:
        if direction_dir not in self._cache:
            self._cache[direction_dir] = (
                load_rows_by_id(direction_dir / "source.csv"),
                load_rows_by_id(direction_dir / "target.csv"),
            )
        return self._cache[direction_dir]


def build_experiment_summary(
    *,
    config: ExperimentPipelineConfig,
    benchmark_builds: tuple[BenchmarkBuildResult, ...],
    score_paths: list[Path],
) -> dict[str, Any]:
    score_rows = [row for path in score_paths for row in load_jsonl(path)]
    return {
        "name": config.name,
        "run_dir": portable_path(config.output.run_dir),
        "benchmark_builds": [
            {
                "name": build.name,
                "output_dir": portable_path(build.output_dir),
                "rows": build.row_count,
                "directions": build.direction_count,
                "manifest": portable_path(build.combined_manifest_path),
                "metadata": portable_path(build.metadata_path),
            }
            for build in benchmark_builds
        ],
        "row_count": len(score_rows),
        "error_count": sum(
            bool(row.get("error") or row.get("evaluation_error")) for row in score_rows
        ),
        "by_model": grouped_metric_summaries(score_rows, "model_run"),
        "by_build": grouped_metric_summaries(score_rows, "build_name"),
        "by_direction": grouped_metric_summaries(score_rows, "direction"),
        "by_target_language": grouped_metric_summaries(score_rows, "target_language_code"),
    }


def grouped_metric_summaries(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[group_value(row, key)].append(row)
    return {value: metric_summary(group_rows) for value, group_rows in sorted(grouped.items())}


def metric_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    metric_names = sorted(
        {
            metric_name
            for row in rows
            for metric_name in row.get("metrics", {})
            if isinstance(row.get("metrics"), dict)
        }
    )
    return {
        "row_count": len(rows),
        "error_count": sum(bool(row.get("error") or row.get("evaluation_error")) for row in rows),
        "metrics": {
            metric_name: numeric_summary(
                [
                    float(row["metrics"][metric_name])
                    for row in rows
                    if isinstance(row.get("metrics"), dict) and metric_name in row["metrics"]
                ]
            )
            for metric_name in metric_names
        },
    }


def render_summary_markdown(summary: dict[str, Any]) -> str:
    lines = [
        f"# Benchmark Experiment Summary: {summary['name']}",
        "",
        f"**Run directory:** `{summary['run_dir']}`  ",
        f"**Scored rows:** `{summary['row_count']}`  ",
        f"**Rows with errors:** `{summary['error_count']}`",
        "",
        "## Benchmark Builds",
        "",
    ]
    lines.extend(
        render_markdown_table(
            headers=["Build", "Rows", "Directions", "Output", "Manifest", "Metadata"],
            rows=[
                [
                    build["name"],
                    build["rows"],
                    build["directions"],
                    f"`{build['output_dir']}`",
                    f"`{build['manifest']}`",
                    f"`{build['metadata']}`",
                ]
                for build in summary["benchmark_builds"]
            ],
        )
    )
    lines.extend(render_group_section("Model Results", summary["by_model"]))
    lines.extend(render_group_section("Direction Results", summary["by_direction"]))
    lines.extend(render_group_section("Target Language Results", summary["by_target_language"]))
    return "\n".join(lines).rstrip() + "\n"


def render_group_section(title: str, groups: dict[str, Any]) -> list[str]:
    metric_names = sorted(
        {
            metric_name
            for group_summary in groups.values()
            for metric_name in group_summary.get("metrics", {})
        }
    )
    headers = ["Group", "Rows", "Errors", *metric_names]
    rows = []
    for name, group_summary in groups.items():
        rows.append(
            [
                name,
                group_summary["row_count"],
                group_summary["error_count"],
                *[
                    group_summary.get("metrics", {}).get(metric_name, {}).get("mean", "")
                    for metric_name in metric_names
                ],
            ]
        )
    return [f"## {title}", "", *render_markdown_table(headers, rows)]


def render_markdown_table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    def format_cell(value: Any) -> str:
        return str(value).replace("|", "\\|").replace("\n", " ")

    formatted_headers = [format_cell(header) for header in headers]
    formatted_rows = [[format_cell(value) for value in row] for row in rows]
    separator = ["---" for _ in headers]
    lines = [
        "| " + " | ".join(formatted_headers) + " |",
        "| " + " | ".join(separator) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in formatted_rows)
    lines.append("")
    return lines


def predictions_output_path(
    config: ExperimentPipelineConfig,
    model_run: ModelRunConfig,
    build: BenchmarkBuildResult,
) -> Path:
    return config.output.run_dir / "predictions" / slugify(model_run.name) / f"{build.name}.jsonl"


def scores_output_path(
    config: ExperimentPipelineConfig,
    model_run: ModelRunConfig,
    build: BenchmarkBuildResult,
) -> Path:
    return config.output.run_dir / "scores" / slugify(model_run.name) / f"{build.name}.jsonl"


def load_rows_by_id(csv_path: Path) -> dict[str, dict[str, str]]:
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        return {str(row["id"]): row for row in csv.DictReader(handle)}


def discover_combined_manifest(output_dir: Path) -> Path:
    manifests = sorted(output_dir.glob("*-directions-*-manifest.jsonl"))
    if len(manifests) != 1:
        raise ValueError(f"Expected one combined manifest in {output_dir}, found {len(manifests)}.")
    return manifests[0]


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def manifest_key(row: dict[str, Any]) -> tuple[str, str]:
    return (str(row.get("source_id") or ""), str(row.get("direction") or ""))


def prediction_key(row: dict[str, Any]) -> tuple[str, str]:
    return (str(row.get("source_id") or ""), str(row.get("direction") or ""))


def resolve_translation_domain(requested: str, manifest_rows: list[dict[str, Any]]) -> str:
    if requested != "auto":
        return requested
    datasets = {str(row.get("dataset") or "").lower() for row in manifest_rows}
    directions = {str(row.get("direction") or "").lower() for row in manifest_rows}
    combined = " ".join(sorted(datasets | directions))
    if "google" in combined or "patent" in combined:
        return "chemistry"
    if "eurolex" in combined or "jrc" in combined or "acquis" in combined:
        return "legal"
    return "generic"


def group_value(row: dict[str, Any], key: str) -> str:
    value: Any = row
    for part in key.split("."):
        if not isinstance(value, dict):
            return "unknown"
        value = value.get(part)
    return str(value or "unknown")


def portable_path(path: Path) -> str:
    try:
        return path.relative_to(Path.cwd()).as_posix()
    except ValueError:
        return str(path)


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9_.-]+", "-", value.lower()).strip("-") or "run"
