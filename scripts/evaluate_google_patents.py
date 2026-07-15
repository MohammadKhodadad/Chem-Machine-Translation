from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from chem_machine_translation.config import DEFAULT_MODEL, load_settings
from chem_machine_translation.data.google_patents import (
    LANGUAGE_NAMES,
    iter_google_patent_translation_documents,
    normalize_language_code,
)
from chem_machine_translation.evaluation.metrics import (
    COMET_DEFAULT_MODEL,
    GENERAL_METRIC_NAMES,
    UnbabelCometScorer,
    compute_translation_metrics,
    parse_metric_names,
)
from chem_machine_translation.translation.terminology import build_terminology_layer
from chem_machine_translation.translation.translators import build_translator
from chem_machine_translation.utils.text import approximate_token_count

DEFAULT_LANGUAGES = ["French", "German", "Spanish", "Portuguese", "Dutch", "Chinese"]


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
    parser.add_argument(
        "--metric",
        action="append",
        choices=GENERAL_METRIC_NAMES,
        default=None,
        help=(
            "Metric to compute. Repeat to select multiple metrics. "
            "Defaults to sequence_similarity, BLEU, chrF, and COMET."
        ),
    )
    parser.add_argument("--comet-model", default=COMET_DEFAULT_MODEL)
    parser.add_argument("--comet-batch-size", type=int, default=8)
    parser.add_argument("--comet-gpus", type=int, default=0)
    parser.add_argument("--terminology-prompt", type=Path, default=None)
    parser.add_argument(
        "--extract-terminology",
        action="store_true",
        help="Use an LLM to extract source terms before translation.",
    )
    parser.add_argument(
        "--terminology-model",
        default=None,
        help="Model used for LLM terminology extraction. Defaults to the translation model.",
    )
    parser.add_argument(
        "--terminology-max-terms",
        type=int,
        default=20,
        help="Maximum LLM-extracted terminology items per document/language.",
    )
    parser.add_argument(
        "--iate-terminology",
        action="store_true",
        help="Use IATE candidate labels for LLM-extracted terminology.",
    )
    parser.add_argument(
        "--wikidata-terminology",
        action="store_true",
        help="Use Wikidata as backup for extracted terms without IATE candidates.",
    )
    parser.add_argument(
        "--refine-terminology",
        action="store_true",
        help="Use an LLM agent to keep, replace, preserve, or drop terminology candidates.",
    )
    parser.add_argument(
        "--terminology-confidence-threshold",
        type=float,
        default=0.85,
        help="Minimum confidence for refined terminology candidates.",
    )
    parser.add_argument(
        "--terminology-max-refined-terms",
        type=int,
        default=8,
        help="Maximum high-confidence refined terms injected per document.",
    )
    parser.add_argument("--min-input-tokens", type=int, default=192)
    parser.add_argument("--max-input-tokens", type=int, default=256)
    parser.add_argument("--text-field", default="context", choices=["context", "abstract", "title"])
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = load_settings()
    metric_names = parse_metric_names(args.metric)
    comet_scorer = (
        UnbabelCometScorer(
            model_name=args.comet_model,
            batch_size=args.comet_batch_size,
            gpus=args.comet_gpus,
        )
        if "comet" in metric_names
        else None
    )
    terminology_layer = build_terminology_layer(
        settings=settings,
        static_prompt_path=args.terminology_prompt,
        extract_terms=(
            args.extract_terminology
            or args.iate_terminology
            or args.wikidata_terminology
            or args.refine_terminology
        )
        and args.strategy != "dry-run",
        extraction_model=args.terminology_model or args.model,
        max_terms=args.terminology_max_terms,
        use_iate=args.iate_terminology,
        use_wikidata=args.wikidata_terminology,
        refine_terms=args.refine_terminology,
        refinement_confidence_threshold=args.terminology_confidence_threshold,
        max_refined_terms=args.terminology_max_refined_terms,
    )
    translator = build_translator(
        strategy=args.strategy,
        settings=settings,
        model=args.model,
        max_rounds=args.max_review_rounds,
        terminology_layer=terminology_layer,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)

    languages = args.languages or DEFAULT_LANGUAGES
    rows = []
    skipped_languages = []

    with args.output.open("w", encoding="utf-8") as handle:
        for language in languages:
            language_code = normalize_language_code(language)
            language_name = LANGUAGE_NAMES[language_code]
            try:
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
            except FileNotFoundError:
                skipped_languages.append(language_name)
                continue

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
                metrics = compute_translation_metrics(
                    prediction=result.translated_text,
                    reference=document.ground_truth,
                    source=document.text,
                    metric_names=metric_names,
                    comet_scorer=comet_scorer,
                )
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
                    "terminology_section": result.terminology_section,
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
