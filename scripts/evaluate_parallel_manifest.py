from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

from chem_machine_translation.config import DEFAULT_MODEL, load_settings
from chem_machine_translation.core.schemas import Document
from chem_machine_translation.evaluation.metrics import (
    COMET_DEFAULT_MODEL,
    GENERAL_METRIC_NAMES,
    MQM_DEFAULT_MODEL,
    TERMINOLOGY_TERM_GROUPS,
    OpenAIMqmJudge,
    UnbabelCometScorer,
    compute_corpus_overlap_metrics,
    compute_translation_metrics,
    parse_metric_names,
)
from chem_machine_translation.translation.translators import build_translator
from chem_machine_translation.utils.text import approximate_token_count, normalize_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate a source.csv/target.csv/manifest.jsonl benchmark direction or a "
            "multidirectional root dataset."
        ),
    )
    parser.add_argument("--dataset-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=None)
    parser.add_argument("--output", type=Path, required=True)
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
        help="Metric to compute. Repeat to select multiple metrics.",
    )
    parser.add_argument("--comet-model", default=COMET_DEFAULT_MODEL)
    parser.add_argument("--comet-batch-size", type=int, default=8)
    parser.add_argument("--comet-gpus", type=int, default=0)
    parser.add_argument("--fsp-mqm-model", default=MQM_DEFAULT_MODEL)
    parser.add_argument("--fsp-mqm-timeout", type=float, default=120.0)
    parser.add_argument(
        "--terminology-term-group",
        action="append",
        choices=TERMINOLOGY_TERM_GROUPS,
        default=None,
        help="Terminology groups used by target terminology metrics. Defaults to verified.",
    )
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
    mqm_judge = (
        OpenAIMqmJudge(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            model=args.fsp_mqm_model,
            timeout=args.fsp_mqm_timeout,
        )
        if "fsp_mqm" in metric_names
        else None
    )
    translator = build_translator(
        strategy=args.strategy,
        settings=settings,
        model=args.model,
        max_rounds=args.max_review_rounds,
        terminology_layer=None,
    )

    manifest_rows = load_manifest_rows(args.manifest or discover_manifest(args.dataset_dir))
    row_loader = ParallelRowsLoader(args.dataset_dir)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    with args.output.open("w", encoding="utf-8") as handle:
        for manifest_row in manifest_rows:
            source_row, target_row = row_loader.rows_for_manifest(manifest_row)
            text_field = str(manifest_row.get("text_field") or "context")
            source_text = normalize_text(source_row[text_field])
            target_text = normalize_text(target_row[text_field])
            document = Document(
                dataset="parallel_manifest",
                source_id=str(manifest_row["source_id"]),
                text=source_text,
                ground_truth=target_text,
                metadata=manifest_row,
            )
            result = translator.translate(
                document=document,
                target_language=str(manifest_row["target_language"]),
                source_language=str(manifest_row["source_language"]),
            )
            metrics = compute_translation_metrics(
                prediction=result.translated_text,
                reference=target_text,
                source=source_text,
                metric_names=metric_names,
                comet_scorer=comet_scorer,
                terminology=manifest_row.get("terminology"),
                terminology_term_groups=args.terminology_term_group,
                mqm_judge=mqm_judge,
            )
            output_row = {
                "dataset": document.dataset,
                "source_id": document.source_id,
                "direction": manifest_row.get("direction"),
                "source_language": manifest_row.get("source_language"),
                "target_language": manifest_row.get("target_language"),
                "strategy": result.strategy,
                "model": result.model,
                "approved": result.approved,
                "review_rounds": result.review_rounds,
                "review_notes": result.review_notes,
                "terminology_section": result.terminology_section,
                "approx_source_tokens": approximate_token_count(source_text),
                "source_text": source_text,
                "predicted_translation": result.translated_text,
                "ground_truth_translation": target_text,
                "metrics": metrics,
                "metadata": manifest_row,
            }
            rows.append(output_row)
            handle.write(json.dumps(output_row, ensure_ascii=False) + "\n")

    print_summary(rows, args.output)


def load_rows_by_id(csv_path: Path) -> dict[str, dict[str, str]]:
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        return {str(row["id"]): row for row in csv.DictReader(handle)}


class ParallelRowsLoader:
    def __init__(self, dataset_dir: Path) -> None:
        self.dataset_dir = dataset_dir
        self._cache: dict[Path, tuple[dict[str, dict[str, str]], dict[str, dict[str, str]]]] = {}

    def rows_for_manifest(self, manifest_row: dict) -> tuple[dict[str, str], dict[str, str]]:
        direction = str(manifest_row.get("direction") or "")
        direction_dir = self.dataset_dir / direction if direction else self.dataset_dir
        source_rows, target_rows = self._rows_for_dir(direction_dir)
        return (
            source_rows[str(manifest_row["source_row_id"])],
            target_rows[str(manifest_row["target_row_id"])],
        )

    def _rows_for_dir(
        self,
        direction_dir: Path,
    ) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]]]:
        if direction_dir not in self._cache:
            self._cache[direction_dir] = (
                load_rows_by_id(direction_dir / "source.csv"),
                load_rows_by_id(direction_dir / "target.csv"),
            )
        return self._cache[direction_dir]


def discover_manifest(dataset_dir: Path) -> Path:
    manifests = sorted(dataset_dir.glob("*manifest.jsonl"))
    if len(manifests) != 1:
        raise ValueError(
            f"Expected exactly one manifest in {dataset_dir}, found {len(manifests)}."
        )
    return manifests[0]


def load_manifest_rows(manifest_path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in manifest_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def print_summary(rows: list[dict], output: Path) -> None:
    print(f"Wrote {len(rows)} evaluated translations to {output}")
    by_direction: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_direction[str(row["direction"])].append(row)

    for direction, direction_rows in sorted(by_direction.items()):
        metrics = defaultdict(list)
        for row in direction_rows:
            for metric_name, value in row["metrics"].items():
                metrics[metric_name].append(value)
        corpus_metrics = compute_corpus_overlap_metrics(
            predictions=[row["predicted_translation"] for row in direction_rows],
            references=[row["ground_truth_translation"] for row in direction_rows],
            metric_names=tuple(metrics),
        )
        metric_summary = ", ".join(
            f"{metric_name}={corpus_metrics.get(metric_name, sum(values) / len(values)):.2f}"
            for metric_name, values in sorted(metrics.items())
        )
        print(f"{direction}: n={len(direction_rows)}, {metric_summary}")


if __name__ == "__main__":
    main()
