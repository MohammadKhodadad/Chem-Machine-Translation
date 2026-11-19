from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
SPEC = importlib.util.spec_from_file_location("audit_comet_input_coverage", SCRIPTS /
                                           "audit_comet_input_coverage.py")
runner = importlib.util.module_from_spec(SPEC)
sys.path.insert(0, str(SCRIPTS))
try:
    SPEC.loader.exec_module(runner)
finally:
    sys.path.remove(str(SCRIPTS))


def test_sentence_histogram_keeps_510_inside_limit_and_preserves_tail():
    sys.path.insert(0, str(SCRIPTS))
    try:
        from plot_comet_sentence_lengths import UPPER_BOUNDS, histogram
    finally:
        sys.path.remove(str(SCRIPTS))
    counts = {0: 1, 50: 2, 510: 3, 511: 4, 8000: 5, 8001: 6}
    result = histogram(counts)
    boundary = UPPER_BOUNDS.index(510)
    assert result[0] == 3
    assert result[boundary] == 3
    assert result[boundary + 1] == 4
    assert result[-2:] == [5, 6]
    assert sum(result) == sum(counts.values())


class WordTokenizer:
    def __call__(self, texts, *, add_special_tokens, truncation):
        assert add_special_tokens is True
        assert truncation is False
        return {"input_ids": [[0] * (len(text.split()) + 2) for text in texts]}


class Segmenter:
    def segment(self, text, language):
        return [part.strip() for part in text.splitlines() if part.strip()]


def audit(text, segmenter=None):
    return runner.audit_text(text, "en", WordTokenizer(), WordTokenizer(),
                             segmenter or Segmenter())


@pytest.mark.parametrize("count, overflows", [(508, False), (509, True)])
def test_comet_boundary_includes_special_tokens(count, overflows):
    result = audit("word " * count)
    assert bool(result["overlong_sentences"]) is overflows
    assert result["max_sentence_tokens"] == count + 2
    assert result["nonwhitespace_preserved"] is True


def test_small_sentences_do_not_guarantee_merged_span_fits():
    result = audit("\n".join(["word " * 200] * 4))
    assert not result["overlong_sentences"]
    assert result["full_tokens"] == result["max_local_span_tokens"] == 802
    assert result["max_sentence_tokens"] == 202


def test_whitespace_normalization_is_not_text_loss_but_dropped_words_are():
    assert audit("  first\n\n second  ")["nonwhitespace_preserved"] is True

    class DroppingSegmenter:
        def segment(self, text, language):
            return ["first"]

    assert audit("first second", DroppingSegmenter())["nonwhitespace_preserved"] is False


def test_pair_summary_counts_records_and_does_not_call_them_neural_successes():
    texts = {"long": audit("word " * 509), "short": audit("a\nb")}
    records = [{"source": "long", "reference": "short"},
               {"source": "short", "reference": "short"}]
    result = runner.summarize_records(records, texts)
    assert result["records"] == 2
    assert result["ordinary_whole_record_overflow"] == 1
    assert result["single_sentence_comet_overflow"] == 1
    assert result["single_sentence_length_safe"] == 1
    assert result["text_preservation_failure"] == 0


def test_embedding_budget_and_empty_text_are_separate_blockers():
    texts = {"long": audit("word " * 8192), "empty": audit("")}
    summary = runner.summarize_records([{"source": "long", "reference": "empty"}], texts)
    assert summary["single_sentence_embedding_overflow"] == 1
    assert summary["empty_side"] == 1
    assert summary["single_sentence_length_safe"] == 0


@pytest.mark.parametrize("corruption", [None, "content", "length"])
def test_sentence_distributions_deduplicate_inputs_but_keep_pair_rows(monkeypatch, corruption):
    sys.path.insert(0, str(SCRIPTS))
    try:
        import plot_comet_sentence_lengths as plotter
    finally:
        sys.path.remove(str(SCRIPTS))
    texts = {}

    def add_text(text, language):
        key = language + ":" + runner.sha256(text.encode("utf-8")).hexdigest()
        texts[key] = {**audit(text), "language": language}
        return key

    long_text, short_text, reference = "word " * 509, "first\nsecond", "Referenz"
    long_key = add_text(long_text, "en")
    short_key = add_text(short_text, "en")
    reference_key = add_text(reference, "de")
    report = {
        "manifests": {"sample": "sample/manifest.jsonl"}, "text_audits": texts,
        "records": [{"dataset": "sample", "index": index, "source": source,
                     "reference": reference_key} for index, source in enumerate(
                         (long_key, short_key))],
    }
    pairs = [({"context": source}, {"context": reference})
             for source in (long_text, short_text)]

    class Loader:
        def __init__(self, path):
            pass

        def rows_for_manifest(self, row):
            return pairs[row["index"]]

    monkeypatch.setattr(plotter, "ParallelRowsLoader", Loader)
    if corruption == "content":
        pairs[0][0]["context"] = "changed content"
    elif corruption == "length":
        texts[long_key]["sentence_tokens_total"] += 1
    if corruption:
        with pytest.raises(ValueError, match="saved audit"):
            plotter.collect_distributions(report, WordTokenizer(), Segmenter())
        return
    result = plotter.collect_distributions(report, WordTokenizer(), Segmenter())
    assert result["sentence_tokens_by_language"] == {"en": {511: 1, 3: 2}, "de": {3: 1}}
    assert result["max_sentence_tokens_per_unique_input_by_language"] == {
        "en": {511: 1, 3: 1}, "de": {3: 1},
    }
    assert result["max_sentence_tokens_per_pair_row"] == {511: 1, 3: 1}


@pytest.mark.parametrize("limit, expected_count", [(None, 2), (1, 1)])
def test_manifest_audit_does_not_filter_oversized_records(tmp_path, monkeypatch,
                                                        limit, expected_count):
    rows = [{"direction": "en-de", "source_row_id": str(index),
             "target_row_id": str(index), "source_language_code": "en",
             "target_language_code": "de"} for index in range(2)]
    (tmp_path / "sample-manifest.jsonl").write_text(
        "\n".join(json.dumps(row) for row in rows), encoding="utf-8",
    )

    class Loader:
        def __init__(self, path):
            pass

        def rows_for_manifest(self, row):
            text = "short" if row["source_row_id"] == "0" else "word " * 509
            return {"context": text}, {"context": "reference"}

    monkeypatch.setattr(runner, "ParallelRowsLoader", Loader)
    result = runner.audit_datasets(
        {"dataset": tmp_path}, WordTokenizer(), WordTokenizer(), Segmenter(), limit,
    )
    assert result["summary"]["records"] == expected_count
    assert result["all_manifest_records_requested"] is (limit is None)
    assert result["summary"]["single_sentence_comet_overflow"] == expected_count - 1