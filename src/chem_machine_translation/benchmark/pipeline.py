from __future__ import annotations

import csv
import hashlib
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from openai import OpenAI

from chem_machine_translation.benchmark.config import (
    BenchmarkBuildConfig,
    BenchmarkCheckpointConfig,
    BenchmarkGenerationConfig,
    BenchmarkTerminologyConfig,
    load_benchmark_config,
)
from chem_machine_translation.benchmark.metadata import write_benchmark_metadata
from chem_machine_translation.config import Settings, load_settings
from chem_machine_translation.data.terminology import (
    DatasetTerminologyGenerator,
    DatasetTerminologyTerm,
    LegalTerminologyGenerator,
    LLMTerminologyRefiner,
    dataset_term_from_json,
    deduplicate_terms,
    select_dataset_terms,
    select_legal_terms,
)
from chem_machine_translation.translation.iate import IATEClient, LocalIATEClient
from chem_machine_translation.utils.text import approximate_token_count, normalize_text

LANGUAGE_NAMES = {
    "de": "German",
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "ja": "Japanese",
    "nl": "Dutch",
    "pt": "Portuguese",
    "ru": "Russian",
    "zh": "Chinese",
}
TEXT_FIELD = "context"


@dataclass(frozen=True)
class BenchmarkBuildResult:
    name: str
    output_dir: Path
    direction_count: int
    row_count: int
    combined_manifest_path: Path
    metadata_path: Path


@dataclass(frozen=True)
class BenchmarkGenerationResult:
    name: str
    builds: tuple[BenchmarkBuildResult, ...]


@dataclass(frozen=True)
class TerminologyRuntime:
    chemistry_generator: DatasetTerminologyGenerator | None = None
    legal_generator: LegalTerminologyGenerator | None = None
    algorithmic_generator: DatasetTerminologyGenerator | None = None
    curator: LLMTerminologyRefiner | None = None


@dataclass(frozen=True)
class BenchmarkCheckpoint:
    root: Path
    enabled: bool
    resume: bool
    config: BenchmarkCheckpointConfig


def run_benchmark_config_file(path: Path | str) -> BenchmarkGenerationResult:
    return run_benchmark_generation(load_benchmark_config(path))


def run_benchmark_generation(
    config: BenchmarkGenerationConfig,
    *,
    settings: Settings | None = None,
    runtime: TerminologyRuntime | None = None,
) -> BenchmarkGenerationResult:
    settings = settings or load_settings()
    runtime = runtime or build_terminology_runtime(config.terminology, settings=settings)
    results = tuple(
        run_benchmark_build(
            build,
            benchmark_name=config.name,
            domain=config.domain,
            terminology=config.terminology,
            runtime=runtime,
            checkpoint=config.checkpoint,
        )
        for build in config.builds
    )
    return BenchmarkGenerationResult(name=config.name, builds=results)


def build_terminology_runtime(
    terminology: BenchmarkTerminologyConfig,
    *,
    settings: Settings | None = None,
) -> TerminologyRuntime:
    settings = settings or load_settings()
    client = build_openai_client(terminology, settings) if needs_llm_client(terminology) else None
    return TerminologyRuntime(
        chemistry_generator=build_chemistry_generator(terminology, client),
        legal_generator=build_legal_generator(terminology, client),
        algorithmic_generator=build_algorithmic_generator(terminology),
        curator=build_llm_curator(terminology, client),
    )


def needs_llm_client(terminology: BenchmarkTerminologyConfig) -> bool:
    return (
        "llm_chemistry" in terminology.candidate_extractors
        or "llm_legal" in terminology.candidate_extractors
        or terminology.llm_curation
    )


def build_openai_client(
    terminology: BenchmarkTerminologyConfig,
    settings: Settings,
) -> OpenAI:
    base_url = terminology.base_url or settings.openai_base_url
    api_key = openai_api_key_for_base_url(base_url, settings)
    if not api_key:
        raise ValueError("An OpenAI-compatible API key is required for LLM benchmark stages.")
    return OpenAI(
        api_key=api_key,
        base_url=base_url,
        timeout=terminology.openai_timeout,
    )


def openai_api_key_for_base_url(base_url: str | None, settings: Settings) -> str | None:
    if base_url and "api.openai.com" in base_url:
        return os.getenv("OPENAI_API_KEY")
    return settings.openai_api_key


def build_chemistry_generator(
    terminology: BenchmarkTerminologyConfig,
    client: Any | None,
) -> DatasetTerminologyGenerator | None:
    if terminology.domain not in {"chemistry", "google_patents"}:
        return None
    if not (
        set(terminology.candidate_extractors)
        & {"llm_chemistry", "stanza_ud", "xlmr_nobi", "spacy"}
    ):
        return None
    return DatasetTerminologyGenerator(
        client=client,
        model=terminology.model,
        max_terms=terminology.candidate_max_terms,
        use_llm="llm_chemistry" in terminology.candidate_extractors,
        llm_api_mode=terminology.api_mode or "responses",
        llm_max_output_tokens=terminology.max_output_tokens,
        llm_thinking=terminology.thinking,
        llm_reasoning_effort=terminology.reasoning_effort,
        use_stanza_extractor="stanza_ud" in terminology.candidate_extractors,
        use_nobi_extractor="xlmr_nobi" in terminology.candidate_extractors,
        nobi_model=terminology.nobi_model,
        use_spacy_extractor="spacy" in terminology.candidate_extractors,
        spacy_model=terminology.spacy_model,
        use_iate=uses_external_evidence_source(terminology, "iate", "local_iate"),
        iate_client=build_iate_client(terminology),
        iate_source_name=iate_source_name(terminology),
        use_wikidata=uses_external_evidence_source(terminology, "wikidata", "wikipedia"),
        use_pubchem=uses_external_evidence_source(terminology, "pubchem"),
        use_chebi=uses_external_evidence_source(terminology, "chebi"),
        use_chembl=uses_external_evidence_source(terminology, "chembl"),
        use_mesh=uses_external_evidence_source(terminology, "mesh"),
        use_nci=uses_external_evidence_source(terminology, "nci"),
        use_agrovoc=uses_external_evidence_source(terminology, "agrovoc"),
        cache_path=terminology.cache_path,
    )


def build_legal_generator(
    terminology: BenchmarkTerminologyConfig,
    client: Any | None,
) -> LegalTerminologyGenerator | None:
    if (
        terminology.domain not in {"jrc", "legal"}
        or "llm_legal" not in terminology.candidate_extractors
    ):
        return None
    if client is None:
        raise ValueError("A client is required for the legal LLM extractor.")
    return LegalTerminologyGenerator(
        client=client,
        model=terminology.model,
        max_terms=terminology.candidate_max_terms,
        use_iate=uses_external_evidence_source(terminology, "iate", "local_iate"),
        iate_client=build_iate_client(terminology),
        iate_source_name=iate_source_name(terminology),
        use_wikidata=uses_external_evidence_source(terminology, "wikidata", "wikipedia"),
        use_unterm=uses_external_evidence_source(terminology, "unterm"),
        cache_path=terminology.legal_cache_path or terminology.cache_path,
        llm_api_mode=terminology.api_mode or "responses",
        llm_max_output_tokens=terminology.max_output_tokens,
        llm_thinking=terminology.thinking,
        llm_reasoning_effort=terminology.reasoning_effort,
    )


def build_algorithmic_generator(
    terminology: BenchmarkTerminologyConfig,
) -> DatasetTerminologyGenerator | None:
    if not (set(terminology.candidate_extractors) & {"stanza_ud", "xlmr_nobi", "spacy"}):
        return None
    return DatasetTerminologyGenerator(
        max_terms=terminology.candidate_max_terms,
        use_llm=False,
        use_stanza_extractor="stanza_ud" in terminology.candidate_extractors,
        use_nobi_extractor="xlmr_nobi" in terminology.candidate_extractors,
        nobi_model=terminology.nobi_model,
        use_spacy_extractor="spacy" in terminology.candidate_extractors,
        spacy_model=terminology.spacy_model,
        use_iate=uses_external_evidence_source(terminology, "iate", "local_iate"),
        iate_client=build_iate_client(terminology),
        iate_source_name=iate_source_name(terminology),
        use_wikidata=uses_external_evidence_source(terminology, "wikidata", "wikipedia"),
        use_pubchem=uses_external_evidence_source(terminology, "pubchem"),
        use_chebi=uses_external_evidence_source(terminology, "chebi"),
        use_chembl=uses_external_evidence_source(terminology, "chembl"),
        use_mesh=uses_external_evidence_source(terminology, "mesh"),
        use_nci=uses_external_evidence_source(terminology, "nci"),
        use_agrovoc=uses_external_evidence_source(terminology, "agrovoc"),
        use_unterm=uses_external_evidence_source(terminology, "unterm"),
        cache_path=terminology.stanza_cache_path or terminology.cache_path,
    )


def build_llm_curator(
    terminology: BenchmarkTerminologyConfig,
    client: Any | None,
) -> LLMTerminologyRefiner | None:
    if not terminology.llm_curation:
        return None
    if client is None:
        raise ValueError("A client is required for the LLM terminology refiner.")
    return LLMTerminologyRefiner(
        client=client,
        model=terminology.model,
        api_mode=terminology.api_mode or "responses",
        max_output_tokens=terminology.max_output_tokens,
        thinking=terminology.thinking,
        reasoning_effort=terminology.reasoning_effort,
    )


def uses_external_evidence_source(
    terminology: BenchmarkTerminologyConfig,
    *names: str,
) -> bool:
    return bool(set(names) & set(terminology.external_evidence_sources))


def build_iate_client(
    terminology: BenchmarkTerminologyConfig,
) -> IATEClient | LocalIATEClient | None:
    if "local_iate" in terminology.external_evidence_sources:
        return LocalIATEClient(terminology.local_iate_path or Path("data/iate"))
    if "iate" in terminology.external_evidence_sources:
        return IATEClient()
    return None


def iate_source_name(terminology: BenchmarkTerminologyConfig) -> str:
    return "local_iate" if "local_iate" in terminology.external_evidence_sources else "iate"


def run_benchmark_build(
    build: BenchmarkBuildConfig,
    *,
    benchmark_name: str,
    domain: str,
    terminology: BenchmarkTerminologyConfig,
    runtime: TerminologyRuntime,
    checkpoint: BenchmarkCheckpointConfig | None = None,
) -> BenchmarkBuildResult:
    checkpoint_context = build_checkpoint_context(
        benchmark_name=benchmark_name,
        build=build,
        checkpoint=checkpoint,
    )
    pair_rows = load_or_select_source_pair_rows(build, checkpoint=checkpoint_context)
    build.output_dir.mkdir(parents=True, exist_ok=True)
    combined_rows = []
    for direction, rows in sorted(pair_rows.items()):
        print(f"Building {build.name} {direction}: {len(rows)} rows.", flush=True)
        direction_dir = build.output_dir / direction
        direction_dir.mkdir(parents=True, exist_ok=True)
        manifest_rows = [build_manifest_row(row=row, kind=build.kind) for row in rows]
        manifest_rows = attach_terminology_to_rows(
            manifest_rows,
            build=build,
            domain=domain,
            terminology=terminology,
            runtime=runtime,
            checkpoint=checkpoint_context,
        )
        write_csv(direction_dir / "source.csv", [row["_source_row"] for row in manifest_rows])
        write_csv(direction_dir / "target.csv", [row["_target_row"] for row in manifest_rows])
        manifest_path = direction_dir / manifest_filename(build.kind, direction, len(manifest_rows))
        write_manifest(manifest_path, manifest_rows)
        combined_rows.extend(manifest_rows)

    combined_manifest_path = build.output_dir / combined_manifest_filename(
        build.kind,
        len(pair_rows),
        len(combined_rows),
    )
    write_manifest(combined_manifest_path, combined_rows)
    metadata_path = build.output_dir / "metadata.json"
    write_benchmark_metadata(metadata_path, rows=combined_rows, build=build)
    return BenchmarkBuildResult(
        name=build.name,
        output_dir=build.output_dir,
        direction_count=len(pair_rows),
        row_count=len(combined_rows),
        combined_manifest_path=combined_manifest_path,
        metadata_path=metadata_path,
    )


def build_checkpoint_context(
    *,
    benchmark_name: str,
    build: BenchmarkBuildConfig,
    checkpoint: BenchmarkCheckpointConfig | None,
) -> BenchmarkCheckpoint:
    checkpoint = checkpoint or BenchmarkCheckpointConfig()
    root = checkpoint.work_dir / slugify_path_part(benchmark_name) / slugify_path_part(build.name)
    if checkpoint.run_id != "auto":
        root = root / slugify_path_part(checkpoint.run_id)
    return BenchmarkCheckpoint(
        root=root,
        enabled=checkpoint.enabled,
        resume=checkpoint.resume,
        config=checkpoint,
    )


def load_or_select_source_pair_rows(
    build: BenchmarkBuildConfig,
    *,
    checkpoint: BenchmarkCheckpoint,
) -> dict[str, list[dict[str, Any]]]:
    stage_hash = stable_hash(
        {
            "stage": "selection",
            "build": checkpoint_build_payload(build),
        }
    )
    cached = read_stage_jsonl(
        checkpoint=checkpoint,
        stage_name="selection",
        relative_path=Path("01_selected_rows.jsonl"),
        expected_hash=stage_hash,
        reuse=checkpoint.config.reuse_selection,
    )
    if cached is not None:
        return group_source_pair_rows_by_direction(cached)

    selected = select_source_pair_rows(build)
    rows = [row for direction in sorted(selected) for row in selected[direction]]
    write_stage_jsonl(
        checkpoint=checkpoint,
        stage_name="selection",
        relative_path=Path("01_selected_rows.jsonl"),
        rows=rows,
        stage_hash=stage_hash,
    )
    return selected


def group_source_pair_rows_by_direction(
    rows: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    selected: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        selected.setdefault(str(row["language_pair"]), []).append(row)
    return {direction: selected[direction] for direction in sorted(selected)}


def select_source_pair_rows(build: BenchmarkBuildConfig) -> dict[str, list[dict[str, Any]]]:
    if build.selection_mode == "anchored" or build.anchor_limit is not None:
        return select_anchor_source_pair_rows(build)

    selected: dict[str, list[dict[str, Any]]] = {}
    language_filter = set(build.languages)
    with build.source_pairs_jsonl.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = normalize_source_pair_row(json.loads(line), kind=build.kind)
            if (
                row["source_language"] not in language_filter
                or row["target_language"] not in language_filter
            ):
                continue
            if not row_passes_token_bounds(row, build):
                continue
            direction = row["language_pair"]
            selected.setdefault(direction, [])
            if len(selected[direction]) < build.limit:
                selected[direction].append(row)
    if build.bidirectional:
        selected = add_bidirectional_pair_rows(selected)
    return {direction: rows for direction, rows in selected.items() if rows}


def select_anchor_source_pair_rows(build: BenchmarkBuildConfig) -> dict[str, list[dict[str, Any]]]:
    if build.kind != "jrc_acquis_snapshot":
        raise ValueError("mode = 'anchored' is only supported for JRC anchored source snapshots.")

    language_filter = set(build.languages)
    expected_directions = expected_language_directions(build.languages)
    rows: list[dict[str, Any]] = []
    directions_by_anchor: dict[str, set[str]] = {}
    anchor_order: list[str] = []
    seen_anchors: set[str] = set()
    with build.source_pairs_jsonl.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = normalize_source_pair_row(json.loads(line), kind=build.kind)
            if (
                row["source_language"] not in language_filter
                or row["target_language"] not in language_filter
            ):
                continue
            if not row_passes_token_bounds(row, build):
                continue
            anchor_id = str(row.get("anchor_id") or "")
            if not anchor_id:
                raise ValueError("mode = 'anchored' requires rows with anchor_id.")
            rows.append(row)
            directions_by_anchor.setdefault(anchor_id, set()).add(row["language_pair"])
            if anchor_id not in seen_anchors:
                seen_anchors.add(anchor_id)
                anchor_order.append(anchor_id)

    complete_anchors = [
        anchor_id
        for anchor_id in anchor_order
        if expected_directions <= directions_by_anchor.get(anchor_id, set())
    ]
    anchor_limit = build.anchor_limit or 0
    if len(complete_anchors) < anchor_limit:
        raise ValueError(
            f"Requested {anchor_limit} complete anchors, but only found "
            f"{len(complete_anchors)} with all {len(expected_directions)} directions."
        )

    selected_anchors = set(complete_anchors[:anchor_limit])
    selected: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if row.get("anchor_id") not in selected_anchors:
            continue
        selected.setdefault(row["language_pair"], []).append(row)
    return {direction: rows for direction, rows in selected.items() if rows}


def expected_language_directions(languages: tuple[str, ...]) -> set[str]:
    return {
        f"{source_language}-{target_language}"
        for source_language in languages
        for target_language in languages
        if source_language != target_language
    }


def normalize_source_pair_row(row: dict[str, Any], *, kind: str) -> dict[str, Any]:
    source_language = str(row.get("source_language") or "").strip().lower()
    target_language = str(row.get("target_language") or "").strip().lower()
    if not source_language or not target_language:
        direction = str(row.get("language_pair") or "")
        source_language, _, target_language = direction.partition("-")
    if source_language not in LANGUAGE_NAMES:
        raise ValueError(f"Unsupported source language for {kind}: {source_language}")
    if target_language not in LANGUAGE_NAMES:
        raise ValueError(f"Unsupported target language for {kind}: {target_language}")
    direction = f"{source_language}-{target_language}"
    return {
        **row,
        "language_pair": direction,
        "source_language": source_language,
        "target_language": target_language,
        "source_text": normalize_text(str(row.get("source_text") or "")),
        "target_text": normalize_text(str(row.get("target_text") or "")),
    }


def row_passes_token_bounds(row: dict[str, Any], build: BenchmarkBuildConfig) -> bool:
    if not row["source_text"] or not row["target_text"]:
        return False
    if build.min_input_tokens is None and build.max_input_tokens is None:
        return True
    token_count = approximate_token_count(row["source_text"])
    if build.min_input_tokens is not None and token_count < build.min_input_tokens:
        return False
    if build.max_input_tokens is not None and token_count > build.max_input_tokens:
        return False
    return True


def add_bidirectional_pair_rows(
    pair_rows: dict[str, list[dict[str, Any]]],
) -> dict[str, list[dict[str, Any]]]:
    bidirectional_rows = {direction: list(rows) for direction, rows in pair_rows.items()}
    for rows in pair_rows.values():
        for row in rows:
            reversed_row = reverse_source_pair_row(row)
            bidirectional_rows.setdefault(reversed_row["language_pair"], []).append(reversed_row)
    return {direction: rows for direction, rows in sorted(bidirectional_rows.items())}


def reverse_source_pair_row(row: dict[str, Any]) -> dict[str, Any]:
    source_language = str(row["source_language"])
    target_language = str(row["target_language"])
    reversed_pair = f"{target_language}-{source_language}"
    return {
        **row,
        "example_id": f"{row.get('example_id')}:reverse",
        "language_pair": reversed_pair,
        "source_language": target_language,
        "target_language": source_language,
        "source_text": row["target_text"],
        "target_text": row["source_text"],
        "selection_rule": (
            f"{row.get('selection_rule', '')}; synthetic reverse direction".strip("; ")
        ),
    }


def build_manifest_row(*, row: dict[str, Any], kind: str) -> dict[str, Any]:
    if kind == "jrc_acquis_snapshot":
        return build_jrc_manifest_row(row)
    return build_google_manifest_row(row)


def build_google_manifest_row(row: dict[str, Any]) -> dict[str, Any]:
    example_id = str(row.get("example_id") or row.get("doc_id") or "")
    source_row, target_row = source_target_rows(row, example_id)
    return {
        "dataset": "google_patents",
        "source_id": example_id,
        "direction": str(row["language_pair"]),
        "source_language": LANGUAGE_NAMES[str(row["source_language"])],
        "source_language_code": str(row["source_language"]),
        "target_language": LANGUAGE_NAMES[str(row["target_language"])],
        "target_language_code": str(row["target_language"]),
        "source_row_id": source_row["id"],
        "target_row_id": target_row["id"],
        "example_id": example_id,
        "doc_id": str(row.get("doc_id") or ""),
        "corpus_id": str(row.get("corpus_id") or ""),
        "publication_number": str(row.get("doc_id") or ""),
        "family_id": str(row.get("group_key") or ""),
        "country_code": str(row.get("source") or ""),
        "publication_date": str(row.get("pub_date") or ""),
        "field": str(row.get("field") or ""),
        "approx_source_tokens": approximate_token_count(str(row["source_text"])),
        "text_field": TEXT_FIELD,
        "selection": str(row.get("selection_rule") or "preselected_source_target_pair"),
        "terminology": [],
        "_source_text": str(row["source_text"]),
        "_target_text": str(row["target_text"]),
        "_source_row": source_row,
        "_target_row": target_row,
    }


def build_jrc_manifest_row(row: dict[str, Any]) -> dict[str, Any]:
    example_id = str(row.get("example_id") or row["language_pair"])
    source_row, target_row = source_target_rows(row, example_id)
    return {
        "dataset": "jrc_acquis",
        "source_id": example_id,
        "direction": str(row["language_pair"]),
        "source_language": LANGUAGE_NAMES[str(row["source_language"])],
        "source_language_code": str(row["source_language"]),
        "target_language": LANGUAGE_NAMES[str(row["target_language"])],
        "target_language_code": str(row["target_language"]),
        "source_row_id": source_row["id"],
        "target_row_id": target_row["id"],
        "doc_id": str(row.get("doc_id") or "unknown"),
        "anchor_id": str(row.get("anchor_id") or ""),
        "chunk_id": example_id,
        "segment_count": int(row.get("segment_count") or 0),
        "section_type": str(row.get("section_type") or ""),
        "approx_source_tokens": approximate_token_count(str(row["source_text"])),
        "approx_target_tokens": approximate_token_count(str(row["target_text"])),
        "text_field": TEXT_FIELD,
        "selection": str(row.get("selection") or "jrc_acquis_source_pair_snapshot"),
        "terminology": [],
        "_source_text": str(row["source_text"]),
        "_target_text": str(row["target_text"]),
        "_source_row": source_row,
        "_target_row": target_row,
    }


def source_target_rows(
    row: dict[str, Any],
    example_id: str,
) -> tuple[dict[str, str], dict[str, str]]:
    source_row = {
        "id": f"{example_id}_source",
        "doc_id": str(row.get("doc_id") or ""),
        "language": str(row["source_language"]),
        TEXT_FIELD: str(row["source_text"]),
    }
    target_row = {
        "id": f"{example_id}_target",
        "doc_id": str(row.get("doc_id") or ""),
        "language": str(row["target_language"]),
        TEXT_FIELD: str(row["target_text"]),
    }
    return source_row, target_row


def attach_terminology_to_rows(
    rows: list[dict[str, Any]],
    *,
    build: BenchmarkBuildConfig | None = None,
    domain: str,
    terminology: BenchmarkTerminologyConfig,
    runtime: TerminologyRuntime,
    checkpoint: BenchmarkCheckpoint | None = None,
) -> list[dict[str, Any]]:
    if checkpoint is None or build is None:
        return attach_terminology_to_rows_without_checkpoints(
            rows,
            domain=domain,
            terminology=terminology,
            runtime=runtime,
        )
    if not terminology.candidate_extractors and runtime.curator is None:
        for row in rows:
            row["terminology"] = []
        return rows

    candidates_by_row = load_or_run_candidate_extraction_stage(
        rows,
        build=build,
        domain=domain,
        terminology=terminology,
        runtime=runtime,
        checkpoint=checkpoint,
    )
    evidence_enriched_by_row = load_or_run_external_evidence_enrichment_stage(
        rows,
        candidates_by_row,
        build=build,
        domain=domain,
        terminology=terminology,
        runtime=runtime,
        checkpoint=checkpoint,
    )
    curated_by_row = load_or_run_llm_curation_stage(
        rows,
        evidence_enriched_by_row=evidence_enriched_by_row,
        build=build,
        domain=domain,
        terminology=terminology,
        runtime=runtime,
        checkpoint=checkpoint,
    )
    manifest_rows = apply_terminology_records(
        rows,
        evidence_enriched_by_row=evidence_enriched_by_row,
        curated_by_row=curated_by_row,
    )
    return load_or_write_manifest_stage(
        manifest_rows,
        build=build,
        terminology=terminology,
        checkpoint=checkpoint,
    )


def attach_terminology_to_rows_without_checkpoints(
    rows: list[dict[str, Any]],
    *,
    domain: str,
    terminology: BenchmarkTerminologyConfig,
    runtime: TerminologyRuntime,
) -> list[dict[str, Any]]:
    total = len(rows)
    for index, row in enumerate(rows, start=1):
        direction = str(row.get("direction") or "unknown-direction")
        print(
            f"Generating terminology for {direction} row {index}/{total}.",
            flush=True,
        )
        terms = generate_candidate_terms(row, domain=domain, runtime=runtime)
        row["terminology"] = [term.to_json() for term in terms]
        if runtime.curator is not None and terms:
            refined_terms = runtime.curator.refine(
                text=row["_target_text"],
                target_language=row["target_language"],
                candidates=terms,
                domain=domain,
                max_terms=terminology.refined_max_terms,
            )
            row["terminology"].extend(term.to_json() for term in refined_terms)
    return rows


def load_or_run_candidate_extraction_stage(
    rows: list[dict[str, Any]],
    *,
    build: BenchmarkBuildConfig,
    domain: str,
    terminology: BenchmarkTerminologyConfig,
    runtime: TerminologyRuntime,
    checkpoint: BenchmarkCheckpoint,
) -> dict[str, list[DatasetTerminologyTerm]]:
    stage_hash = stable_hash(
        {
            "stage": "candidate_extraction",
            "build": checkpoint_build_payload(build),
            "terminology": candidate_extraction_stage_payload(terminology),
            "rows": rows_checksum(rows),
        }
    )
    cached = read_stage_jsonl(
        checkpoint=checkpoint,
        stage_name="candidate_extraction",
        relative_path=direction_checkpoint_path(rows, "02_candidate_extraction.jsonl"),
        expected_hash=stage_hash,
        reuse=checkpoint.config.reuse_candidate_extraction,
    )
    if cached is not None:
        return terms_by_row_from_records(cached)

    records = []
    total = len(rows)
    for index, row in enumerate(rows, start=1):
        direction = str(row.get("direction") or "unknown-direction")
        print(f"Extracting terminology candidates for {direction} row {index}/{total}.")
        terms = generate_candidate_extraction_terms(
            row,
            domain=domain,
            terminology=terminology,
            runtime=runtime,
        )
        records.append(terms_record(row=row, terms=terms))
    write_stage_jsonl(
        checkpoint=checkpoint,
        stage_name="candidate_extraction",
        relative_path=direction_checkpoint_path(rows, "02_candidate_extraction.jsonl"),
        rows=records,
        stage_hash=stage_hash,
    )
    return terms_by_row_from_records(records)


def load_or_run_external_evidence_enrichment_stage(
    rows: list[dict[str, Any]],
    candidates_by_row: dict[str, list[DatasetTerminologyTerm]],
    *,
    build: BenchmarkBuildConfig,
    domain: str,
    terminology: BenchmarkTerminologyConfig,
    runtime: TerminologyRuntime,
    checkpoint: BenchmarkCheckpoint,
) -> dict[str, list[DatasetTerminologyTerm]]:
    stage_hash = stable_hash(
        {
            "stage": "external_evidence_enrichment",
            "build": checkpoint_build_payload(build),
            "terminology": external_evidence_enrichment_stage_payload(terminology),
            "candidates": terms_by_row_checksum(candidates_by_row),
        }
    )
    cached = read_stage_jsonl(
        checkpoint=checkpoint,
        stage_name="external_evidence_enrichment",
        relative_path=direction_checkpoint_path(rows, "03_external_evidence.jsonl"),
        expected_hash=stage_hash,
        reuse=checkpoint.config.reuse_external_evidence_enrichment,
    )
    if cached is not None:
        return terms_by_row_from_records(cached)

    records = []
    rows_by_id = {manifest_row_id(row): row for row in rows}
    items = sorted(candidates_by_row.items())
    total = len(items)
    for index, (row_id, terms) in enumerate(items, start=1):
        print(f"Enriching terminology candidates with external evidence for row {index}/{total}.")
        enriched_terms = enrich_candidates_with_external_evidence(
            terms,
            row=rows_by_id[row_id],
            domain=domain,
            terminology=terminology,
            runtime=runtime,
        )
        records.append({"row_id": row_id, "terms": [term.to_json() for term in enriched_terms]})
    write_stage_jsonl(
        checkpoint=checkpoint,
        stage_name="external_evidence_enrichment",
        relative_path=direction_checkpoint_path(rows, "03_external_evidence.jsonl"),
        rows=records,
        stage_hash=stage_hash,
    )
    return terms_by_row_from_records(records)


def load_or_run_llm_curation_stage(
    rows: list[dict[str, Any]],
    *,
    evidence_enriched_by_row: dict[str, list[DatasetTerminologyTerm]],
    build: BenchmarkBuildConfig,
    domain: str,
    terminology: BenchmarkTerminologyConfig,
    runtime: TerminologyRuntime,
    checkpoint: BenchmarkCheckpoint,
) -> dict[str, list[DatasetTerminologyTerm]]:
    if runtime.curator is None:
        return {}
    stage_hash = stable_hash(
        {
            "stage": "llm_curation",
            "build": checkpoint_build_payload(build),
            "terminology": llm_curation_stage_payload(terminology),
            "external_evidence": terms_by_row_checksum(evidence_enriched_by_row),
        }
    )
    cached = read_stage_jsonl(
        checkpoint=checkpoint,
        stage_name="llm_curation",
        relative_path=direction_checkpoint_path(rows, "04_llm_curated_terms.jsonl"),
        expected_hash=stage_hash,
        reuse=checkpoint.config.reuse_llm_curation,
    )
    if cached is not None:
        return terms_by_row_from_records(cached)

    records = []
    total = len(rows)
    for index, row in enumerate(rows, start=1):
        row_id = manifest_row_id(row)
        terms = evidence_enriched_by_row.get(row_id, [])
        refined_terms: list[DatasetTerminologyTerm] = []
        if terms:
            direction = str(row.get("direction") or "unknown-direction")
            print(f"Curating terminology for {direction} row {index}/{total}.")
            refined_terms = runtime.curator.refine(
                text=row["_target_text"],
                target_language=row["target_language"],
                candidates=terms,
                domain=domain,
                max_terms=terminology.refined_max_terms,
            )
        records.append(terms_record(row=row, terms=refined_terms))
    write_stage_jsonl(
        checkpoint=checkpoint,
        stage_name="llm_curation",
        relative_path=direction_checkpoint_path(rows, "04_llm_curated_terms.jsonl"),
        rows=records,
        stage_hash=stage_hash,
    )
    return terms_by_row_from_records(records)


def load_or_write_manifest_stage(
    rows: list[dict[str, Any]],
    *,
    build: BenchmarkBuildConfig,
    terminology: BenchmarkTerminologyConfig,
    checkpoint: BenchmarkCheckpoint,
) -> list[dict[str, Any]]:
    stage_hash = stable_hash(
        {
            "stage": "manifest",
            "build": checkpoint_build_payload(build),
            "terminology": manifest_stage_payload(terminology),
            "rows": manifest_rows_checksum(rows),
        }
    )
    cached = read_stage_jsonl(
        checkpoint=checkpoint,
        stage_name="manifest",
        relative_path=direction_checkpoint_path(rows, "05_manifest_rows.jsonl"),
        expected_hash=stage_hash,
        reuse=checkpoint.config.reuse_manifest,
    )
    if cached is not None:
        return cached
    write_stage_jsonl(
        checkpoint=checkpoint,
        stage_name="manifest",
        relative_path=direction_checkpoint_path(rows, "05_manifest_rows.jsonl"),
        rows=rows,
        stage_hash=stage_hash,
    )
    return rows


def generate_candidate_terms(
    row: dict[str, Any],
    *,
    domain: str,
    runtime: TerminologyRuntime,
) -> list[DatasetTerminologyTerm]:
    if domain in {"chemistry", "google_patents"}:
        if runtime.chemistry_generator is None:
            return []
        return runtime.chemistry_generator.generate(
            source_text=row["_source_text"],
            source_language=row["source_language"],
            target_language=row["target_language"],
            reference_text=row["_target_text"],
        )

    terms: list[DatasetTerminologyTerm] = []
    if runtime.legal_generator is not None:
        terms.extend(
            runtime.legal_generator.generate(
                target_language=row["target_language"],
                reference_text=row["_target_text"],
                eurovoc_descriptors={},
            )
        )
    if runtime.algorithmic_generator is not None:
        terms.extend(
            runtime.algorithmic_generator.generate(
                source_text=row["_source_text"],
                source_language=row["source_language"],
                target_language=row["target_language"],
                reference_text=row["_target_text"],
            )
        )
    return deduplicate_terms(terms)


def generate_candidate_extraction_terms(
    row: dict[str, Any],
    *,
    domain: str,
    terminology: BenchmarkTerminologyConfig,
    runtime: TerminologyRuntime,
) -> list[DatasetTerminologyTerm]:
    if domain in {"chemistry", "google_patents"}:
        generator = runtime.chemistry_generator
        if generator is None:
            return []
        if not hasattr(generator, "extractors"):
            return generate_candidate_terms(row, domain=domain, runtime=runtime)
        terms = extract_terms_from_dataset_generator(
            generator=generator,
            row=row,
            max_terms=terminology.candidate_max_terms,
        )
        return deduplicate_terms(terms)[: terminology.candidate_max_terms]

    terms: list[DatasetTerminologyTerm] = []
    legal_generator = runtime.legal_generator
    if legal_generator is not None and hasattr(legal_generator, "llm_extractor"):
        terms.extend(
            legal_generator.llm_extractor.extract(
                text=row["_target_text"],
                target_language=row["target_language"],
                max_terms=terminology.candidate_max_terms,
            )
        )
    elif legal_generator is not None:
        terms.extend(generate_candidate_terms(row, domain=domain, runtime=runtime))

    algorithmic_generator = runtime.algorithmic_generator
    if algorithmic_generator is not None and hasattr(algorithmic_generator, "extractors"):
        terms.extend(
            extract_terms_from_dataset_generator(
                generator=algorithmic_generator,
                row=row,
                max_terms=terminology.candidate_max_terms,
            )
        )
    return deduplicate_terms(terms)[: terminology.candidate_max_terms]


def extract_terms_from_dataset_generator(
    *,
    generator: Any,
    row: dict[str, Any],
    max_terms: int,
) -> list[DatasetTerminologyTerm]:
    terms: list[DatasetTerminologyTerm] = []
    llm_extractor = getattr(generator, "llm_extractor", None)
    if llm_extractor is not None:
        terms.extend(
            llm_extractor.extract(
                text=row["_target_text"],
                target_language=row["target_language"],
                max_terms=max_terms,
            )
        )
    for extractor in getattr(generator, "extractors", []):
        terms.extend(
            extractor.extract(
                row["_target_text"],
                max_terms=max_terms,
                target_language=row["target_language"],
            )
        )
    return terms


def enrich_candidates_with_external_evidence(
    terms: list[DatasetTerminologyTerm],
    *,
    row: dict[str, Any],
    domain: str,
    terminology: BenchmarkTerminologyConfig,
    runtime: TerminologyRuntime,
) -> list[DatasetTerminologyTerm]:
    if not terms:
        return []
    if domain in {"jrc", "legal"}:
        verified = verify_legal_candidate_terms(terms, row=row, runtime=runtime)
        return select_legal_terms(verified, max_terms=terminology.candidate_max_terms)
    verified = verify_dataset_candidate_terms(terms, row=row, runtime=runtime)
    return select_dataset_terms(
        deduplicate_terms(verified),
        max_terms=terminology.candidate_max_terms,
    )


def verify_dataset_candidate_terms(
    terms: list[DatasetTerminologyTerm],
    *,
    row: dict[str, Any],
    runtime: TerminologyRuntime,
) -> list[DatasetTerminologyTerm]:
    generator = runtime.chemistry_generator or runtime.algorithmic_generator
    if generator is None or not hasattr(generator, "add_external_candidates"):
        return deduplicate_terms(terms)
    return [
        generator.add_external_candidates(term=term, target_language=row["target_language"])
        for term in deduplicate_terms(terms)
    ]


def verify_legal_candidate_terms(
    terms: list[DatasetTerminologyTerm],
    *,
    row: dict[str, Any],
    runtime: TerminologyRuntime,
) -> list[DatasetTerminologyTerm]:
    if runtime.legal_generator is not None and hasattr(
        runtime.legal_generator,
        "add_legal_evidence",
    ):
        return [
            runtime.legal_generator.add_legal_evidence(
                term=term,
                target_language=row["target_language"],
                eurovoc_descriptors={},
            )
            for term in deduplicate_terms(terms)
        ]
    if runtime.algorithmic_generator is not None and hasattr(
        runtime.algorithmic_generator,
        "add_external_candidates",
    ):
        return [
            runtime.algorithmic_generator.add_external_candidates(
                term=term,
                target_language=row["target_language"],
            )
            for term in deduplicate_terms(terms)
        ]
    return deduplicate_terms(terms)


def apply_terminology_records(
    rows: list[dict[str, Any]],
    *,
    evidence_enriched_by_row: dict[str, list[DatasetTerminologyTerm]],
    curated_by_row: dict[str, list[DatasetTerminologyTerm]],
) -> list[dict[str, Any]]:
    for row in rows:
        row_id = manifest_row_id(row)
        terms = [
            *evidence_enriched_by_row.get(row_id, []),
            *curated_by_row.get(row_id, []),
        ]
        row["terminology"] = [term.to_json() for term in terms]
    return rows


def read_stage_jsonl(
    *,
    checkpoint: BenchmarkCheckpoint,
    stage_name: str,
    relative_path: Path,
    expected_hash: str,
    reuse: bool,
) -> list[dict[str, Any]] | None:
    if not (checkpoint.enabled and checkpoint.resume and reuse):
        return None
    output_path = checkpoint.root / relative_path
    status = read_stage_status(checkpoint.root)
    stage = status.get(str(relative_path))
    if not output_path.exists() or not isinstance(stage, dict):
        return None
    if stage.get("stage") != stage_name or stage.get("hash") != expected_hash:
        return None
    print(f"Reusing benchmark checkpoint: {relative_path}", flush=True)
    return read_jsonl(output_path)


def write_stage_jsonl(
    *,
    checkpoint: BenchmarkCheckpoint,
    stage_name: str,
    relative_path: Path,
    rows: list[dict[str, Any]],
    stage_hash: str,
) -> None:
    if not checkpoint.enabled:
        return
    output_path = checkpoint.root / relative_path
    write_jsonl(output_path, rows)
    status = read_stage_status(checkpoint.root)
    status[str(relative_path)] = {
        "stage": stage_name,
        "hash": stage_hash,
        "row_count": len(rows),
        "output_path": str(output_path),
    }
    write_json(checkpoint.root / "stage_status.json", status)


def read_stage_status(root: Path) -> dict[str, Any]:
    status_path = root / "stage_status.json"
    if not status_path.exists():
        return {}
    try:
        return json.loads(status_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with temp_path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
    temp_path.replace(path)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    temp_path.replace(path)


def terms_record(row: dict[str, Any], terms: list[DatasetTerminologyTerm]) -> dict[str, Any]:
    return {
        "row_id": manifest_row_id(row),
        "direction": str(row.get("direction") or ""),
        "terms": [term.to_json() for term in terms],
    }


def terms_by_row_from_records(
    records: list[dict[str, Any]],
) -> dict[str, list[DatasetTerminologyTerm]]:
    return {
        str(record["row_id"]): [
            dataset_term_from_json(term)
            for term in record.get("terms", [])
            if isinstance(term, dict)
        ]
        for record in records
    }


def direction_checkpoint_path(rows: list[dict[str, Any]], filename: str) -> Path:
    direction = "unknown-direction"
    if rows:
        direction = str(rows[0].get("direction") or rows[0].get("language_pair") or direction)
    return Path("directions") / slugify_path_part(direction) / filename


def manifest_row_id(row: dict[str, Any]) -> str:
    return stable_hash(
        {
            "direction": row.get("direction"),
            "source_row_id": row.get("source_row_id"),
            "target_row_id": row.get("target_row_id"),
            "source_id": row.get("source_id"),
        }
    )


def rows_checksum(rows: list[dict[str, Any]]) -> str:
    return stable_hash(
        [
            {
                "row_id": manifest_row_id(row),
                "direction": row.get("direction"),
                "source_text": row.get("_source_text"),
                "target_text": row.get("_target_text"),
            }
            for row in rows
        ]
    )


def terms_by_row_checksum(terms_by_row: dict[str, list[DatasetTerminologyTerm]]) -> str:
    return stable_hash(
        {
            row_id: [term.to_json() for term in terms]
            for row_id, terms in sorted(terms_by_row.items())
        }
    )


def manifest_rows_checksum(rows: list[dict[str, Any]]) -> str:
    return stable_hash(rows)


def checkpoint_build_payload(build: BenchmarkBuildConfig) -> dict[str, Any]:
    return {
        "name": build.name,
        "kind": build.kind,
        "source_pairs_jsonl": str(build.source_pairs_jsonl),
        "output_dir": str(build.output_dir),
        "languages": build.languages,
        "limit": build.limit,
        "selection_mode": build.selection_mode,
        "min_input_tokens": build.min_input_tokens,
        "max_input_tokens": build.max_input_tokens,
        "anchor_limit": build.anchor_limit,
        "bidirectional": build.bidirectional,
    }


def candidate_extraction_stage_payload(terminology: BenchmarkTerminologyConfig) -> dict[str, Any]:
    return {
        "domain": terminology.domain,
        "candidate_max_terms": terminology.candidate_max_terms,
        "model": terminology.model,
        "base_url": terminology.base_url,
        "api_mode": terminology.api_mode,
        "max_output_tokens": terminology.max_output_tokens,
        "thinking": terminology.thinking,
        "reasoning_effort": terminology.reasoning_effort,
        "candidate_extractors": terminology.candidate_extractors,
        "nobi_model": terminology.nobi_model,
        "spacy_model": terminology.spacy_model,
    }


def external_evidence_enrichment_stage_payload(
    terminology: BenchmarkTerminologyConfig,
) -> dict[str, Any]:
    local_iate_path = str(terminology.local_iate_path) if terminology.local_iate_path else None
    return {
        "domain": terminology.domain,
        "candidate_max_terms": terminology.candidate_max_terms,
        "external_evidence_sources": terminology.external_evidence_sources,
        "local_iate_path": local_iate_path,
    }


def llm_curation_stage_payload(terminology: BenchmarkTerminologyConfig) -> dict[str, Any]:
    return {
        "domain": terminology.domain,
        "llm_curation": terminology.llm_curation,
        "refined_max_terms": terminology.refined_max_terms,
        "model": terminology.model,
        "base_url": terminology.base_url,
        "api_mode": terminology.api_mode,
        "max_output_tokens": terminology.max_output_tokens,
        "thinking": terminology.thinking,
        "reasoning_effort": terminology.reasoning_effort,
    }


def manifest_stage_payload(terminology: BenchmarkTerminologyConfig) -> dict[str, Any]:
    return {
        "candidate_max_terms": terminology.candidate_max_terms,
        "refined_max_terms": terminology.refined_max_terms,
    }


def stable_hash(payload: Any) -> str:
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:16]


def slugify_path_part(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip()).strip("-")
    return slug or "default"


def write_csv(csv_path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = sorted({field for row in rows for field in row})
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_manifest(manifest_path: Path, rows: list[dict[str, Any]]) -> None:
    temp_path = manifest_path.with_suffix(manifest_path.suffix + ".tmp")
    with temp_path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            output_row = {
                key: value
                for key, value in row.items()
                if not key.startswith("_") and value not in (None, "")
            }
            handle.write(json.dumps(output_row, ensure_ascii=False) + "\n")
    temp_path.replace(manifest_path)


def manifest_filename(kind: str, direction: str, row_count: int) -> str:
    prefix = "jrc-acquis" if kind == "jrc_acquis_snapshot" else "google-patents"
    return f"{prefix}-{direction}-{row_count}-manifest.jsonl"


def combined_manifest_filename(kind: str, direction_count: int, row_count: int) -> str:
    prefix = "jrc-acquis" if kind == "jrc_acquis_snapshot" else "google-patents"
    row_name = "chunks" if kind == "jrc_acquis_snapshot" else "pairs"
    return f"{prefix}-{direction_count}-directions-{row_count}-{row_name}-manifest.jsonl"


def refined_terms_from_manifest(row: dict[str, Any]) -> list[DatasetTerminologyTerm]:
    return [
        dataset_term_from_json(term)
        for term in row.get("terminology", [])
        if isinstance(term, dict) and term.get("term_group") == "refined"
    ]

