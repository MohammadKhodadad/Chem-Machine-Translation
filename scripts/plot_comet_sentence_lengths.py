from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path

from audit_comet_input_coverage import token_lengths
from evaluate_parallel_manifest import ParallelRowsLoader

LIMIT = 510
UPPER_BOUNDS = (50, 100, 150, 200, 300, 400, LIMIT, 750, 1000, 1500, 2000, 4000, 8000)
LANGUAGES = {
    "de": "German", "en": "English", "es": "Spanish", "fr": "French",
    "ja": "Japanese", "pt": "Portuguese", "ru": "Russian", "zh": "Chinese",
}


def histogram(counts):
    frequencies = [0] * (len(UPPER_BOUNDS) + 1)
    for length, count in counts.items():
        index = next((index for index, upper in enumerate(UPPER_BOUNDS)
                      if int(length) <= upper), len(UPPER_BOUNDS))
        frequencies[index] += count
    return frequencies


def collect_distributions(report, tokenizer, segmenter):
    sentences, inputs = defaultdict(Counter), defaultdict(Counter)
    seen, loaders = set(), {}
    for record in report["records"]:
        if all(record[side] in seen for side in ("source", "reference")):
            continue
        dataset = record["dataset"]
        if dataset not in loaders:
            loaders[dataset] = ParallelRowsLoader(Path(report["manifests"][dataset]).parent)
        actual = loaders[dataset].rows_for_manifest(record)
        for side, item in zip(("source", "reference"), actual, strict=True):
            key = record[side]
            if key in seen:
                continue
            previous = report["text_audits"][key]
            language, text = previous["language"], item["context"]
            if key != language + ":" + sha256(text.encode("utf-8")).hexdigest():
                raise ValueError(f"Input content differs from saved audit: {key}")
            segments = segmenter.segment(text, language)
            lengths = token_lengths(tokenizer, segments) if segments else []
            observed = (len(lengths), sum(lengths), max(lengths, default=0),
                        sum(length > LIMIT for length in lengths))
            expected = (previous["sentence_count"], previous["sentence_tokens_total"],
                        previous["max_sentence_tokens"], len(previous["overlong_sentences"]))
            if observed != expected:
                raise ValueError(f"Sentence token lengths differ from saved audit: {key}")
            sentences[language].update(lengths)
            inputs[language].update([max(lengths, default=0)])
            seen.add(key)
            if len(seen) % 1000 == 0:
                print(f"Verified {len(seen)} unique language/text inputs", flush=True)
    if seen != set(report["text_audits"]):
        raise ValueError("Not all saved text audits were reconstructed")
    pairs = Counter(max(report["text_audits"][record[side]]["max_sentence_tokens"]
                        for side in ("source", "reference")) for record in report["records"])
    return {"sentence_tokens_by_language": dict(sentences),
            "max_sentence_tokens_per_unique_input_by_language": dict(inputs),
            "max_sentence_tokens_per_pair_row": dict(pairs)}


def draw_bars(axis, counts, title):
    labels = [f"{lower + 1}-{upper}" for lower, upper in
              zip((0, *UPPER_BOUNDS[:-1]), UPPER_BOUNDS, strict=True)] + [">8000"]
    labels[0] = "0-50"
    frequencies = histogram(counts)
    boundary = UPPER_BOUNDS.index(LIMIT) + 0.5
    axis.bar(range(len(labels)), frequencies,
             color=["#167d8d" if index < boundary else "#cf493d"
                    for index in range(len(labels))], width=0.82)
    axis.axvline(boundary, color="#a92b21", linestyle="--", linewidth=1.6,
                 label="510-token limit")
    total = sum(frequencies)
    over = sum(count for length, count in counts.items() if int(length) > LIMIT)
    axis.set_title(f"{title} | n={total:,} | >510: {over:,} ({100 * over / total:.2f}%)",
                   loc="left", fontsize=11, pad=12)
    axis.set_xticks(range(len(labels)), labels, rotation=55, ha="right", fontsize=8)
    axis.set_yscale("log")
    axis.set_ylim(bottom=0.8, top=max(max(frequencies, default=1) * 3, 10))
    axis.set_ylabel("Count (log scale)")
    axis.set_xlabel("COMET tokens, including special tokens (inclusive bins)")
    axis.grid(axis="y", alpha=0.2)
    axis.set_axisbelow(True)
    axis.spines[["top", "right"]].set_visible(False)
    axis.legend(loc="upper right", fontsize=8, frameon=False)


def plot_distributions(distributions, output):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    all_sentences = Counter()
    for counts in distributions["sentence_tokens_by_language"].values():
        all_sentences.update({int(length): count for length, count in counts.items()})
    figure, axis = plt.subplots(figsize=(15, 6), layout="constrained")
    draw_bars(axis, all_sentences, "All sentences (all languages combined)")
    figure.savefig(output / "sentence_lengths_all_languages.png", dpi=160, facecolor="white")
    plt.close(figure)

    for key, filename, title in (
        ("sentence_tokens_by_language", "sentence_lengths_by_language.png",
         "Individual sentence lengths by language"),
        ("max_sentence_tokens_per_unique_input_by_language",
         "maximum_sentence_per_input_by_language.png",
         "Longest sentence per input text, by language"),
    ):
        groups = distributions[key]
        figure, axes = plt.subplots((len(groups) + 1) // 2, 2, figsize=(18, 18), squeeze=False,
                                    layout="constrained")
        figure.suptitle(title + "\nUnique language/text inputs; no truncation", fontsize=19)
        for axis, language in zip(axes.flat, sorted(groups), strict=False):
            draw_bars(axis, groups[language], f"{LANGUAGES.get(language, language)} ({language})")
        for axis in list(axes.flat)[len(groups):]:
            axis.set_visible(False)
        figure.savefig(output / filename, dpi=160, facecolor="white")
        plt.close(figure)
    figure, axis = plt.subplots(figsize=(15, 6), layout="constrained")
    draw_bars(axis, distributions["max_sentence_tokens_per_pair_row"],
              "Longest sentence per paired data row (maximum across source and reference)")
    figure.savefig(output / "maximum_sentence_per_pair_row.png", dpi=160, facecolor="white")
    plt.close(figure)


def main():
    parser = argparse.ArgumentParser(
        description="Plot verified COMET sentence-length distributions",
    )
    parser.add_argument("--audit", type=Path, default=Path(
        "reports/comet_input_coverage/full_benchmark_20261117.json"))
    parser.add_argument("--output-dir", type=Path, default=Path(
        "reports/comet_input_coverage/sentence_lengths_20261118"))
    args = parser.parse_args()
    digest = sha256(args.audit.read_bytes()).hexdigest()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    cache = args.output_dir / "distributions.json"
    if cache.exists():
        result = json.loads(cache.read_text(encoding="utf-8"))
        if result["audit_sha256"] != digest:
            raise ValueError("Cached distributions belong to a different coverage audit")
    else:
        from transformers import AutoTokenizer

        from chem_machine_translation.evaluation.aligned_comet import SpacySentenceSegmenter

        report = json.loads(args.audit.read_text(encoding="utf-8"))
        tokenizer = AutoTokenizer.from_pretrained("xlm-roberta-large", local_files_only=True)
        result = {
            "audit_sha256": digest, "token_limit_including_special_tokens": LIMIT,
            "counting_units": {
                "sentence": "Every segment in each unique language/text input, once.",
                "input": "One maximum sentence length per unique language/text input.",
                "pair_row": "One maximum across both sides for every original manifest row.",
            },
            **collect_distributions(report, tokenizer, SpacySentenceSegmenter({})),
        }
        cache.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    plot_distributions(result, args.output_dir)
    print(f"Saved distributions and four charts to {args.output_dir}")


if __name__ == "__main__":
    main()