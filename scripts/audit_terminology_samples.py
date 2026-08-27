from __future__ import annotations
# ruff: noqa: I001

import csv
import json
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from openai import OpenAI

from chem_machine_translation.config import load_settings
from chem_machine_translation.data.terminology import (
    DatasetTerminologyTerm,
    DatasetTerminologyGenerator,
    LLMTerminologyRefiner,
    dataset_term_from_json,
    deduplicate_terms,
    find_exact_text_span,
)
try:
    from render_final_four_refiner_highlights import render_case
except ModuleNotFoundError:
    from scripts.render_final_four_refiner_highlights import render_case

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_JSON = ROOT / "docs" / "terminology-sample-audit.json"
OUTPUT_DOC = ROOT / "docs" / "terminology-sample-audit.md"
FIGURE_DIR = ROOT / "docs" / "figures" / "terminology-sample-audit"
REFINED_MAX_TERMS = 8
CHEMICAL_CANDIDATE_MAX_TERMS = 40
GOOGLE_PATENTS_SOURCE_SNAPSHOT = (
    "benchmark_sources/google_patents_within_document_pairs_250_per_language_pair.jsonl"
)
HISTORICAL_ARTIFACT_REV = "a34841c^"
JRC_ARTICLE_ROOTS = (
    "jrc_acquis_anchored_articles_5_all_non_llm_terms",
    "jrc_acquis_anchored_articles_5_llm_terms",
    "jrc_acquis_anchored_articles_5_spacy_only_terms",
)
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
EXTRACTOR_LABELS = (
    ("llm_target", "LLM chemistry extractor"),
    ("legal_llm", "LLM legal extractor"),
    ("stanza_ud_dependency", "Stanza/UD dependency extractor"),
    ("stanza_ud_ngram", "Stanza/UD relaxed n-gram extractor"),
    ("stanza_ud_proper_name", "Stanza/UD proper-name extractor"),
    ("xlmr_nobi", "XLM-R/NOBI token-classification extractor"),
    ("spacy_entity", "spaCy named-entity extractor"),
    ("spacy_noun_chunk", "spaCy noun-chunk extractor"),
    ("spacy_ngram", "spaCy token n-gram extractor"),
)


@dataclass(frozen=True)
class SampleSpec:
    dataset: str
    roots: tuple[str, ...]
    direction: str
    domain: str
    min_source_tokens: int
    max_source_tokens: int
    revision: str | None = None


SAMPLES = [
    SampleSpec(
        "google_patents",
        (GOOGLE_PATENTS_SOURCE_SNAPSHOT,),
        "de-fr",
        "chemistry",
        128,
        384,
    ),
    SampleSpec(
        "google_patents",
        (GOOGLE_PATENTS_SOURCE_SNAPSHOT,),
        "en-de",
        "chemistry",
        128,
        384,
    ),
    SampleSpec(
        "google_patents",
        (GOOGLE_PATENTS_SOURCE_SNAPSHOT,),
        "en-fr",
        "chemistry",
        128,
        384,
    ),
    SampleSpec(
        "google_patents",
        (GOOGLE_PATENTS_SOURCE_SNAPSHOT,),
        "en-zh",
        "chemistry",
        128,
        384,
    ),
    SampleSpec(
        "google_patents",
        (GOOGLE_PATENTS_SOURCE_SNAPSHOT,),
        "fr-ru",
        "chemistry",
        128,
        384,
    ),
    SampleSpec("jrc_acquis", JRC_ARTICLE_ROOTS, "de-es", "jrc", 150, 450, HISTORICAL_ARTIFACT_REV),
    SampleSpec("jrc_acquis", JRC_ARTICLE_ROOTS, "es-en", "jrc", 150, 450, HISTORICAL_ARTIFACT_REV),
    SampleSpec("jrc_acquis", JRC_ARTICLE_ROOTS, "fr-pt", "jrc", 150, 450, HISTORICAL_ARTIFACT_REV),
    SampleSpec("jrc_acquis", JRC_ARTICLE_ROOTS, "pt-fr", "jrc", 150, 450, HISTORICAL_ARTIFACT_REV),
    SampleSpec("jrc_acquis", JRC_ARTICLE_ROOTS, "en-de", "jrc", 150, 450, HISTORICAL_ARTIFACT_REV),
]


def main() -> None:
    settings = load_settings()
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY or OPENCODE_API_KEY is required for sample audit.")

    client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
    chemical_generator = DatasetTerminologyGenerator(
        client=client,
        model=settings.default_model,
        max_terms=CHEMICAL_CANDIDATE_MAX_TERMS,
        use_llm=True,
        use_iate=True,
        use_wikidata=True,
        use_pubchem=True,
        use_chebi=True,
        use_chembl=True,
        use_mesh=True,
        use_nci=True,
        use_agrovoc=True,
        llm_api_mode=settings.llm_api_mode,
        llm_max_output_tokens=settings.llm_max_output_tokens,
        llm_thinking=settings.llm_thinking,
        llm_reasoning_effort=settings.llm_reasoning_effort,
        use_nobi_extractor=True,
        use_spacy_extractor=True,
    )
    refiner = LLMTerminologyRefiner(
        client=client,
        model=settings.default_model,
        api_mode=settings.llm_api_mode,
        max_output_tokens=settings.llm_max_output_tokens,
        thinking=settings.llm_thinking,
        reasoning_effort=settings.llm_reasoning_effort,
    )

    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    results = []
    for index, spec in enumerate(SAMPLES, start=1):
        manifest_row, source_text, target_text, candidates = load_sample(
            spec,
            chemical_generator=chemical_generator,
        )
        print(
            f"sample={index} dataset={spec.dataset} direction={spec.direction} "
            f"candidates={len(candidates)} target={manifest_row['target_language']}",
            flush=True,
        )

        started = time.perf_counter()
        refined_terms = refiner.refine(
            text=target_text,
            target_language=manifest_row["target_language"],
            candidates=candidates,
            domain=spec.domain,
            max_terms=REFINED_MAX_TERMS,
        )
        seconds = round(time.perf_counter() - started, 1)
        verified_refined_terms = [term for term in refined_terms if term.verified_by]
        figure_path = FIGURE_DIR / f"sample-{index:02d}-{spec.dataset}-{spec.direction}.png"
        render_case(
            title=f"Sample {index}: {spec.dataset} {spec.direction}",
            text=target_text,
            extracted_terms=candidates,
            refined_terms=refined_terms,
            verified_refined_terms=verified_refined_terms,
            output_path=figure_path,
        )

        result = {
            "sample": index,
            "dataset": spec.dataset,
            "direction": spec.direction,
            "domain": spec.domain,
            "source_language": manifest_row["source_language"],
            "target_language": manifest_row["target_language"],
            "example_id": manifest_row.get("example_id") or manifest_row.get("source_id"),
            "source_id": manifest_row.get("source_id"),
            "approx_source_tokens": manifest_row.get("approx_source_tokens"),
            "source_snapshot": manifest_row.get("source_snapshot"),
            "model": settings.default_model,
            "api_mode": settings.llm_api_mode,
            "llm_max_output_tokens": settings.llm_max_output_tokens,
            "prompt_version": "strict-refiner-v2",
            "refiner_seconds": seconds,
            "candidate_count": len(candidates),
            "candidate_exact_count": count_exact_terms(target_text, candidates),
            "candidate_verified_count": sum(1 for term in candidates if term.verified_by),
            "refined_count": len(refined_terms),
            "refined_exact_count": count_exact_terms(target_text, refined_terms),
            "refined_verified_count": len(verified_refined_terms),
            "source_text": source_text,
            "target_text": target_text,
            "figure_path": relative_posix(figure_path),
            "candidates": [term.to_json() for term in candidates],
            "refined_terms": [term.to_json() for term in refined_terms],
            "verified_refined_terms": [term.to_json() for term in verified_refined_terms],
        }
        results.append(result)
        print(
            json.dumps(
                {
                    "sample": index,
                    "seconds": seconds,
                    "refined": result["refined_count"],
                    "verified_refined": result["refined_verified_count"],
                    "figure": result["figure_path"],
                },
                ensure_ascii=False,
            ),
            flush=True,
        )

    OUTPUT_JSON.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    OUTPUT_DOC.write_text(render_markdown(results), encoding="utf-8")
    print(f"Wrote {OUTPUT_JSON}")
    print(f"Wrote {OUTPUT_DOC}")


def load_sample(
    spec: SampleSpec,
    *,
    chemical_generator: DatasetTerminologyGenerator,
) -> tuple[dict[str, Any], str, str, list[DatasetTerminologyTerm]]:
    if spec.dataset == "google_patents" and spec.roots[0].endswith(".jsonl"):
        return load_google_source_snapshot_sample(spec, chemical_generator)
    row_index, manifest_row = select_manifest_row(spec, spec.roots[0])
    example_id = manifest_row.get("example_id") or manifest_row.get("source_id")
    source_text = load_csv_context(load_csv_text(spec, spec.roots[0], "source.csv"), row_index)
    target_text = load_csv_context(load_csv_text(spec, spec.roots[0], "target.csv"), row_index)
    terms = []
    for root in spec.roots:
        row = find_manifest_row(spec, root, example_id) or manifest_row
        terms.extend(dataset_term_from_json(term) for term in row.get("terminology", []))
    return manifest_row, source_text, target_text, deduplicate_terms(terms)


def load_google_source_snapshot_sample(
    spec: SampleSpec,
    generator: DatasetTerminologyGenerator,
) -> tuple[dict[str, Any], str, str, list[DatasetTerminologyTerm]]:
    row = select_google_source_snapshot_row(spec)
    source_language_code = str(row["source_language"])
    target_language_code = str(row["target_language"])
    source_language = LANGUAGE_NAMES.get(source_language_code, source_language_code)
    target_language = LANGUAGE_NAMES.get(target_language_code, target_language_code)
    source_text = str(row["source_text"])
    target_text = str(row["target_text"])
    terms = generator.generate(
        source_text=source_text,
        source_language=source_language,
        target_language=target_language,
        reference_text=target_text,
    )
    example_id = str(row.get("example_id") or row.get("doc_id") or spec.direction)
    manifest_row = {
        "dataset": "google_patents",
        "source_id": example_id,
        "example_id": example_id,
        "direction": spec.direction,
        "source_language": source_language,
        "source_language_code": source_language_code,
        "target_language": target_language,
        "target_language_code": target_language_code,
        "doc_id": str(row.get("doc_id") or ""),
        "corpus_id": str(row.get("corpus_id") or ""),
        "publication_number": str(row.get("doc_id") or ""),
        "family_id": str(row.get("group_key") or ""),
        "country_code": str(row.get("source") or ""),
        "publication_date": str(row.get("pub_date") or ""),
        "field": str(row.get("field") or ""),
        "approx_source_tokens": int(
            row.get("source_token_count") or approximate_whitespace_tokens(source_text)
        ),
        "source_snapshot": spec.roots[0],
        "terminology": [term.to_json() for term in terms],
    }
    return manifest_row, source_text, target_text, deduplicate_terms(terms)


def select_google_source_snapshot_row(spec: SampleSpec) -> dict[str, Any]:
    snapshot_path = ROOT / spec.roots[0]
    rows = []
    with snapshot_path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("language_pair") == spec.direction:
                rows.append(row)
    if not rows:
        raise ValueError(f"No Google source rows found for {spec.direction}.")
    eligible = [
        row
        for row in rows
        if spec.min_source_tokens
        <= int(row.get("source_token_count") or 0)
        <= spec.max_source_tokens
    ]
    if not eligible:
        eligible = rows
    return min(
        eligible,
        key=lambda row: (
            abs(int(row.get("source_token_count") or 0) - spec.min_source_tokens),
            str(row.get("example_id") or ""),
        ),
    )


def select_manifest_row(spec: SampleSpec, root: str) -> tuple[int, dict[str, Any]]:
    rows = load_manifest_rows(spec, root)
    eligible = [
        (index, row)
        for index, row in enumerate(rows)
        if row.get("terminology")
        and spec.min_source_tokens
        <= int(row.get("approx_source_tokens") or 0)
        <= spec.max_source_tokens
    ]
    if not eligible:
        eligible = [
            (index, row)
            for index, row in enumerate(rows)
            if row.get("terminology")
        ]
    if not eligible:
        raise ValueError(f"No terminology rows found for {root}/{spec.direction}.")
    return min(
        eligible,
        key=lambda item: (
            abs(int(item[1].get("approx_source_tokens") or 0) - spec.min_source_tokens),
            item[0],
        ),
    )


def find_manifest_row(spec: SampleSpec, root: str, example_id: str | None) -> dict[str, Any] | None:
    if not example_id:
        return None
    for row in load_manifest_rows(spec, root):
        if example_id in {row.get("example_id"), row.get("source_id")}:
            return row
    return None


def load_manifest_rows(spec: SampleSpec, root: str) -> list[dict[str, Any]]:
    if spec.revision:
        manifest_path = next(
            path
            for path in git_list(f"benchmark_datasets/{root}/{spec.direction}")
            if path.endswith("-manifest.jsonl")
        )
        text = git_text(manifest_path, spec.revision)
    else:
        sample_dir = ROOT / "benchmark_datasets" / root / spec.direction
        manifest_path = next(sample_dir.glob("*-manifest.jsonl"))
        text = manifest_path.read_text(encoding="utf-8")
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def load_csv_text(spec: SampleSpec, root: str, filename: str) -> str:
    if spec.revision:
        return git_text(
            f"benchmark_datasets/{root}/{spec.direction}/{filename}",
            spec.revision,
        )
    return (ROOT / "benchmark_datasets" / root / spec.direction / filename).read_text(
        encoding="utf-8"
    )


def git_list(path: str) -> list[str]:
    result = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", HISTORICAL_ARTIFACT_REV, path],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return result.stdout.decode("utf-8").splitlines()


def git_text(path: str, revision: str) -> str:
    result = subprocess.run(
        ["git", "show", f"{revision}:{path}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return result.stdout.decode("utf-8")


def load_csv_context(csv_text: str, row_index: int) -> str:
    with csv_text_as_handle(csv_text) as handle:
        rows = list(csv.DictReader(handle))
    row = rows[row_index]
    return row.get("context") or row.get("text") or row.get("abstract") or ""


def csv_text_as_handle(text: str) -> Any:
    from io import StringIO

    return StringIO(text)


def approximate_whitespace_tokens(text: str) -> int:
    return len(text.split())


def count_exact_terms(text: str, terms: list[DatasetTerminologyTerm]) -> int:
    return sum(1 for term in terms if find_exact_text_span(text, primary_target_term(term)))


def primary_target_term(term: DatasetTerminologyTerm) -> str:
    if term.target_terms:
        return term.target_terms[0]
    if term.reference_candidates:
        return term.reference_candidates[0]
    return term.source_term


def relative_posix(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def render_markdown(results: list[dict[str, Any]]) -> str:
    total_candidates = sum(result["candidate_count"] for result in results)
    total_refined = sum(result["refined_count"] for result in results)
    total_verified_refined = sum(result["refined_verified_count"] for result in results)
    total_seconds = sum(float(result["refiner_seconds"]) for result in results)
    lines = [
        "# Terminology Sample Audit",
        "",
        "This audit shows candidate, refined, and verified-refined terminology spans for 10 "
        "multilingual samples. Underlines use three lanes: gray for all candidates, blue for "
        "refined terms, and green for verified refined terms.",
        "",
        "The Google Patents chemistry samples are selected directly from the newer tracked source "
        f"snapshot `{GOOGLE_PATENTS_SOURCE_SNAPSHOT}` and then passed through the standard "
        "chemistry candidate extractor, verifier, and refiner flow.",
        "",
        "## Summary",
        "",
        f"- Samples: {len(results)}",
        f"- Model: `{results[0]['model']}`",
        f"- API mode: `{results[0]['api_mode']}`",
        f"- Total candidates: {total_candidates}",
        f"- Total refined terms: {total_refined}",
        f"- Total verified refined terms: {total_verified_refined}",
        f"- Total refiner time: {total_seconds:.1f}s",
        "",
    ]
    for result in results:
        lines.extend(render_sample_section(result))
    return "\n".join(lines) + "\n"


def render_sample_section(result: dict[str, Any]) -> list[str]:
    title = (
        f"Sample {result['sample']}: {result['dataset']} "
        f"{result['direction']} ({result['target_language']})"
    )
    figure_path = Path(result["figure_path"]).relative_to("docs").as_posix()
    return [
        f"## {title}",
        "",
        f"- Example: `{result['example_id']}`",
        *render_source_snapshot_line(result),
        f"- Source language: {result['source_language']}",
        f"- Target language: {result['target_language']}",
        f"- Approx source tokens: {result['approx_source_tokens']}",
        f"- Counts: {result['candidate_count']} candidates, "
        f"{result['refined_count']} refined, "
        f"{result['refined_verified_count']} verified refined",
        f"- Refiner time: {result['refiner_seconds']}s",
        "",
        f"![Sample {result['sample']} terminology spans]({figure_path})",
        "",
        "### Source Text",
        "",
        normalize_markdown_text(result["source_text"]),
        "",
        "### Target Text",
        "",
        normalize_markdown_text(result["target_text"]),
        "",
        "### Candidates By Extractor",
        "",
        "The same candidate can appear under multiple extractors when deduplication merged the "
        "same exact target span from several sources.",
        "",
        render_candidates_by_extractor(result["candidates"]),
        "",
        "### Refined Terms",
        "",
        render_term_list(result["refined_terms"]),
        "",
        "### Verified Refined Terms",
        "",
        render_term_list(result["verified_refined_terms"]),
        "",
    ]


def render_source_snapshot_line(result: dict[str, Any]) -> list[str]:
    source_snapshot = result.get("source_snapshot")
    if not source_snapshot:
        return []
    return [f"- Source snapshot: `{source_snapshot}`"]


def render_candidates_by_extractor(raw_terms: list[dict[str, Any]]) -> str:
    if not raw_terms:
        return "- None"

    lines = []
    used_term_ids: set[int] = set()
    for tag, label in EXTRACTOR_LABELS:
        terms = [
            term
            for term in raw_terms
            if tag in source_parts(term)
        ]
        if not terms:
            continue
        used_term_ids.update(id(term) for term in terms)
        lines.extend(
            [
                f"#### {label} (`{tag}`; {pluralize_candidate_count(len(terms))})",
                "",
                render_term_list(terms),
                "",
            ]
        )

    other_terms = [term for term in raw_terms if id(term) not in used_term_ids]
    if other_terms:
        lines.extend(
            [
                "#### Other or verifier-only provenance "
                f"({pluralize_candidate_count(len(other_terms))})",
                "",
                render_term_list(other_terms),
                "",
            ]
        )

    return "\n".join(lines).strip() or "- None"


def pluralize_candidate_count(count: int) -> str:
    noun = "candidate" if count == 1 else "candidates"
    return f"{count} {noun}"


def source_parts(term: dict[str, Any]) -> set[str]:
    return {
        part.strip()
        for part in str(term.get("source") or "").split("+")
        if part.strip()
    }


def render_term_list(raw_terms: list[dict[str, Any]]) -> str:
    if not raw_terms:
        return "- None"
    lines = []
    for term in raw_terms:
        target = first_value(term.get("target_terms")) or first_value(
            term.get("reference_candidates")
        )
        category = term.get("category") or "other"
        verified_by = term.get("verified_by") or []
        verified = f"; verified by {', '.join(verified_by)}" if verified_by else ""
        lines.append(f"- `{escape_backticks(target)}` [{category}{verified}]")
    return "\n".join(lines)


def first_value(values: Any) -> str:
    if isinstance(values, list) and values:
        return str(values[0])
    if isinstance(values, str):
        return values
    return ""


def escape_backticks(text: str) -> str:
    return text.replace("`", "\\`")


def normalize_markdown_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


if __name__ == "__main__":
    main()
