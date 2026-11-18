from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from dataclasses import asdict
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

from evaluate_parallel_manifest import ParallelRowsLoader, discover_manifest

DEFAULT_DATASETS = {
    "google_patents": Path(
        "benchmark_datasets/google_patents_judged_exact_high_glm_flash_local"
    ),
    "jrc_articles": Path(
        "benchmark_datasets/jrc_acquis_anchored_articles_250_anchors_glm_flash"
    ),
    "jrc_definitions": Path(
        "benchmark_datasets/jrc_acquis_anchored_definitions_250_anchors_glm_flash"
    ),
}
METRICS = ("comet", "reference_assignment_comet", "sentalign_comet")


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def select_documents(dataset_dirs, tokenizer, segmenter, directions, min_tokens=600,
                     max_tokens=2000, allow_overlong_sentences=False):
    documents = []
    screening = []
    for dataset, directory in dataset_dirs.items():
        manifest_path = discover_manifest(directory)
        loader = ParallelRowsLoader(directory)
        by_direction = {direction: [] for direction in directions}
        with manifest_path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                row = json.loads(line)
                if row["direction"] not in by_direction:
                    continue
                source_row, reference_row = loader.rows_for_manifest(row)
                source, reference = source_row["context"], reference_row["context"]
                source_language = row["source_language_code"]
                target_language = row["target_language_code"]
                counts = {name: len(tokenizer.encode(text, add_special_tokens=True,
                                                     truncation=False))
                          for name, text in (("source", source), ("reference", reference))}
                if min(counts.values()) < min_tokens or max(counts.values()) > max_tokens:
                    continue
                source_sentences = segmenter.segment(source, source_language)
                reference_sentences = segmenter.segment(reference, target_language)
                if min(len(source_sentences), len(reference_sentences)) < 4:
                    continue
                maximum_sentence_tokens = max(
                    len(tokenizer.encode(sentence, add_special_tokens=True, truncation=False))
                    for sentence in source_sentences + reference_sentences
                )
                if maximum_sentence_tokens > 510 and not allow_overlong_sentences:
                    continue
                identity = str(row.get("source_id") or row["source_row_id"])
                by_direction[row["direction"]].append({
                    "id": f"{dataset}:{row['direction']}:{identity}",
                    "dataset": dataset, "direction": row["direction"],
                    "source": source, "reference": reference,
                    "source_language": source_language, "target_language": target_language,
                    "reference_sentences": reference_sentences,
                    "full_token_counts": counts,
                    "maximum_sentence_tokens": maximum_sentence_tokens,
                    "selection_allow_overlong_sentences": allow_overlong_sentences,
                    "source_sha256": text_hash(source), "reference_sha256": text_hash(reference),
                    "provenance": {
                        "dataset_dir": directory.as_posix(),
                        "manifest": manifest_path.as_posix(), "manifest_line": line_number,
                        **{key: row.get(key) for key in (
                            "dataset", "source_id", "source_row_id", "target_row_id",
                            "doc_id", "anchor_id", "publication_number", "section_type",
                        )},
                    },
                })
        used_documents = set()
        for direction, candidates in by_direction.items():
            screening.append({"dataset": dataset, "direction": direction,
                              "eligible_count": len(candidates)})
            candidates.sort(key=lambda item: (-min(item["full_token_counts"].values()), item["id"]))
            chosen = next((item for item in candidates
                           if item["provenance"]["doc_id"] not in used_documents), None)
            if chosen is None:
                raise ValueError(f"No eligible distinct long document for {dataset}/{direction}.")
            donors = [item for item in candidates
                      if item["provenance"]["doc_id"] != chosen["provenance"]["doc_id"]
                      and item["reference_sha256"] != chosen["reference_sha256"]]
            if not donors:
                raise ValueError(f"No distinct same-language donor for {dataset}/{direction}.")
            chosen = dict(chosen)
            chosen["donor"] = min(donors, key=lambda item: (
                abs(item["full_token_counts"]["reference"]
                    - chosen["full_token_counts"]["reference"]), item["id"],
            ))
            used_documents.add(chosen["provenance"]["doc_id"])
            documents.append(chosen)
    return documents, screening


def build_variants(document, donor):
    if document["target_language"] != donor["target_language"]:
        raise ValueError("Donor must be in the same target language.")
    if document["dataset"] != donor["dataset"] or document["id"] == donor["id"]:
        raise ValueError("Donor must be a distinct record in the same dataset.")
    sentences = document["reference_sentences"]
    if len(sentences) < 4:
        raise ValueError("At least four reference sentences are required.")
    donor_sentences = donor["reference_sentences"]
    variants = [{
        "condition": "reference_control", "prediction": document["reference"],
        "changed_reference_indices": [], "nominal_corruption_fraction": 0.0,
        "construction": "Unmodified dataset reference; positive control, not a model output.",
    }]
    for fraction in (0.25, 0.5, 0.75):
        count = max(1, round(len(sentences) * fraction))
        start = len(sentences) - count
        indices = list(range(start, len(sentences)))
        percentage = int(100 * fraction)
        replacement = [donor_sentences[index % len(donor_sentences)] for index in range(count)]
        for operation, tail in (("omission", []), ("replacement", replacement)):
            variants.append({
                "condition": f"tail_{operation}_{percentage}",
                "prediction": "\n".join(sentences[:start] + tail),
                "changed_reference_indices": indices,
                "nominal_corruption_fraction": fraction,
                "actual_sentence_corruption_fraction": count / len(sentences),
                "donor_id": donor["id"] if operation == "replacement" else None,
                "construction": (
                    f"Keep the first {start} reference sentences; {operation} of the last {count}. "
                    "Replacement sentences come from a different real document, not authored text."
                ),
            })
    variants.append({
        "condition": "wrong_document", "prediction": donor["reference"],
        "changed_reference_indices": list(range(len(sentences))),
        "nominal_corruption_fraction": 1.0, "actual_sentence_corruption_fraction": 1.0,
        "donor_id": donor["id"],
        "construction": "Unmodified translation of a different document in the same dataset.",
    })
    for variant in variants:
        variant["prediction_sha256"] = text_hash(variant["prediction"])
    return variants


def summarize(results):
    summary = []
    for dataset in sorted({row["dataset"] for row in results}):
        for condition in sorted({row["condition"] for row in results}):
            rows = [row for row in results if row["dataset"] == dataset
                    and row["condition"] == condition]
            for metric in METRICS:
                values = [row["scores"][metric] for row in rows
                          if row["scores"][metric] is not None]
                summary.append({
                    "dataset": dataset, "condition": condition, "metric": metric,
                    "case_count": len(rows), "scored_count": len(values),
                    "mean": sum(values) / len(values) if values else None,
                })
    return summary


def quality_checks(results):
    checks = []
    for document_id in sorted({row["document_id"] for row in results}):
        rows = {row["condition"]: row for row in results if row["document_id"] == document_id}
        for metric in METRICS:
            control = rows["reference_control"]["scores"][metric]
            for condition, row in rows.items():
                if condition == "reference_control":
                    continue
                score = row["scores"][metric]
                checks.append({
                    "document_id": document_id, "dataset": row["dataset"], "metric": metric,
                    "expectation": "control_above_degraded", "condition": condition,
                    "passed": (
                        control > score if control is not None and score is not None else None
                    ),
                    "drop": control - score if control is not None and score is not None else None,
                })
            for operation in ("omission", "replacement"):
                scores = [control] + [rows[f"tail_{operation}_{percentage}"]["scores"][metric]
                                      for percentage in (25, 50, 75)]
                checks.append({
                    "document_id": document_id, "dataset": rows["reference_control"]["dataset"],
                    "metric": metric, "expectation": "strict_degradation_order",
                    "condition": operation,
                    "passed": all(
                        left > right for left, right in zip(scores, scores[1:], strict=False)
                    )
                    if all(score is not None for score in scores) else None,
                    "scores": scores,
                })
    return checks


def run_inference(report, output):
    import numpy as np
    import torch
    from comet import load_from_checkpoint
    from huggingface_hub import snapshot_download
    from test_aligned_comet_long_prefix import CachedComet, CachedEmbedder, first_difference

    from chem_machine_translation.evaluation.aligned_comet import (
        AlignedCometConfig,
        AlignedCometScorer,
        SentAlignCometConfig,
        SentAlignCometScorer,
    )
    from chem_machine_translation.evaluation.metrics import UnbabelCometScorer

    torch.set_num_threads(4)
    torch.manual_seed(42)
    np.random.seed(42)
    embedding_path = snapshot_download("BAAI/bge-m3", local_files_only=True)
    checkpoint_dir = Path(snapshot_download("Unbabel/wmt22-comet-da", local_files_only=True))
    checkpoints = sorted(checkpoint_dir.rglob("*.ckpt"))
    if not checkpoints:
        raise RuntimeError("No complete COMET checkpoint is cached.")
    print("Loading shared cached COMET checkpoint...", flush=True)
    model = load_from_checkpoint(str(checkpoints[0]))
    model.eval()
    tokenizer = model.encoder.tokenizer
    assignment_config = AlignedCometConfig(embedding_model=embedding_path)
    sentalign_config = SentAlignCometConfig(
        alignment_model=embedding_path,
        alignment_cache=str(Path("benchmark_work/sentalign_real_embedding_cache").resolve()),
    )
    checked_comet = CachedComet(model)
    regular = UnbabelCometScorer(batch_size=8)
    regular._model = model
    scorers = {
        "reference_assignment_comet": AlignedCometScorer(
            config=assignment_config, embedder=CachedEmbedder(assignment_config),
            comet_scorer=checked_comet,
        ),
        "sentalign_comet": SentAlignCometScorer(sentalign_config, comet_scorer=checked_comet),
    }
    report.update({
        "started_at": datetime.now(timezone.utc).isoformat(),
        "comet_checkpoint": str(checkpoints[0]), "embedding_snapshot": embedding_path,
        "reference_assignment_config": asdict(assignment_config),
        "sentalign_config": asdict(sentalign_config),
        "package_versions": {name: version(name) for name in (
            "sentalign", "unbabel-comet", "transformers", "torch", "spacy",
        )},
        "seed": 42, "torch_threads": 4, "results": [], "completed": False,
    })
    for document in report["documents"]:
        source, reference = document["source"], document["reference"]
        assert text_hash(source) == document["source_sha256"]
        assert text_hash(reference) == document["reference_sha256"]
        control_retained = model.encoder.prepare_sample([reference])["input_ids"][0].tolist()
        reference_ids = tokenizer.encode(reference, add_special_tokens=True, truncation=False)
        for variant in build_variants(document, document["donor"]):
            prediction = variant["prediction"]
            prediction_ids = tokenizer.encode(prediction, add_special_tokens=True, truncation=False)
            retained = model.encoder.prepare_sample([prediction])["input_ids"][0].tolist()
            row = {
                **variant, "document_id": document["id"], "dataset": document["dataset"],
                "direction": document["direction"], "scores": {}, "errors": {},
                "metric_details": {}, "seconds": {},
                "prediction_tokens": len(prediction_ids),
                "regular_retained_prediction_tokens": len(retained),
                "regular_reference_prediction_ids_equal": control_retained == retained,
                "first_different_token": first_difference(reference_ids, prediction_ids),
            }
            for metric in METRICS:
                started = time.perf_counter()
                try:
                    if metric == "comet":
                        score = regular.score(source, prediction, reference)
                    else:
                        result = scorers[metric].score_document(
                            source, prediction, reference, document["source_language"],
                            document["target_language"],
                        )
                        score = result.score
                        row["metric_details"][metric] = asdict(result)
                    if not math.isfinite(score):
                        raise ValueError("Metric returned a nonfinite score.")
                    row["scores"][metric] = score
                except (ValueError, RuntimeError) as exc:
                    row["scores"][metric] = None
                    row["errors"][metric] = f"{type(exc).__name__}: {exc}"
                row["seconds"][metric] = time.perf_counter() - started
            report["results"].append(row)
            output.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False),
                              encoding="utf-8")
            print(json.dumps({
                "document": document["id"], "condition": variant["condition"],
                "scores": row["scores"], "errors": row["errors"],
            }), flush=True)
    report["summary"] = summarize(report["results"])
    report["quality_checks"] = quality_checks(report["results"])
    report["completed"] = True
    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False),
                      encoding="utf-8")
    print(f"Saved {len(report['results'])} real-record cases to {output}", flush=True)


def main():
    parser = argparse.ArgumentParser(description="Real-record long-document COMET diagnostics.")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--select-only", action="store_true")
    parser.add_argument("--fixtures", type=Path)
    parser.add_argument("--directions", nargs="+", default=["en-de", "en-fr", "en-es"])
    parser.add_argument("--only-dataset", choices=sorted(DEFAULT_DATASETS))
    parser.add_argument("--allow-overlong-sentences", action="store_true")
    parser.add_argument("--min-tokens", type=int, default=600)
    parser.add_argument("--max-tokens", type=int, default=2000)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"Preserving existing output: {args.output}")
    from transformers import AutoTokenizer

    from chem_machine_translation.evaluation.aligned_comet import SpacySentenceSegmenter

    tokenizer = AutoTokenizer.from_pretrained("xlm-roberta-large", local_files_only=True)
    segmenter = SpacySentenceSegmenter({})
    if args.fixtures:
        report = json.loads(args.fixtures.read_text(encoding="utf-8"))
    else:
        documents, screening = select_documents(
            {name: path for name, path in DEFAULT_DATASETS.items()
             if args.only_dataset is None or name == args.only_dataset},
            tokenizer, segmenter, args.directions,
            args.min_tokens, args.max_tokens, args.allow_overlong_sentences,
        )
        report = {
            "protocol": "Real benchmark records with deterministic reference-derived degradations.",
            "quality_labels": "Construction labels only; not human ratings or new MT outputs.",
            "selection": {
                "min_tokens_per_side": args.min_tokens, "max_tokens_per_side": args.max_tokens,
                "minimum_sentences_per_side": 4,
                "max_individual_sentence_tokens": None if args.allow_overlong_sentences else 510,
                "allow_overlong_sentences": args.allow_overlong_sentences,
                "directions": args.directions, "screening": screening,
                "rule": (
                    "Longest minimum side length first; distinct documents; "
                    "no score-based selection."
                ),
            },
            "documents": documents,
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.select_only:
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        for document in report["documents"]:
            print(document["id"], document["full_token_counts"], flush=True)
        return
    run_inference(report, args.output)


if __name__ == "__main__":
    main()