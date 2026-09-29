from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 fallback when installed
    import tomli as tomllib  # type: ignore[no-redef]

from chem_machine_translation.config import DEFAULT_MODEL
from chem_machine_translation.evaluation.metrics import (
    COMET_DEFAULT_MODEL,
    DEFAULT_METRIC_NAMES,
    DEFAULT_TERMINOLOGY_TERM_GROUPS,
    GENERAL_METRIC_NAMES,
    MQM_DEFAULT_MODEL,
    TERMINOLOGY_TERM_GROUPS,
)

SUPPORTED_TRANSLATORS = {"dry-run", "one-shot"}
SUPPORTED_PROVIDERS = {"openai", "opencode", "openai-compatible"}
SUPPORTED_TRANSLATION_DOMAINS = {"auto", "chemistry", "legal", "generic"}


@dataclass(frozen=True)
class ExperimentBenchmarkConfig:
    config_path: Path
    run_generation: bool = True


@dataclass(frozen=True)
class ModelRunConfig:
    name: str
    translator: str = "one-shot"
    provider: str = "openai"
    model: str = DEFAULT_MODEL
    temperature: float = 0.0
    provider_base_url: str | None = None
    provider_timeout: float | None = None
    llm_thinking: str | None = None
    llm_reasoning_effort: str | None = None
    prediction_workers: int = 1
    translation_domain: str = "auto"
    use_manifest_terminology: bool = False
    terminology_groups: tuple[str, ...] = DEFAULT_TERMINOLOGY_TERM_GROUPS
    max_manifest_terminology_terms: int | None = None
    resume: bool = True


@dataclass(frozen=True)
class TerminologyMetricSetConfig:
    name: str
    term_groups: tuple[str, ...] = DEFAULT_TERMINOLOGY_TERM_GROUPS
    require_verified: bool = False


@dataclass(frozen=True)
class EvaluationRunConfig:
    name: str
    metrics: tuple[str, ...] = DEFAULT_METRIC_NAMES
    terminology_groups: tuple[str, ...] = DEFAULT_TERMINOLOGY_TERM_GROUPS
    terminology_metric_sets: tuple[TerminologyMetricSetConfig, ...] = ()
    comet_model: str = COMET_DEFAULT_MODEL
    comet_batch_size: int = 8
    comet_gpus: int = 0
    fsp_mqm_model: str = MQM_DEFAULT_MODEL
    fsp_mqm_timeout: float = 120.0


@dataclass(frozen=True)
class ExperimentOutputConfig:
    run_dir: Path
    overwrite_scores: bool = True


@dataclass(frozen=True)
class ExperimentPipelineConfig:
    name: str
    benchmark: ExperimentBenchmarkConfig
    model_runs: tuple[ModelRunConfig, ...]
    evaluation: EvaluationRunConfig
    output: ExperimentOutputConfig


def load_experiment_config(path: Path | str) -> ExperimentPipelineConfig:
    config_path = Path(path)
    with config_path.open("rb") as handle:
        payload = tomllib.load(handle)
    config = experiment_config_from_mapping(payload, base_dir=config_path.parent)
    validate_experiment_config(config)
    return config


def experiment_config_from_mapping(
    payload: dict[str, Any],
    *,
    base_dir: Path,
) -> ExperimentPipelineConfig:
    return ExperimentPipelineConfig(
        name=str(payload.get("name") or "benchmark_experiment"),
        benchmark=benchmark_config_from_mapping(
            dict(payload.get("benchmark") or {}),
            base_dir=base_dir,
        ),
        model_runs=tuple(
            model_run_config_from_mapping(dict(model_run), base_dir=base_dir)
            for model_run in payload.get("model_runs", [])
        ),
        evaluation=evaluation_config_from_mapping(
            dict(payload.get("evaluation") or {}),
            base_dir=base_dir,
        ),
        output=output_config_from_mapping(dict(payload.get("output") or {}), base_dir=base_dir),
    )


def benchmark_config_from_mapping(
    payload: dict[str, Any],
    *,
    base_dir: Path,
) -> ExperimentBenchmarkConfig:
    return ExperimentBenchmarkConfig(
        config_path=required_path(payload.get("config"), base_dir=base_dir, field_name="config"),
        run_generation=bool(payload.get("run_generation", payload.get("run", True))),
    )


def model_run_config_from_mapping(
    payload: dict[str, Any],
    *,
    base_dir: Path,
) -> ModelRunConfig:
    if "config" in payload:
        referenced = load_mapping_from_file(
            required_path(payload.get("config"), base_dir=base_dir, field_name="model_run.config")
        )
        referenced.update({key: value for key, value in payload.items() if key != "config"})
        payload = referenced
    return ModelRunConfig(
        name=str(payload.get("name") or payload.get("model") or "model_run"),
        translator=str(payload.get("translator") or "one-shot"),
        provider=str(payload.get("provider") or "openai"),
        model=str(payload.get("model") or DEFAULT_MODEL),
        temperature=float(payload.get("temperature") or 0.0),
        provider_base_url=optional_string(payload.get("provider_base_url")),
        provider_timeout=optional_float(payload.get("provider_timeout")),
        llm_thinking=optional_string(payload.get("llm_thinking")),
        llm_reasoning_effort=optional_string(payload.get("llm_reasoning_effort")),
        prediction_workers=max(1, int(payload.get("prediction_workers") or 1)),
        translation_domain=str(payload.get("translation_domain") or "auto"),
        use_manifest_terminology=bool(payload.get("use_manifest_terminology", False)),
        terminology_groups=string_tuple(
            payload.get("terminology_groups") or DEFAULT_TERMINOLOGY_TERM_GROUPS
        ),
        max_manifest_terminology_terms=optional_int(
            payload.get("max_manifest_terminology_terms")
        ),
        resume=bool(payload.get("resume", True)),
    )


def evaluation_config_from_mapping(
    payload: dict[str, Any],
    *,
    base_dir: Path,
) -> EvaluationRunConfig:
    if "config" in payload:
        referenced = load_mapping_from_file(
            required_path(payload.get("config"), base_dir=base_dir, field_name="evaluation.config")
        )
        referenced.update({key: value for key, value in payload.items() if key != "config"})
        payload = referenced
    return EvaluationRunConfig(
        name=str(payload.get("name") or "default"),
        metrics=string_tuple(payload.get("metrics") or DEFAULT_METRIC_NAMES),
        terminology_groups=string_tuple(
            payload.get("terminology_groups") or DEFAULT_TERMINOLOGY_TERM_GROUPS
        ),
        terminology_metric_sets=tuple(
            terminology_metric_set_from_mapping(dict(item))
            for item in payload.get("terminology_metric_sets", [])
        ),
        comet_model=str(payload.get("comet_model") or COMET_DEFAULT_MODEL),
        comet_batch_size=int(payload.get("comet_batch_size") or 8),
        comet_gpus=int(payload.get("comet_gpus") or 0),
        fsp_mqm_model=str(payload.get("fsp_mqm_model") or MQM_DEFAULT_MODEL),
        fsp_mqm_timeout=float(payload.get("fsp_mqm_timeout") or 120.0),
    )


def terminology_metric_set_from_mapping(payload: dict[str, Any]) -> TerminologyMetricSetConfig:
    return TerminologyMetricSetConfig(
        name=str(payload.get("name") or "").strip(),
        term_groups=string_tuple(payload.get("term_groups") or DEFAULT_TERMINOLOGY_TERM_GROUPS),
        require_verified=bool(payload.get("require_verified", False)),
    )


def output_config_from_mapping(
    payload: dict[str, Any],
    *,
    base_dir: Path,
) -> ExperimentOutputConfig:
    return ExperimentOutputConfig(
        run_dir=required_path(payload.get("run_dir"), base_dir=base_dir, field_name="run_dir"),
        overwrite_scores=bool(payload.get("overwrite_scores", True)),
    )


def load_mapping_from_file(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        return dict(tomllib.load(handle))


def validate_experiment_config(config: ExperimentPipelineConfig) -> None:
    if not config.benchmark.config_path.exists():
        raise FileNotFoundError(f"Benchmark config not found: {config.benchmark.config_path}")
    if not config.model_runs:
        raise ValueError("Experiment config must define at least one model run.")
    for model_run in config.model_runs:
        if model_run.translator not in SUPPORTED_TRANSLATORS:
            raise ValueError(f"Unsupported translator: {model_run.translator}")
        if model_run.provider not in SUPPORTED_PROVIDERS:
            raise ValueError(f"Unsupported provider: {model_run.provider}")
        if model_run.translation_domain not in SUPPORTED_TRANSLATION_DOMAINS:
            raise ValueError(f"Unsupported translation domain: {model_run.translation_domain}")
        validate_terms("terminology_groups", model_run.terminology_groups, TERMINOLOGY_TERM_GROUPS)
    validate_terms("metrics", config.evaluation.metrics, GENERAL_METRIC_NAMES)
    validate_terms(
        "terminology_groups",
        config.evaluation.terminology_groups,
        TERMINOLOGY_TERM_GROUPS,
    )
    metric_set_names = set()
    for metric_set in config.evaluation.terminology_metric_sets:
        if not metric_set.name:
            raise ValueError("Terminology metric sets require a name.")
        if metric_set.name in metric_set_names:
            raise ValueError(f"Duplicate terminology metric set name: {metric_set.name}")
        metric_set_names.add(metric_set.name)
        validate_terms(
            f"terminology metric set {metric_set.name}",
            metric_set.term_groups,
            TERMINOLOGY_TERM_GROUPS,
        )


def validate_terms(name: str, values: tuple[str, ...], supported: tuple[str, ...]) -> None:
    unsupported = sorted(set(values) - set(supported))
    if unsupported:
        raise ValueError(f"Unsupported {name}: {', '.join(unsupported)}")


def required_path(value: Any, *, base_dir: Path, field_name: str) -> Path:
    if value in (None, ""):
        raise ValueError(f"Missing required path field: {field_name}")
    return resolve_config_path(Path(str(value)), base_dir)


def resolve_config_path(path: Path, base_dir: Path) -> Path:
    if path.is_absolute():
        return path
    return (config_path_root(base_dir) / path).resolve()


def config_path_root(base_dir: Path) -> Path:
    if base_dir.name in {"experiments", "model_runs", "evaluation"} and base_dir.parent.name in {
        "config",
        "configs",
    }:
        return base_dir.parent.parent
    return base_dir


def string_tuple(value: Any) -> tuple[str, ...]:
    if value in (None, ""):
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, list | tuple):
        return tuple(str(item) for item in value)
    raise TypeError(f"Expected string or list of strings, got {type(value).__name__}")


def optional_string(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value)


def optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    return int(value)


def optional_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    return float(value)
