from __future__ import annotations

import argparse
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
    parser.add_argument("--tex-engine", default="tectonic")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    tex_path = args.output_dir / "paper.tex"
    tex_path.write_text(assemble_tex(args.paper_dir), encoding="utf-8")
    print(f"Wrote {tex_path}")
    if args.compile_pdf:
        compile_pdf(tex_path=tex_path, tex_engine=args.tex_engine)


def assemble_tex(paper_dir: Path) -> str:
    body = "\n\n".join(read_fragment(path) for path in fragment_paths(paper_dir))
    return latex_preamble() + "\n\\begin{document}\n\n" + body + "\n\n\\end{document}\n"


def fragment_paths(paper_dir: Path) -> list[Path]:
    paths = [paper_dir / "latex" / "sections" / name for name in SECTION_ORDER]
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
        for _ in range(2):
            subprocess.run(
                [tex_engine, "-interaction=nonstopmode", tex_path.name],
                cwd=tex_path.parent,
                check=True,
            )
    print(f"Wrote {tex_path.with_suffix('.pdf')}")


if __name__ == "__main__":
    main()
