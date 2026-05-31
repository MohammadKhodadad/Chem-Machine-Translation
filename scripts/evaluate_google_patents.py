from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from chem_machine_translation.config import DEFAULT_MODEL, load_settings
from chem_machine_translation.google_patents import (
    LANGUAGE_NAMES,
    iter_google_patent_translation_documents,
    normalize_language_code,
)
from chem_machine_translation.metrics import compute_translation_metrics
from chem_machine_translation.text import approximate_token_count
from chem_machine_translation.translators import build_translator

DEFAULT_LANGUAGES = ["French", "German", "Portuguese", "Chinese", "Spanish"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate generated translations against Google Patents ground truth.",
    )
    parser.add_argument("--data-dir", type=Path, default=Path("data/preprocessed"))
    parser.add_argument("--output", type=Path, default=Path("reports/google-patents-eval.jsonl"))
    parser.add_argument("--language", action="append", dest="languages", default=None)
    parser.add_argument("--limit", type=int, default=10, help="Aligned documents per language.")
    parser.add_argument(
        "--strategy",
        default="dry-run",
        choices=["dry-run", "openai", "openai-agentic"],
    )
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--max-review-rounds", type=int, default=3)
    parser.add_argument("--min-input-tokens", type=int, default=192)
    parser.add_argument("--max-input-tokens", type=int, default=256)
    parser.add_argument("--text-field", default="context", choices=["context", "abstract", "title"])
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = load_settings()
    translator = build_translator(
        strategy=args.strategy,
        settings=settings,
        model=args.model,
        max_rounds=args.max_review_rounds,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)

    languages = args.languages or DEFAULT_LANGUAGES
    rows = []
    skipped_languages = []

    with args.output.open("w", encoding="utf-8") as handle:
        for language in languages:
            language_code = normalize_language_code(language)
            language_name = LANGUAGE_NAMES[language_code]
            documents = list(
                iter_google_patent_translation_documents(
                    data_dir=args.data_dir,
                    target_language=language_name,
                    limit=args.limit,
                    min_input_tokens=args.min_input_tokens,
                    max_input_tokens=args.max_input_tokens,
                    text_field=args.text_field,
                )
            )
            if not documents:
                skipped_languages.append(language_name)
                continue

            for document in documents:
                result = translator.translate(
                    document=document,
                    target_language=language_name,
                    source_language="English",
                )
                assert document.ground_truth is not None
                metrics = compute_translation_metrics(result.translated_text, document.ground_truth)
                row = {
                    "dataset": document.dataset,
                    "source_id": document.source_id,
                    "source_language": "English",
                    "target_language": language_name,
                    "target_language_code": language_code,
                    "strategy": result.strategy,
                    "model": result.model,
                    "approved": result.approved,
                    "review_rounds": result.review_rounds,
                    "review_notes": result.review_notes,
                    "approx_source_tokens": approximate_token_count(document.text),
                    "source_text": document.text,
                    "predicted_translation": result.translated_text,
                    "ground_truth_translation": document.ground_truth,
                    "metrics": metrics,
                    "metadata": document.metadata,
                }
                rows.append(row)
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    print_summary(rows, skipped_languages, args.output)


def print_summary(rows: list[dict], skipped_languages: list[str], output: Path) -> None:
    print(f"Wrote {len(rows)} evaluated translations to {output}")
    if skipped_languages:
        print(f"Skipped languages without aligned examples: {', '.join(skipped_languages)}")

    by_language: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_language[row["target_language"]].append(row)

    for language, language_rows in sorted(by_language.items()):
        metrics = defaultdict(list)
        for row in language_rows:
            for metric_name, value in row["metrics"].items():
                metrics[metric_name].append(value)

        metric_summary = ", ".join(
            f"{metric_name}={sum(values) / len(values):.2f}"
            for metric_name, values in sorted(metrics.items())
        )
        print(f"{language}: n={len(language_rows)}, {metric_summary}")


if __name__ == "__main__":
    main()
