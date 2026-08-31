from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from render_final_four_refiner_highlights import render_case
except ModuleNotFoundError:
    from scripts.render_final_four_refiner_highlights import render_case

from chem_machine_translation.data.terminology import DatasetTerminologyTerm, dataset_term_from_json

ROOT = Path(__file__).resolve().parents[1]
ARTICLE_MANIFEST = (
    ROOT
    / "benchmark_datasets"
    / "jrc_acquis_anchored_articles_1_anchor"
    / "jrc-acquis-20-directions-20-chunks-manifest.jsonl"
)
REPORT_PATH = ROOT / "docs" / "legal-one-anchor-benchmark-report.md"
FIGURE_DIR = ROOT / "docs" / "figures" / "legal-one-anchor-benchmark"
LANGUAGE_ORDER = ("de", "en", "es", "fr", "pt")


def main() -> None:
    rows = load_manifest(ARTICLE_MANIFEST)
    if not rows:
        raise ValueError(f"No rows found in {ARTICLE_MANIFEST}")

    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    selected_rows = select_article_rows_by_target_language(rows)
    figure_paths = render_language_figures(selected_rows)
    REPORT_PATH.write_text(
        render_report(rows=rows, selected_rows=selected_rows, figure_paths=figure_paths),
        encoding="utf-8",
    )
    print(f"Wrote {REPORT_PATH}")
    for figure_path in figure_paths.values():
        print(f"Wrote {figure_path}")


def load_manifest(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def select_article_rows_by_target_language(
    rows: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    selected: dict[str, dict[str, Any]] = {}
    for language_code in LANGUAGE_ORDER:
        candidates = [
            row
            for row in rows
            if row.get("target_language_code") == language_code
        ]
        if not candidates:
            continue
        preferred_source = "en" if language_code != "en" else "de"
        selected[language_code] = next(
            (
                row
                for row in candidates
                if row.get("source_language_code") == preferred_source
            ),
            candidates[0],
        )
    return selected


def render_language_figures(
    rows_by_language: dict[str, dict[str, Any]],
) -> dict[str, Path]:
    figure_paths: dict[str, Path] = {}
    for language_code, row in rows_by_language.items():
        terms = parse_terms(row)
        refined_terms = [term for term in terms if term.term_group == "refined"]
        extracted_terms = [term for term in terms if term.term_group != "refined"]
        verified_refined_terms = [term for term in refined_terms if term.verified_by]
        output_path = FIGURE_DIR / f"article-anchor-{language_code}-terms.png"
        render_case(
            title=f"{row['target_language']} article text: {row['direction']}",
            text=target_text_from_row(row),
            extracted_terms=extracted_terms,
            refined_terms=refined_terms,
            verified_refined_terms=verified_refined_terms,
            output_path=output_path,
        )
        figure_paths[language_code] = output_path
    return figure_paths


def target_text_from_row(row: dict[str, Any]) -> str:
    target_csv = ARTICLE_MANIFEST.parent / str(row["direction"]) / "target.csv"
    with target_csv.open("r", encoding="utf-8", newline="") as handle:
        for target_row in csv.DictReader(handle):
            if target_row.get("id") == row.get("target_row_id"):
                return str(target_row.get("context") or "")
    raise ValueError(f"Could not find target text for {row['target_row_id']} in {target_csv}")


def parse_terms(row: dict[str, Any]) -> list[DatasetTerminologyTerm]:
    return [
        dataset_term_from_json(term)
        for term in row.get("terminology", [])
        if isinstance(term, dict)
    ]


def render_report(
    *,
    rows: list[dict[str, Any]],
    selected_rows: dict[str, dict[str, Any]],
    figure_paths: dict[str, Path],
) -> str:
    first_row = rows[0]
    direction_count = len({row["direction"] for row in rows})
    anchor_ids = sorted({row.get("anchor_id", "") for row in rows})
    refined_count = sum(
        1
        for row in rows
        for term in row.get("terminology", [])
        if isinstance(term, dict) and term.get("term_group") == "refined"
    )
    terminology_rows = sum(bool(row.get("terminology")) for row in rows)
    lines = [
        "# One-Anchor Legal Benchmark Report",
        "",
        "This report documents the one-anchor JRC-Acquis article benchmark generated from the",
        "config-driven benchmark pipeline.",
        "",
        "## Test Run",
        "",
        "- Config: `config/benchmark_generation/legal_one_anchor.toml`",
        "- Command: `uv run python scripts/generate_benchmark.py --config "
        "config/benchmark_generation/legal_one_anchor.toml`",
        f"- Dataset: `{first_row['dataset']}`",
        f"- Section type: `{first_row.get('section_type', 'article')}`",
        f"- Anchor ID: `{', '.join(anchor_ids)}`",
        f"- Directions: `{direction_count}` ordered language directions",
        f"- Rows with terminology: `{terminology_rows}` of `{len(rows)}`",
        f"- Refined terms across the article benchmark: `{refined_count}`",
        "",
        "## Flow",
        "",
        "1. The TOML config selects the JRC article source snapshot and sets `anchor_limit = 1`.",
        "2. The benchmark pipeline keeps one shared `anchor_id` and expands it across all ordered",
        "   language directions for `de`, `en`, `es`, `fr`, and `pt`.",
        "3. Each selected target/reference article text is passed through the legal terminology",
        "   stack: legal LLM extraction, Stanza/UD, XLM-R/NOBI, spaCy, IATE, Wikidata, and UNTERM.",
        "4. The LLM refiner selects the final `refined` terminology group, capped at eight terms",
        "   per row.",
        "5. The manifest stores both diagnostic candidate terms and final `refined` terms.",
        "",
        "## Figure Legend",
        "",
        "- Gray underline: extracted candidate term from LLM or deterministic extractors.",
        "- Blue underline: LLM-refined final term.",
        "- Green underline: refined term that also has verifier evidence.",
        "",
        "## Article Text By Language",
        "",
    ]
    for language_code in LANGUAGE_ORDER:
        row = selected_rows.get(language_code)
        if row is None:
            continue
        lines.extend(render_language_section(language_code, row, figure_paths[language_code]))
    return "\n".join(lines) + "\n"


def render_language_section(
    language_code: str,
    row: dict[str, Any],
    figure_path: Path,
) -> list[str]:
    terms = parse_terms(row)
    group_counts = Counter(term.term_group for term in terms)
    refined_terms = [term for term in terms if term.term_group == "refined"]
    verified_refined = [term for term in refined_terms if term.verified_by]
    relative_figure_path = figure_path.relative_to(REPORT_PATH.parent).as_posix()
    lines = [
        f"### {row['target_language']} (`{language_code}`)",
        "",
        f"- Direction shown: `{row['direction']}`",
        f"- Candidate/verified terms: `{len(terms) - len(refined_terms)}`",
        f"- Refined terms: `{len(refined_terms)}`",
        f"- Verified refined terms: `{len(verified_refined)}`",
        "- Term groups: "
        + ", ".join(f"`{group}` = `{count}`" for group, count in sorted(group_counts.items())),
        "",
        f"![{row['target_language']} article terminology underlines]({relative_figure_path})",
        "",
        "Selected refined terms:",
        "",
    ]
    if refined_terms:
        lines.extend(
            f"- `{term.target_terms[0]}`"
            + (f" (`{', '.join(term.verified_by)}`)" if term.verified_by else "")
            for term in refined_terms[:8]
            if term.target_terms
        )
    else:
        lines.append("- No refined terms selected.")
    lines.append("")
    return lines


if __name__ == "__main__":
    main()

