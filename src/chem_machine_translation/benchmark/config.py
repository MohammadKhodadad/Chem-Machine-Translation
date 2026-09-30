from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 fallback when installed
    import tomli as tomllib  # type: ignore[no-redef]

from chem_machine_translation.config import DEFAULT_LLM_MAX_OUTPUT_TOKENS, DEFAULT_MODEL
from chem_machine_translation.data.terminology import DEFAULT_SPACY_MODEL

SUPPORTED_DOMAINS = {"chemistry", "google_patents", "jrc", "legal"}
SUPPORTED_SOURCE_KINDS = {"google_patents_snapshot", "jrc_acquis_snapshot"}
SUPPORTED_SELECTION_MODES = {"per_direction", "anchored"}
SUPPORTED_CANDIDATE_EXTRACTORS = {
    "external_dataset",
    "llm_chemistry",
    "llm_legal",
    "stanza_ud",
    "xlmr_nobi",
    "spacy",
}
SUPPORTED_EXTERNAL_EVIDENCE_SOURCES = {
    "iate",
    "local_iate",
    "wikidata",
    "wikipedia",
    "pubchem",
    "chebi",
    "chembl",
    "mesh",
    "nci",
    "agrovoc",
    "unterm",
}


@dataclass(frozen=True)
class BenchmarkBuildConfig:
    name: str
    kind: str
    source_pairs_jsonl: Path
    output_dir: Path
    languages: tuple[str, ...]
    limit: int
    selection_mode: str = "per_direction"
    min_input_tokens: int | None = None
    max_input_tokens: int | None = None
    anchor_limit: int | None = None
    bidirectional: bool = False


@dataclass(frozen=True)
class BenchmarkTerminologyConfig:
    domain: str
    candidate_max_terms: int = 40
    refined_max_terms: int = 8
    model: str = DEFAULT_MODEL
    base_url: str | None = None
    api_mode: str | None = None
    max_output_tokens: int = DEFAULT_LLM_MAX_OUTPUT_TOKENS
    thinking: str | None = None
    reasoning_effort: str | None = None
    candidate_extractors: tuple[str, ...] = ()
    external_dataset_manifest: Path | None = None
    external_dataset_source: str = "external_dataset"
    external_evidence_sources: tuple[str, ...] = ()
    llm_curation: bool = True
    workers: int = 1
    legal_workers: int | None = None
    stanza_workers: int | None = None
    nobi_model: str = "tthhanh/xlm-ate-nobi-en-nes"
    spacy_model: str = DEFAULT_SPACY_MODEL
    cache_path: Path | None = None
    legal_cache_path: Path | None = None
    stanza_cache_path: Path | None = None
    local_iate_path: Path | None = None
    openai_timeout: float = 120.0

    @property
    def resolved_legal_workers(self) -> int:
        return self.legal_workers or self.workers

    @property
    def resolved_stanza_workers(self) -> int:
        return self.stanza_workers or self.workers


@dataclass(frozen=True)
class BenchmarkCheckpointConfig:
    enabled: bool = True
    work_dir: Path = Path("benchmark_work")
    resume: bool = True
    run_id: str = "auto"
    reuse_selection: bool = True
    reuse_candidate_extraction: bool = True
    reuse_external_evidence_enrichment: bool = True
    reuse_llm_curation: bool = True
    reuse_manifest: bool = True


@dataclass(frozen=True)
class BenchmarkGenerationConfig:
    name: str
    domain: str
    builds: tuple[BenchmarkBuildConfig, ...]
    terminology: BenchmarkTerminologyConfig
    checkpoint: BenchmarkCheckpointConfig = BenchmarkCheckpointConfig()


def load_benchmark_config(
    path: Path | str,
    *,
    validate_paths: bool = True,
) -> BenchmarkGenerationConfig:
    config_path = Path(path)
    with config_path.open("rb") as handle:
        payload = tomllib.load(handle)
    config = benchmark_config_from_mapping(payload, base_dir=config_path.parent)
    validate_benchmark_config(config, validate_paths=validate_paths)
    return config


def benchmark_config_from_mapping(
    payload: dict[str, Any],
    *,
    base_dir: Path | None = None,
) -> BenchmarkGenerationConfig:
    base_dir = base_dir or Path.cwd()
    domain = str(payload.get("domain") or "").strip()
    terminology_payload = dict(payload.get("terminology") or {})
    terminology = terminology_config_from_mapping(
        terminology_payload,
        domain=domain,
        base_dir=base_dir,
    )
    checkpoint = checkpoint_config_from_mapping(
        dict(payload.get("checkpoint") or {}),
        base_dir=base_dir,
    )
    builds = build_configs_from_mapping(payload, domain=domain, base_dir=base_dir)
    return BenchmarkGenerationConfig(
        name=str(payload.get("name") or "benchmark_generation"),
        domain=domain,
        builds=tuple(builds),
        terminology=terminology,
        checkpoint=checkpoint,
    )


def terminology_config_from_mapping(
    payload: dict[str, Any],
    *,
    domain: str,
    base_dir: Path,
) -> BenchmarkTerminologyConfig:
    return BenchmarkTerminologyConfig(
        domain=str(payload.get("domain") or domain),
        candidate_max_terms=int(payload.get("candidate_max_terms") or 40),
        refined_max_terms=int(payload.get("refined_max_terms") or 8),
        model=str(payload.get("model") or DEFAULT_MODEL),
        base_url=optional_string(payload.get("base_url")),
        api_mode=optional_string(payload.get("api_mode")),
        max_output_tokens=int(payload.get("max_output_tokens") or DEFAULT_LLM_MAX_OUTPUT_TOKENS),
        thinking=optional_string(payload.get("thinking")),
        reasoning_effort=optional_string(payload.get("reasoning_effort")),
        candidate_extractors=string_tuple(payload.get("candidate_extractors")),
        external_dataset_manifest=optional_path(
            payload.get("external_dataset_manifest"),
            base_dir=base_dir,
        ),
        external_dataset_source=str(payload.get("external_dataset_source") or "external_dataset"),
        external_evidence_sources=string_tuple(payload.get("external_evidence_sources")),
        llm_curation=bool(payload.get("llm_curation", True)),
        workers=int(payload.get("workers") or 1),
        legal_workers=optional_int(payload.get("legal_workers")),
        stanza_workers=optional_int(payload.get("stanza_workers")),
        nobi_model=str(payload.get("nobi_model") or "tthhanh/xlm-ate-nobi-en-nes"),
        spacy_model=str(payload.get("spacy_model") or DEFAULT_SPACY_MODEL),
        cache_path=optional_path(payload.get("cache_path"), base_dir=base_dir),
        legal_cache_path=optional_path(payload.get("legal_cache_path"), base_dir=base_dir),
        stanza_cache_path=optional_path(payload.get("stanza_cache_path"), base_dir=base_dir),
        local_iate_path=optional_path(payload.get("local_iate_path"), base_dir=base_dir),
        openai_timeout=float(payload.get("openai_timeout") or 120.0),
    )


def checkpoint_config_from_mapping(
    payload: dict[str, Any],
    *,
    base_dir: Path,
) -> BenchmarkCheckpointConfig:
    reuse_payload = dict(payload.get("reuse") or {})
    return BenchmarkCheckpointConfig(
        enabled=bool(payload.get("enabled", True)),
        work_dir=optional_path(payload.get("work_dir"), base_dir=base_dir)
        or resolve_config_path(Path("benchmark_work"), base_dir),
        resume=bool(payload.get("resume", True)),
        run_id=str(payload.get("run_id") or "auto"),
        reuse_selection=bool(reuse_payload.get("selection", True)),
        reuse_candidate_extraction=bool(reuse_payload.get("candidate_extraction", True)),
        reuse_external_evidence_enrichment=bool(
            reuse_payload.get("external_evidence_enrichment", True)
        ),
        reuse_llm_curation=bool(reuse_payload.get("llm_curation", True)),
        reuse_manifest=bool(reuse_payload.get("manifest", True)),
    )


def build_configs_from_mapping(
    payload: dict[str, Any],
    *,
    domain: str,
    base_dir: Path,
) -> list[BenchmarkBuildConfig]:
    selection = dict(payload.get("selection") or {})
    if "source" in payload:
        source = dict(payload["source"])
        return [
            build_config_from_mapping(
                source,
                domain=domain,
                selection=selection,
                base_dir=base_dir,
                default_name=str(payload.get("name") or "benchmark"),
            )
        ]
    builds = payload.get("builds")
    if not isinstance(builds, list) or not builds:
        raise ValueError("Benchmark config must define either [source] or [[builds]].")
    return [
        build_config_from_mapping(
            dict(build),
            domain=domain,
            selection=selection,
            base_dir=base_dir,
            default_name=f"build_{index}",
        )
        for index, build in enumerate(builds, start=1)
    ]


def build_config_from_mapping(
    payload: dict[str, Any],
    *,
    domain: str,
    selection: dict[str, Any],
    base_dir: Path,
    default_name: str,
) -> BenchmarkBuildConfig:
    kind = str(
        payload.get("kind")
        or selection.get("kind")
        or default_source_kind_for_domain(domain)
    )
    languages = string_tuple(payload.get("languages") or selection.get("languages"))
    limit = int(payload.get("limit") or selection.get("limit") or 250)
    anchor_limit = optional_int(payload.get("anchor_limit") or selection.get("anchor_limit"))
    selection_mode = str(
        payload.get("mode")
        or payload.get("selection_mode")
        or selection.get("mode")
        or selection.get("selection_mode")
        or default_selection_mode(anchor_limit=anchor_limit)
    )
    return BenchmarkBuildConfig(
        name=str(payload.get("name") or default_name),
        kind=kind,
        source_pairs_jsonl=required_path(
            payload.get("source_pairs_jsonl"),
            base_dir=base_dir,
            field_name="source_pairs_jsonl",
        ),
        output_dir=required_path(
            payload.get("output_dir"),
            base_dir=base_dir,
            field_name="output_dir",
        ),
        languages=languages,
        limit=limit,
        selection_mode=selection_mode,
        min_input_tokens=optional_int(
            payload.get("min_input_tokens") or selection.get("min_input_tokens")
        ),
        max_input_tokens=optional_int(
            payload.get("max_input_tokens") or selection.get("max_input_tokens")
        ),
        anchor_limit=anchor_limit,
        bidirectional=bool(payload.get("bidirectional", selection.get("bidirectional", False))),
    )


def validate_benchmark_config(
    config: BenchmarkGenerationConfig,
    *,
    validate_paths: bool = True,
) -> None:
    if config.domain not in SUPPORTED_DOMAINS:
        raise ValueError(f"Unsupported benchmark domain: {config.domain}")
    if not config.builds:
        raise ValueError("At least one benchmark build is required.")
    if not str(config.checkpoint.work_dir):
        raise ValueError("checkpoint.work_dir must not be empty.")
    validate_terms(
        "candidate_extractors",
        config.terminology.candidate_extractors,
        SUPPORTED_CANDIDATE_EXTRACTORS,
    )
    validate_terms(
        "external_evidence_sources",
        config.terminology.external_evidence_sources,
        SUPPORTED_EXTERNAL_EVIDENCE_SOURCES,
    )
    if config.terminology.candidate_max_terms < 1:
        raise ValueError("terminology.candidate_max_terms must be positive.")
    if config.terminology.refined_max_terms < 1:
        raise ValueError("terminology.refined_max_terms must be positive.")
    if "external_dataset" in config.terminology.candidate_extractors:
        manifest = config.terminology.external_dataset_manifest
        if manifest is None:
            raise ValueError(
                "terminology.external_dataset_manifest is required when "
                "candidate_extractors includes 'external_dataset'."
            )
        if validate_paths and not manifest.exists():
            raise FileNotFoundError(f"External dataset manifest not found: {manifest}")
        if not config.terminology.external_dataset_source.strip():
            raise ValueError("terminology.external_dataset_source must not be empty.")
    for build in config.builds:
        if build.kind not in SUPPORTED_SOURCE_KINDS:
            raise ValueError(f"Unsupported source kind: {build.kind}")
        if build.selection_mode not in SUPPORTED_SELECTION_MODES:
            raise ValueError(f"Unsupported selection mode: {build.selection_mode}")
        if not build.languages:
            raise ValueError(f"Build {build.name!r} must define at least one language.")
        if build.limit < 1:
            raise ValueError(f"Build {build.name!r} limit must be positive.")
        if build.selection_mode == "anchored":
            if build.kind != "jrc_acquis_snapshot":
                raise ValueError("mode = 'anchored' is only supported for JRC snapshots.")
            if len(build.languages) < 2:
                raise ValueError(f"Build {build.name!r} needs at least two languages.")
            if build.anchor_limit is None or build.anchor_limit < 1:
                raise ValueError(f"Build {build.name!r} anchor_limit must be positive.")
        elif build.anchor_limit is not None:
            raise ValueError("anchor_limit requires mode = 'anchored'.")
        if validate_paths and not build.source_pairs_jsonl.exists():
            raise FileNotFoundError(f"Source snapshot not found: {build.source_pairs_jsonl}")


def validate_terms(name: str, values: tuple[str, ...], supported: set[str]) -> None:
    unsupported = sorted(set(values) - supported)
    if unsupported:
        raise ValueError(f"Unsupported {name}: {', '.join(unsupported)}")


def default_source_kind_for_domain(domain: str) -> str:
    if domain in {"jrc", "legal"}:
        return "jrc_acquis_snapshot"
    return "google_patents_snapshot"


def default_selection_mode(*, anchor_limit: int | None) -> str:
    if anchor_limit is not None:
        return "anchored"
    return "per_direction"


def required_path(value: Any, *, base_dir: Path, field_name: str) -> Path:
    if value in (None, ""):
        raise ValueError(f"Missing required path field: {field_name}")
    return resolve_config_path(Path(str(value)), base_dir)


def optional_path(value: Any, *, base_dir: Path) -> Path | None:
    if value in (None, ""):
        return None
    return resolve_config_path(Path(str(value)), base_dir)


def resolve_config_path(path: Path, base_dir: Path) -> Path:
    if path.is_absolute():
        return path
    return (config_path_root(base_dir) / path).resolve()


def config_path_root(base_dir: Path) -> Path:
    if base_dir.name == "benchmark" and base_dir.parent.name == "configs":
        return base_dir.parent.parent
    if base_dir.name == "benchmark_generation" and base_dir.parent.name in {"config", "configs"}:
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

