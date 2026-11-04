from __future__ import annotations

import argparse
import csv
import os
import shutil
import subprocess
from pathlib import Path

SECTION_ORDER = [
    "00-title.tex",
    "01-abstract.tex",
    "02-introduction.tex",
    "03-literature.tex",
    "04-methods.tex",
    "05-results.tex",
    "06-ablation.tex",
    "07-references.tex",
]
APPENDIX_ORDER = [
    "a-prompts.tex",
    "b-examples-and-figures.tex",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render the LaTeX paper draft.")
    parser.add_argument("--paper-dir", type=Path, default=Path("docs/paper"))
    parser.add_argument("--output-dir", type=Path, default=Path("docs/paper/build"))
    parser.add_argument("--compile-pdf", action="store_true")
    parser.add_argument("--include-appendix", action="store_true")
    parser.add_argument("--tex-engine", default="tectonic")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    render_result_figures(args.paper_dir)
    bibliography_path = args.paper_dir / "latex" / "references.bib"
    output_bibliography_path = args.output_dir / "references.bib"
    if bibliography_path.resolve() != output_bibliography_path.resolve():
        shutil.copyfile(bibliography_path, output_bibliography_path)
    tex_path = args.output_dir / "paper.tex"
    tex_path.write_text(
        assemble_tex(
            args.paper_dir, include_appendix=args.include_appendix, output_dir=args.output_dir
        ),
        encoding="utf-8",
    )
    print(f"Wrote {tex_path}")
    if args.compile_pdf:
        compile_pdf(tex_path=tex_path, tex_engine=args.tex_engine)


def assemble_tex(
    paper_dir: Path, *, include_appendix: bool = False, output_dir: Path | None = None
) -> str:
    body = "\n\n".join(
        read_fragment(path) for path in fragment_paths(paper_dir, include_appendix=include_appendix)
    )
    roots = (
        paper_dir / "figures",
        paper_dir.parent.parent / "reports/evaluation-e452b88/analysis/figures",
    )
    destination = output_dir or paper_dir / "build"
    graphic_paths = "".join(
        "{" + Path(os.path.relpath(root.resolve(), destination.resolve())).as_posix() + "/}"
        for root in roots
    )
    return (
        latex_preamble()
        + "\n\\graphicspath{"
        + graphic_paths
        + "}"
        + "\n\\begin{document}\n\n"
        + body
        + "\n\n\\end{document}\n"
    )


def render_result_figures(paper_dir: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.patches import Patch

    tables = paper_dir.parent.parent / "reports/evaluation-e452b88/analysis/tables"

    def read(name):
        with (tables / name).open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    ranked = sorted(
        (
            row
            for row in read("chosen_01_mixed_ranks.csv")
            if row["view"] == "luna" and row["scope"] == "overall"
        ),
        key=lambda row: int(row["mixed_rank"]),
    )
    runs = [row["run"] for row in ranked]
    figures = paper_dir / "figures"
    figures.mkdir(parents=True, exist_ok=True)

    def save(figure, name):
        for extension in ("pdf", "png"):
            figure.savefig(figures / f"{name}.{extension}", dpi=240, bbox_inches="tight")
        plt.close(figure)

    figure, axis = plt.subplots(figsize=(6.3, 2.8))
    axis.set_axis_off()
    cells = [
        [
            f"{index + 1}. {row['model']}",
            row["mixed_rank"],
            *[
                f"{float(row[f'{family}_mean_rank']):.2f}"
                for family in ("semantic", "lexical", "terminology")
            ],
        ]
        for index, row in enumerate(ranked)
    ]
    table = axis.table(
        cellText=cells,
        colLabels=("Model ID / recorded label", "Rank", "Semantic", "Lexical", "Terms"),
        colWidths=(0.44, 0.09, 0.16, 0.16, 0.15),
        cellLoc="center",
        bbox=(0, 0, 1, 1),
    )
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    for (row, column), cell in table.get_celld().items():
        cell.set_edgecolor("#d9dfdc")
        cell.set_linewidth(0.4)
        if row == 0:
            cell.set_facecolor("#e8eeeb")
            cell.get_text().set_weight("bold")
        if column == 0:
            cell.get_text().set_ha("left")
    figure.subplots_adjust(left=0.01, right=0.99, bottom=0.02, top=0.99)
    save(figure, "results-rank-summary")

    scores = read("translation_quality.csv") + read("terminology.csv")
    datasets = (
        ("google_patents", "Chemical Patents"),
        ("jrc_articles", "JRC Articles"),
        ("jrc_definitions", "JRC Definitions"),
    )
    metrics = (
        ("comet", "shared_general", "not_applicable", "COMET"),
        ("variant_aware_target_term_coverage", "luna", "externally_verified", "Coverage (%)"),
    )
    colors = ("#317b9a", "#d88738")
    figure, axes = plt.subplots(2, 3, figsize=(6.3, 3.5))
    for row_index, (metric, view, category, label) in enumerate(metrics):
        maximum = max(
            float(row["value"])
            for row in scores
            if row["metric"] == metric
            and row["view"] == view
            and row["category"] == category
            and row["value"]
        )
        for column, (dataset, title) in enumerate(datasets):
            axis = axes[row_index, column]
            for setting_index, setting in enumerate(("zero_shot", "few_shot")):
                lookup = {
                    row["run"]: row["value"]
                    for row in scores
                    if (row["metric"], row["view"], row["category"], row["dataset"], row["setting"])
                    == (metric, view, category, dataset, setting)
                }
                values = [float(lookup[run]) if lookup[run] else np.nan for run in runs]
                axis.bar(
                    np.arange(len(runs)) + (setting_index - 0.5) * 0.38,
                    values,
                    width=0.36,
                    color=colors[setting_index],
                    zorder=3,
                )
            axis.set_ylim(0, maximum * 1.08)
            axis.set_xticks(range(len(runs)), range(1, len(runs) + 1), fontsize=6)
            axis.tick_params(axis="y", labelsize=6)
            axis.set_ylabel(label if column == 0 else "", fontsize=7)
            if row_index == 0:
                axis.set_title(title, fontsize=8)
            else:
                axis.set_xlabel("Model ID", fontsize=7)
            axis.grid(axis="y", color="#e4e8e5", linewidth=0.4)
            axis.set_axisbelow(True)
            axis.spines[["top", "right"]].set_visible(False)
    figure.legend(
        handles=[
            Patch(color=color, label=setting)
            for color, setting in zip(colors, ("Zero-shot", "Few-shot"), strict=True)
        ],
        loc="upper center",
        ncol=2,
        frameon=False,
        fontsize=8,
    )
    figure.subplots_adjust(left=0.10, right=0.99, top=0.86, bottom=0.12, hspace=0.4, wspace=0.38)
    save(figure, "results-prompting-summary")


def fragment_paths(paper_dir: Path, *, include_appendix: bool = False) -> list[Path]:
    paths = [paper_dir / "latex" / "sections" / name for name in SECTION_ORDER]
    if include_appendix:
        paths.extend(paper_dir / "latex" / "appendix" / name for name in APPENDIX_ORDER)
    return paths


def read_fragment(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"LaTeX fragment not found: {path}")
    return path.read_text(encoding="utf-8").strip()


def latex_preamble() -> str:
    return r"""\documentclass[11pt]{article}

\usepackage[a4paper,margin=1in]{geometry}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{lmodern}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{hyperref}
\usepackage{xcolor}
\usepackage{listings}

\hypersetup{
  colorlinks=true,
  linkcolor=blue,
  urlcolor=blue,
  citecolor=blue
}

\lstset{
  basicstyle=\ttfamily\small,
  breaklines=true,
  columns=fullflexible,
  frame=single
}

\title{Chemistry-Aware Machine Translation Evaluation with Domain Terminology Verification}
\author{BASF AI}
\date{\today}
"""


def compile_pdf(*, tex_path: Path, tex_engine: str) -> None:
    if shutil.which(tex_engine) is None:
        raise FileNotFoundError(f"TeX engine not found on PATH: {tex_engine}")
    if tex_engine == "tectonic":
        subprocess.run(
            [tex_engine, tex_path.name],
            cwd=tex_path.parent,
            check=True,
        )
    else:
        for pass_index in range(3):
            subprocess.run(
                [tex_engine, "-interaction=nonstopmode", tex_path.name],
                cwd=tex_path.parent,
                check=True,
            )
            if pass_index == 0:
                subprocess.run(
                    ["bibtex", tex_path.stem],
                    cwd=tex_path.parent,
                    check=True,
                )
    print(f"Wrote {tex_path.with_suffix('.pdf')}")


if __name__ == "__main__":
    main()
