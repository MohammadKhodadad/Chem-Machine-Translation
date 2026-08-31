from __future__ import annotations

import csv
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from openai import OpenAI

from chem_machine_translation.benchmark.config import (
    BenchmarkBuildConfig,
    BenchmarkGenerationConfig,
    BenchmarkTerminologyConfig,
    load_benchmark_config,
)
from chem_machine_translation.config import Settings, load_settings
from chem_machine_translation.data.terminology import (
    DatasetTerminologyGenerator,
    DatasetTerminologyTerm,
    LegalTerminologyGenerator,
    LLMTerminologyRefiner,
    dataset_term_from_json,
    deduplicate_terms,
)
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


@dataclass(frozen=True)
class BenchmarkGenerationResult:
    name: str
    builds: tuple[BenchmarkBuildResult, ...]


@dataclass(frozen=True)
class TerminologyRuntime:
    chemistry_generator: DatasetTerminologyGenerator | None = None
    legal_generator: LegalTerminologyGenerator | None = None
    algorithmic_generator: DatasetTerminologyGenerator | None = None
    refiner: LLMTerminologyRefiner | None = None


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
            domain=config.domain,
            terminology=config.terminology,
            runtime=runtime,
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
        refiner=build_refiner(terminology, client),
    )


def needs_llm_client(terminology: BenchmarkTerminologyConfig) -> bool:
    return (
        "llm_chemistry" in terminology.extractors
        or "llm_legal" in terminology.extractors
        or terminology.refiner
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
    if not (set(terminology.extractors) & {"llm_chemistry", "stanza_ud", "xlmr_nobi", "spacy"}):
        return None
    return DatasetTerminologyGenerator(
        client=client,
        model=terminology.model,
        max_terms=terminology.candidate_max_terms,
        use_llm="llm_chemistry" in terminology.extractors,
        llm_api_mode=terminology.api_mode or "responses",
        llm_max_output_tokens=terminology.max_output_tokens,
        llm_thinking=terminology.thinking,
        llm_reasoning_effort=terminology.reasoning_effort,
        use_stanza_extractor="stanza_ud" in terminology.extractors,
        use_nobi_extractor="xlmr_nobi" in terminology.extractors,
        nobi_model=terminology.nobi_model,
        use_spacy_extractor="spacy" in terminology.extractors,
        spacy_model=terminology.spacy_model,
        use_iate=uses_verifier(terminology, "iate"),
        use_wikidata=uses_verifier(terminology, "wikidata", "wikipedia"),
        use_pubchem=uses_verifier(terminology, "pubchem"),
        use_chebi=uses_verifier(terminology, "chebi"),
        use_chembl=uses_verifier(terminology, "chembl"),
        use_mesh=uses_verifier(terminology, "mesh"),
        use_nci=uses_verifier(terminology, "nci"),
        use_agrovoc=uses_verifier(terminology, "agrovoc"),
        cache_path=terminology.cache_path,
    )


def build_legal_generator(
    terminology: BenchmarkTerminologyConfig,
    client: Any | None,
) -> LegalTerminologyGenerator | None:
    if terminology.domain not in {"jrc", "legal"} or "llm_legal" not in terminology.extractors:
        return None
    if client is None:
        raise ValueError("A client is required for the legal LLM extractor.")
    return LegalTerminologyGenerator(
        client=client,
        model=terminology.model,
        max_terms=terminology.candidate_max_terms,
        use_iate=uses_verifier(terminology, "iate"),
        use_wikidata=uses_verifier(terminology, "wikidata", "wikipedia"),
        use_unterm=uses_verifier(terminology, "unterm"),
        cache_path=terminology.legal_cache_path or terminology.cache_path,
        llm_api_mode=terminology.api_mode or "responses",
        llm_max_output_tokens=terminology.max_output_tokens,
        llm_thinking=terminology.thinking,
        llm_reasoning_effort=terminology.reasoning_effort,
    )


def build_algorithmic_generator(
    terminology: BenchmarkTerminologyConfig,
) -> DatasetTerminologyGenerator | None:
    if not (set(terminology.extractors) & {"stanza_ud", "xlmr_nobi", "spacy"}):
        return None
    return DatasetTerminologyGenerator(
        max_terms=terminology.candidate_max_terms,
        use_llm=False,
        use_stanza_extractor="stanza_ud" in terminology.extractors,
        use_nobi_extractor="xlmr_nobi" in terminology.extractors,
        nobi_model=terminology.nobi_model,
        use_spacy_extractor="spacy" in terminology.extractors,
        spacy_model=terminology.spacy_model,
        use_iate=uses_verifier(terminology, "iate"),
        use_wikidata=uses_verifier(terminology, "wikidata", "wikipedia"),
        use_pubchem=uses_verifier(terminology, "pubchem"),
        use_chebi=uses_verifier(terminology, "chebi"),
        use_chembl=uses_verifier(terminology, "chembl"),
        use_mesh=uses_verifier(terminology, "mesh"),
        use_nci=uses_verifier(terminology, "nci"),
        use_agrovoc=uses_verifier(terminology, "agrovoc"),
        use_unterm=uses_verifier(terminology, "unterm"),
        cache_path=terminology.stanza_cache_path or terminology.cache_path,
    )


def build_refiner(
    terminology: BenchmarkTerminologyConfig,
    client: Any | None,
) -> LLMTerminologyRefiner | None:
    if not terminology.refiner:
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


def uses_verifier(terminology: BenchmarkTerminologyConfig, *names: str) -> bool:
    return bool(set(names) & set(terminology.verifiers))


def run_benchmark_build(
    build: BenchmarkBuildConfig,
    *,
    domain: str,
    terminology: BenchmarkTerminologyConfig,
    runtime: TerminologyRuntime,
) -> BenchmarkBuildResult:
    pair_rows = select_source_pair_rows(build)
    build.output_dir.mkdir(parents=True, exist_ok=True)
    combined_rows = []
    for direction, rows in sorted(pair_rows.items()):
        print(f"Building {build.name} {direction}: {len(rows)} rows.", flush=True)
        direction_dir = build.output_dir / direction
        direction_dir.mkdir(parents=True, exist_ok=True)
        manifest_rows = [build_manifest_row(row=row, kind=build.kind) for row in rows]
        manifest_rows = attach_terminology_to_rows(
            manifest_rows,
            domain=domain,
            terminology=terminology,
            runtime=runtime,
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
    return BenchmarkBuildResult(
        name=build.name,
        output_dir=build.output_dir,
        direction_count=len(pair_rows),
        row_count=len(combined_rows),
        combined_manifest_path=combined_manifest_path,
    )


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
        if runtime.refiner is not None and terms:
            refined_terms = runtime.refiner.refine(
                text=row["_target_text"],
                target_language=row["target_language"],
                candidates=terms,
                domain=domain,
                max_terms=terminology.refined_max_terms,
            )
            row["terminology"].extend(term.to_json() for term in refined_terms)
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

