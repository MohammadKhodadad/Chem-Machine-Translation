from __future__ import annotations

import argparse
import json
import math
import time
from collections import defaultdict
from dataclasses import asdict
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

from evaluate_parallel_manifest import ParallelRowsLoader

SIDES = ("source", "reference", "prediction")


def select_cases(audit):
    grouped = defaultdict(lambda: defaultdict(list))
    for record in audit["records"]:
        sides = [audit["text_audits"][record[side]] for side in ("source", "reference")]
        if any(side["sentence_count"] == 0 or side["sentence_count"] > 1000
               or side["max_sentence_embedding_tokens"] > 8192 for side in sides):
            continue
        direct = any(side["max_sentence_tokens"] > 510 for side in sides)
        merge = any(side["max_word_eligible_local_span_tokens"] > 510 for side in sides)
        stratum = "overlong_sentence" if direct else "merge_risk" if merge else "safe"
        eligible_long = sum(sentence["words"] <= 110 for side in sides
                            for sentence in side["overlong_sentences"])
        key = (-eligible_long, abs(min(side["full_tokens"] for side in sides) - 1200),
               record["dataset"], record["direction"], record["manifest_line"])
        grouped[sides[1]["language"]][stratum].append((key, record))
    selected = []
    for language, strata in sorted(grouped.items()):
        for values in strata.values():
            values.sort(key=lambda item: item[0])
        used_documents, used_references = set(), set()
        for slot, choices in enumerate((
            ("safe",), ("overlong_sentence",), ("merge_risk", "overlong_sentence"),
        ), 1):
            chosen = None
            for stratum in choices:
                for _, record in strata[stratum]:
                    identity = (record["dataset"], record.get("doc_id") or record["source_row_id"])
                    if (identity not in used_documents
                            and record["reference"] not in used_references):
                        chosen = {**record, "target_language": language, "stratum": stratum,
                                  "case_id": f"{language}-{slot}"}
                        used_documents.add(identity)
                        used_references.add(record["reference"])
                        break
                if chosen is not None:
                    break
            if chosen is None:
                raise ValueError(f"Cannot select three distinct cases for {language}: slot {slot}")
            selected.append(chosen)
    return selected


def text_coverage(result):
    coverage = {}
    for side in SIDES:
        total = sum(len("".join(block[side].split())) for block in result.blocks)
        excluded = sum(len("".join(block[side].split())) for block in result.blocks
                       if block.get("excluded"))
        scored = sum(len("".join(block[side].split())) for block in result.blocks
                     if block["state"] == "matched" and not block.get("excluded"))
        coverage[side] = {"total_nonwhitespace_characters": total,
                          "excluded_nonwhitespace_characters": excluded,
                          "scored_nonwhitespace_characters": scored}
    return coverage


def summarize(results):
    groups = {"all": results}
    for row in results:
        groups.setdefault(row["target_language"], []).append(row)
    summary = []
    for language, rows in sorted(groups.items()):
        audited = [row for row in rows if row.get("filtered_details")]
        coverages = [row["filtered_details"]["coverage"] for row in audited]
        paired = [row for row in rows if row["strict_score"] is not None
                  and row["filtered_score"] is not None]
        values = {
            "language": language, "case_count": len(rows), "audited_case_count": len(audited),
            "affected_rows": sum(item["excluded_blocks"] > 0 for item in coverages),
            "strict_scored_rows": sum(row["strict_score"] is not None for row in rows),
            "filtered_scored_rows": sum(row["filtered_score"] is not None for row in rows),
            "strict_errors": sum(bool(row.get("strict_error")) for row in rows),
            "filtered_errors": sum(bool(row.get("filtered_error")) for row in rows),
            "recovered_rows": sum(row["strict_score"] is None
                                  and row["filtered_score"] is not None for row in rows),
            "zero_to_unscored_rows": sum(row["strict_score"] == 0
                                         and row["filtered_score"] is None for row in rows),
            "unscored_in_both_rows": sum(row["strict_score"] is None
                                         and row["filtered_score"] is None for row in rows),
            "matched_blocks": sum(item["matched_blocks"] for item in coverages),
            "excluded_blocks": sum(item["excluded_blocks"] for item in coverages),
            "paired_scored_rows": len(paired),
            "paired_mean_score_change": sum(row["filtered_score"] - row["strict_score"]
                                           for row in paired) / len(paired) if paired else None,
            "sentences": {}, "text": {},
        }
        matched = values["matched_blocks"]
        values["excluded_matched_block_percentage"] = (
            100 * values["excluded_blocks"] / matched if matched else None
        )
        for side in SIDES:
            counts = {key: sum(item["sentences"][side][key] for item in coverages)
                      for key in ("total_sentences", "excluded_sentences", "scored_sentences")}
            total = counts["total_sentences"]
            counts["excluded_percentage"] = (
                100 * counts["excluded_sentences"] / total if total else None
            )
            counts["scored_percentage"] = (
                100 * counts["scored_sentences"] / total if total else None
            )
            values["sentences"][side] = counts
            chars = {key: sum(row["text_coverage"][side][key] for row in audited)
                     for key in ("total_nonwhitespace_characters",
                                 "excluded_nonwhitespace_characters",
                                 "scored_nonwhitespace_characters")}
            total_chars = chars["total_nonwhitespace_characters"]
            chars["scored_percentage"] = (
                100 * chars["scored_nonwhitespace_characters"] / total_chars
                if total_chars else None
            )
            chars["excluded_percentage"] = (
                100 * chars["excluded_nonwhitespace_characters"] / total_chars
                if total_chars else None
            )
            values["text"][side] = chars
        summary.append(values)
    return summary


def validate_resume(report, audit_digest, cases):
    if report["audit_sha256"] != audit_digest:
        raise ValueError("Cannot resume: coverage audit changed.")
    results = report["results"]
    if len(results) > len(cases) or any(
        any(row.get(key) != value for key, value in case.items())
        for row, case in zip(results, cases, strict=False)
    ):
        raise ValueError("Cannot resume: selected cases changed.")


def main():
    parser = argparse.ArgumentParser(description="SentAlign strict/filter real-record comparison")
    parser.add_argument("--audit", type=Path, default=Path(
        "reports/comet_input_coverage/full_benchmark_20261117.json"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    if args.output.exists() and not args.resume:
        raise FileExistsError(f"Preserving existing output: {args.output}")
    if args.resume and not args.output.exists():
        parser.error("--resume requires an existing report")
    import numpy as np
    import torch
    from comet import load_from_checkpoint
    from huggingface_hub import snapshot_download
    from test_aligned_comet_long_prefix import CachedComet

    from chem_machine_translation.evaluation.aligned_comet import (
        SentAlignCometConfig,
        SentAlignCometScorer,
    )

    audit = json.loads(args.audit.read_text(encoding="utf-8"))
    cases = select_cases(audit)
    digest = sha256(args.audit.read_bytes()).hexdigest()
    previous = json.loads(args.output.read_text(encoding="utf-8")) if args.resume else None
    if previous is not None:
        validate_resume(previous, digest, cases)
        if previous.get("completed") and len(previous["results"]) == len(cases):
            print(f"Already completed: {len(cases)} cases in {args.output}")
            return
    torch.set_num_threads(4)
    torch.manual_seed(42)
    np.random.seed(42)
    checkpoint = next(Path(snapshot_download("Unbabel/wmt22-comet-da",
                                            local_files_only=True)).rglob("*.ckpt"))
    model = load_from_checkpoint(str(checkpoint))
    model.eval()
    comet = CachedComet(model)
    embedding = snapshot_download("BAAI/bge-m3", local_files_only=True)
    settings = {
        "alignment_model": embedding,
        "alignment_cache": str(Path("benchmark_work/sentalign_three_per_language").resolve()),
    }
    filtered = SentAlignCometScorer(SentAlignCometConfig(
        **settings, exclude_overlong_blocks=True), comet_scorer=comet)
    strict = SentAlignCometScorer(SentAlignCometConfig(**settings), comet_scorer=comet)
    report = {
        "completed": False, "started_at": datetime.now(timezone.utc).isoformat(),
        "audit_sha256": digest,
        "strict_config": asdict(strict.config), "filtered_config": asdict(filtered.config),
        "checkpoint": str(checkpoint), "seed": 42, "torch_threads": 4,
        "protocol": "Three distinct real records per target language; SentAlign only.",
        "candidate_origin": "Unmodified reference positive controls, not model translations.",
        "selection": "One safe, one overlong, one merge-risk (or second overlong) per language. "
                     "Prefer overlong segments within upstream 110-word limit, then nearest "
                     "1200-token shorter side; no COMET-score-based selection.",
        "limits": "Size-stratified operational test, not representative exclusion prevalence "
                  "or production translation-quality validation.",
        "results": [],
    }
    if previous is not None:
        if any(previous[key] != report[key] for key in (
            "strict_config", "filtered_config", "checkpoint", "candidate_origin",
        )):
            raise ValueError("Cannot resume: scorer settings or candidate origin changed.")
        report = previous
        report["resumed_at"] = datetime.now(timezone.utc).isoformat()
    loaders = {}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for case in cases[len(report["results"]):]:
        dataset = case["dataset"]
        if dataset not in loaders:
            loaders[dataset] = ParallelRowsLoader(Path(audit["manifests"][dataset]).parent)
        source_row, reference_row = loaders[dataset].rows_for_manifest(case)
        source, reference = source_row["context"], reference_row["context"]
        source_language = audit["text_audits"][case["source"]]["language"]
        for text, key, language in ((source, case["source"], source_language),
                                    (reference, case["reference"], case["target_language"])):
            if key != language + ":" + sha256(text.encode("utf-8")).hexdigest():
                raise ValueError(f"Actual CSV differs from saved audit: {key}")
        row = {**case, "source_text": source, "reference_text": reference,
               "prediction_text": reference, "source_language": source_language,
               "strict_score": None, "filtered_score": None}
        for name, scorer in (("filtered", filtered), ("strict", strict)):
            started = time.perf_counter()
            try:
                result = scorer.score_document(source, reference, reference, source_language,
                                               case["target_language"])
                if result.score is not None and not math.isfinite(result.score):
                    raise ValueError("Nonfinite score")
                row[f"{name}_score"] = result.score
                row[f"{name}_details"] = asdict(result)
                if name == "filtered":
                    row["text_coverage"] = text_coverage(result)
                    strict.aligner = filtered.aligner
            except (ValueError, RuntimeError) as exc:
                row[f"{name}_error"] = f"{type(exc).__name__}: {exc}"
            row[f"{name}_seconds"] = time.perf_counter() - started
        if row.get("filtered_details"):
            def links(scorer):
                return [item["links"] for item in scorer._alignment_audits]

            row["identical_alignment_links"] = links(strict) == links(filtered)
            if not row["identical_alignment_links"]:
                raise ValueError(f"Strict and filtered alignment differs for {case['case_id']}")
        report["results"].append(row)
        report["summary"] = summarize(report["results"])
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False),
                               encoding="utf-8")
        print(json.dumps({key: row.get(key) for key in (
            "case_id", "stratum", "strict_score", "filtered_score",
            "strict_error", "filtered_error",
        )}), flush=True)
    if len(report["results"]) != len(cases):
        raise ValueError("Comparison incomplete: not all selected cases were evaluated.")
    report["completed"] = True
    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False),
                           encoding="utf-8")


if __name__ == "__main__":
    main()