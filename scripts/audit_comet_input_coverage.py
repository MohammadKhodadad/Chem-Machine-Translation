from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
from importlib.metadata import version
from pathlib import Path
from types import SimpleNamespace

from evaluate_parallel_manifest import ParallelRowsLoader, discover_manifest
from evaluate_real_document_metrics import DEFAULT_DATASETS

from chem_machine_translation.evaluation.aligned_comet import (
    AlignedCometConfig,
    SentAlignCometConfig,
    SpacySentenceSegmenter,
)


def token_lengths(tokenizer, texts):
    return [len(tokens) for tokens in tokenizer(
        texts, add_special_tokens=True, truncation=False,
    )["input_ids"]]


def audit_text(text, language, tokenizer, embedding_tokenizer, segmenter):
    config = AlignedCometConfig()
    sentalign = SentAlignCometConfig()
    sentences = segmenter.segment(text, language)
    sentence_tokens = token_lengths(tokenizer, sentences) if sentences else []
    embedding_tokens = token_lengths(embedding_tokenizer, sentences) if sentences else []
    word_counts = [len(sentence.split()) for sentence in sentences]
    spans = [(start, stop, " ".join(sentences[start:stop]))
             for start in range(len(sentences))
             for stop in range(start + 1, min(len(sentences), start +
                                            sentalign.max_concatenations) + 1)]
    span_tokens = token_lengths(tokenizer, [span[2] for span in spans]) if spans else []
    span_embedding_tokens = token_lengths(
        embedding_tokenizer, [span[2] for span in spans],
    ) if spans else []
    long_sentences = [
        {"index": index, "comet_tokens": count, "words": word_counts[index],
         "sha256": sha256(sentences[index].encode("utf-8")).hexdigest(),
         "excerpt": sentences[index][:180]}
        for index, count in enumerate(sentence_tokens) if count > config.max_comet_tokens
    ]
    worst_span = max(range(len(spans)), key=span_tokens.__getitem__) if spans else None
    eligible_tokens = [count for (_, _, span), count in zip(spans, span_tokens, strict=True)
                       if len(span.split()) <= 110]
    return {
        "language": language, "characters": len(text),
        "full_tokens": token_lengths(tokenizer, [text])[0],
        "sentence_count": len(sentences),
        "nonwhitespace_preserved": (
            "".join(text.split()) == "".join("".join(sentences).split())
        ),
        "max_sentence_tokens": max(sentence_tokens, default=0),
        "sentence_tokens_total": sum(sentence_tokens),
        "sentence_overflow_tokens": sum(
            max(0, count - config.max_comet_tokens) for count in sentence_tokens
        ),
        "overlong_sentences": long_sentences,
        "max_sentence_embedding_tokens": max(embedding_tokens, default=0),
        "sentences_over_110_words": sum(count > 110 for count in word_counts),
        "max_local_span_tokens": max(span_tokens, default=0),
        "local_spans_over_comet_limit": sum(
            count > config.max_comet_tokens for count in span_tokens
        ),
        "max_word_eligible_local_span_tokens": max(eligible_tokens, default=0),
        "max_local_span_embedding_tokens": max(span_embedding_tokens, default=0),
        "worst_local_span": None if worst_span is None else {
            "indices": list(range(spans[worst_span][0], spans[worst_span][1])),
            "comet_tokens": span_tokens[worst_span],
        },
    }


def summarize_records(records, texts):
    config = AlignedCometConfig()
    counts = Counter(records=0)
    for record in records:
        sides = [texts[record[side]] for side in ("source", "reference")]
        flags = {
            "ordinary_whole_record_overflow": any(
                side["full_tokens"] > config.max_comet_tokens for side in sides
            ),
            "single_sentence_comet_overflow": any(side["overlong_sentences"] for side in sides),
            "single_sentence_embedding_overflow": any(
                side["max_sentence_embedding_tokens"] > config.embedding_max_tokens
                for side in sides
            ),
            "max_sentences_exceeded": any(
                side["sentence_count"] > config.max_sentences for side in sides
            ),
            "text_preservation_failure": any(not side["nonwhitespace_preserved"] for side in sides),
            "empty_side": any(side["sentence_count"] == 0 for side in sides),
            "sentalign_over_110_words": any(side["sentences_over_110_words"] for side in sides),
            "sentalign_local_span_overflow": any(
                side["max_local_span_tokens"] > config.max_comet_tokens for side in sides
            ),
            "sentalign_word_eligible_local_span_overflow": any(
                side["max_word_eligible_local_span_tokens"] > config.max_comet_tokens
                for side in sides
            ),
            "sentalign_local_embedding_overflow": any(
                side["max_local_span_embedding_tokens"] > config.embedding_max_tokens
                for side in sides
            ),
        }
        flags["single_sentence_length_safe"] = not any(flags[name] for name in (
            "single_sentence_comet_overflow", "single_sentence_embedding_overflow",
            "max_sentences_exceeded", "text_preservation_failure", "empty_side",
        ))
        counts["records"] += 1
        counts.update({name: int(bool(flag)) for name, flag in flags.items()})
    return dict(counts)


def audit_datasets(datasets, tokenizer, embedding_tokenizer, segmenter, limit=None):
    records, texts, manifests = [], {}, {}
    for dataset, directory in datasets.items():
        manifest = discover_manifest(directory)
        manifests[dataset] = manifest.as_posix()
        loader = ParallelRowsLoader(directory)
        count = 0
        with manifest.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if limit is not None and count >= limit:
                    break
                if not line.strip():
                    continue
                row = json.loads(line)
                source, reference = loader.rows_for_manifest(row)
                record = {
                    "dataset": dataset, "direction": row["direction"],
                    "manifest_line": line_number, "doc_id": row.get("doc_id"),
                    "source_id": row.get("source_id"),
                    "source_row_id": row["source_row_id"],
                    "target_row_id": row["target_row_id"],
                }
                for side, item, language in (
                    ("source", source, row["source_language_code"]),
                    ("reference", reference, row["target_language_code"]),
                ):
                    text = item["context"]
                    key = language + ":" + sha256(text.encode("utf-8")).hexdigest()
                    record[side] = key
                    if key not in texts:
                        texts[key] = audit_text(
                            text, language, tokenizer, embedding_tokenizer, segmenter,
                        )
                        texts[key]["example"] = {
                            "dataset": dataset, "manifest_line": line_number, "side": side,
                            "row_id": row["source_row_id" if side == "source" else "target_row_id"],
                        }
                records.append(record)
                count += 1
                if count % 500 == 0:
                    print(f"{dataset}: {count} records; {len(texts)} unique language/text inputs",
                          flush=True)
        print(f"Finished {dataset}: {count} records", flush=True)
    groups = sorted({(row["dataset"], row["direction"]) for row in records})
    return {
        "completed": True, "all_manifest_records_requested": limit is None,
        "limit_per_dataset": limit,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "scope": (
            "Built source/reference inputs; generated translations and neural alignments not run."
        ),
        "settings": {"comet_limit_including_special_tokens": 510,
                     "embedding_limit_including_special_tokens": 8192,
                     "max_sentences": 1000, "max_local_span_sentences": 4,
                     "sentalign_word_limit_per_side": 110,
                     "segmenter": "SpacySentenceSegmenter({}); blank xx + sentencizer"},
        "caveats": [
            "Length-safe means size-safe, not semantically aligned or quality-calibrated.",
            "Possible 1-4 sentence spans are not actual selected SentAlign links.",
            "Reference-span closure can exceed four sentences; this span scan does not bound it.",
            "Unknown model translations must be audited separately.",
            "Segmentation may normalize whitespace; nonwhitespace preservation is checked exactly.",
        ],
        "manifests": manifests,
        "summary": summarize_records(records, texts),
        "by_dataset": {
            dataset: summarize_records([row for row in records if row["dataset"] == dataset], texts)
            for dataset in datasets
        },
        "by_direction": [
            {"dataset": dataset, "direction": direction, **summarize_records(
                [row for row in records
                 if (row["dataset"], row["direction"]) == (dataset, direction)],
                texts,
            )} for dataset, direction in groups
        ],
        "records": records, "text_audits": texts,
    }


def probe_overflows(report, tokenizer):
    from comet.encoders.base import Encoder
    from comet.encoders.xlmr import XLMREncoder
    from transformers import AutoConfig

    from chem_machine_translation.evaluation.aligned_comet import (
        AlignedCometScorer,
        TokenCheckedCometScorer,
    )

    config = AutoConfig.from_pretrained("xlm-roberta-large", local_files_only=True)
    model_metadata = SimpleNamespace(model=SimpleNamespace(config=config))
    positions = XLMREncoder.max_positions.fget(model_metadata)
    encoder = SimpleNamespace(tokenizer=tokenizer, max_positions=positions)
    checked = TokenCheckedCometScorer()
    checked._model = SimpleNamespace(encoder=encoder)
    scorer = AlignedCometScorer(comet_scorer=checked)
    assert checked.token_limit() == report["settings"]["comet_limit_including_special_tokens"]
    probes = []
    segmenter = SpacySentenceSegmenter({})
    for dataset, manifest in report["manifests"].items():
        candidates = [
            (sentence["comet_tokens"], record, side, sentence["index"])
            for record in report["records"] if record["dataset"] == dataset
            for side in ("source", "reference")
            if report["text_audits"][record[side]]["language"] == "en"
            for sentence in report["text_audits"][record[side]]["overlong_sentences"]
        ]
        if not candidates:
            continue
        count, record, side, index = min(candidates, key=lambda item: item[0])
        source, reference = ParallelRowsLoader(Path(manifest).parent).rows_for_manifest(record)
        text = (source if side == "source" else reference)["context"]
        key = "en:" + sha256(text.encode("utf-8")).hexdigest()
        assert key == record[side]
        sentence = segmenter.segment(text, "en")[index]
        assert checked.token_count(sentence) == count
        prepared = Encoder.prepare_sample(encoder, [sentence])
        retained = int(prepared["attention_mask"][0].sum())
        block = {"source": sentence, "reference": sentence, "prediction": sentence,
                 "state": "matched", "score": 0.0}
        try:
            scorer._score_blocks([block], "en", "en", "forced_complete_block_length_probe")
        except ValueError as exc:
            error = str(exc)
            assert error.startswith("Aligned COMET token budget exceeded")
        else:
            raise AssertionError("An oversized real sentence was not rejected by the token guard.")
        assert retained == checked.token_limit() < count
        probes.append({
            "dataset": dataset, "direction": record["direction"],
            "manifest_line": record["manifest_line"], "doc_id": record["doc_id"],
            "source_id": record["source_id"], "side": side, "sentence_index": index,
            "text_sha256": key, "sentence": sentence,
            "full_sentence_tokens": count, "ordinary_comet_retained_tokens": retained,
            "ordinary_comet_truncated_tokens": count - retained,
            "aligned_guard_error": error,
        })
    return {
        "scope": "Real sentence input-preparation/guard probes; no neural inference or alignment.",
        "encoder_config_max_position_embeddings": config.max_position_embeddings,
        "encoder_max_positions": positions, "effective_token_limit": checked.token_limit(),
        "construction": "Same real sentence on all sides forces a complete block for the guard.",
        "probes": probes,
    }


def main():
    parser = argparse.ArgumentParser(description="Audit built COMET input lengths without scoring.")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--only-dataset", action="append", choices=tuple(DEFAULT_DATASETS))
    parser.add_argument("--limit-per-dataset", type=int)
    parser.add_argument("--probe-report", type=Path,
                        help="Replay one real overflow per dataset from an existing full audit.")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output already exists; choose a new report filename.")
    if args.limit_per_dataset is not None and args.limit_per_dataset <= 0:
        parser.error("--limit-per-dataset must be positive.")
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained("xlm-roberta-large", local_files_only=True)
    if args.probe_report:
        report = probe_overflows(
            json.loads(args.probe_report.read_text(encoding="utf-8")), tokenizer,
        )
    else:
        embedding_tokenizer = AutoTokenizer.from_pretrained("BAAI/bge-m3", local_files_only=True)
        datasets = {name: path for name, path in DEFAULT_DATASETS.items()
                    if not args.only_dataset or name in args.only_dataset}
        report = audit_datasets(
            datasets, tokenizer, embedding_tokenizer, SpacySentenceSegmenter({}),
            args.limit_per_dataset,
        )
        report["tokenizers"] = {"comet": tokenizer.name_or_path,
                                "embedding": embedding_tokenizer.name_or_path}
    report["versions"] = {name: version(name) for name in (
        "unbabel-comet", "transformers", "spacy", "sentalign",
    )}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    if "by_dataset" in report:
        print(json.dumps(report["by_dataset"], indent=2))
    else:
        for probe in report["probes"]:
            print(probe["dataset"], probe["full_sentence_tokens"], "-> ordinary retained",
                  probe["ordinary_comet_retained_tokens"], "; aligned guard rejected")
    print(f"Saved audit to {args.output}")


if __name__ == "__main__":
    main()