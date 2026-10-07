import importlib.util
import json
import sys
from pathlib import Path

SCRIPT_PATH = (
    Path(__file__).resolve().parents[1] / "scripts" / "create_google_patents_source_pairs.py"
)
SPEC = importlib.util.spec_from_file_location("create_google_patents_source_pairs", SCRIPT_PATH)
assert SPEC and SPEC.loader
source_exporter = importlib.util.module_from_spec(SPEC)
sys.modules["create_google_patents_source_pairs"] = source_exporter
SPEC.loader.exec_module(source_exporter)


def test_select_source_pair_rows_applies_language_filter_and_pair_limit() -> None:
    rows = [
        _row("en-de", "en", "de", "doc-1"),
        _row("en-de", "en", "de", "doc-2"),
        _row("en-fr", "en", "fr", "doc-3"),
        _row("fr-ja", "fr", "ja", "doc-4"),
        _row("en-de", "en", "de", "doc-empty", target_text=""),
    ]

    selected, skipped_empty = source_exporter.select_source_pair_rows(
        rows=rows,
        language_filter={"en", "de", "fr"},
        limit_per_pair=1,
        min_source_tokens=None,
        max_source_tokens=None,
        min_target_tokens=None,
        max_target_tokens=None,
        backfill_shortfalls=False,
        require_full_limit=False,
    )

    assert skipped_empty == 1
    assert [row["doc_id"] for row in selected] == ["doc-1", "doc-3"]
    assert [row["language_pair"] for row in selected] == ["en-de", "en-fr"]


def test_export_google_patents_source_pairs_writes_jsonl_and_metadata(tmp_path: Path) -> None:
    output_jsonl = tmp_path / "google_pairs.jsonl"
    metadata_output = tmp_path / "google_pairs_metadata.json"

    count, metadata = source_exporter.export_google_patents_source_pairs(
        rows=[
            _row("en-de", "en", "de", "doc-1"),
            _row("en-de", "en", "de", "doc-2"),
            _row("de-fr", "de", "fr", "doc-3"),
        ],
        output_jsonl=output_jsonl,
        metadata_output=metadata_output,
        dataset_id="test-dataset",
        split="train",
        revision="abc123",
        limit_per_pair=2,
        min_source_tokens=128,
        max_source_tokens=384,
        min_target_tokens=None,
        max_target_tokens=None,
        backfill_shortfalls=False,
        require_full_limit=False,
        languages=None,
    )

    rows = [json.loads(line) for line in output_jsonl.read_text(encoding="utf-8").splitlines()]
    metadata_from_disk = json.loads(metadata_output.read_text(encoding="utf-8"))

    assert count == 3
    assert rows[0]["example_id"] == "within-document:abstract:en-de:doc-1"
    assert len(rows[0]["source_text"].split()) == 180
    assert metadata == metadata_from_disk
    assert metadata["language_pair_counts"] == {"de-fr": 1, "en-de": 2}
    assert metadata["dataset_id"] == "test-dataset"
    assert metadata["revision"] == "abc123"
    assert metadata["min_source_tokens"] == 128
    assert metadata["max_source_tokens"] == 384


def test_select_source_pair_rows_applies_token_length_filter() -> None:
    selected, _ = source_exporter.select_source_pair_rows(
        rows=[
            _row("en-de", "en", "de", "too-short", source_token_count=60),
            _row("en-de", "en", "de", "in-range", source_token_count=180),
            _row("en-de", "en", "de", "too-long", source_token_count=600),
        ],
        language_filter=set(),
        limit_per_pair=10,
        min_source_tokens=128,
        max_source_tokens=384,
        min_target_tokens=None,
        max_target_tokens=None,
        backfill_shortfalls=False,
        require_full_limit=False,
    )

    assert [row["doc_id"] for row in selected] == ["in-range"]


def test_select_source_pair_rows_with_backfill_prefers_length_then_fills() -> None:
    selected, _ = source_exporter.select_source_pair_rows(
        rows=[
            _row("en-de", "en", "de", "source-and-target", source_token_count=180),
            _row(
                "en-de",
                "en",
                "de",
                "source-only",
                source_token_count=180,
                target_token_count=20,
            ),
            _row(
                "en-de",
                "en",
                "de",
                "target-only",
                source_token_count=20,
                target_token_count=180,
            ),
            _row("en-de", "en", "de", "fallback", source_token_count=20, target_token_count=20),
            _row("de-es", "de", "es", "shortfall", source_token_count=180),
        ],
        language_filter=set(),
        limit_per_pair=4,
        min_source_tokens=128,
        max_source_tokens=384,
        min_target_tokens=128,
        max_target_tokens=384,
        backfill_shortfalls=True,
        require_full_limit=True,
    )

    assert [row["doc_id"] for row in selected] == [
        "source-and-target",
        "source-only",
        "target-only",
        "fallback",
    ]


def test_select_source_pair_rows_keeps_only_accepted_exact_or_high_rows() -> None:
    exact = _row("en-de", "en", "de", "exact")
    exact.update({"pair_ok": True, "judge_verdict": "exact"})
    high = _row("en-de", "en", "de", "high")
    high.update({"pair_ok": True, "judge_verdict": "high"})
    medium = _row("en-de", "en", "de", "medium")
    medium.update({"pair_ok": False, "judge_verdict": "medium"})
    mislabeled = _row("en-de", "en", "de", "mislabeled")
    mislabeled.update({"pair_ok": False, "judge_verdict": "exact"})

    selected, _ = source_exporter.select_source_pair_rows(
        rows=[exact, high, medium, mislabeled],
        language_filter=set(),
        limit_per_pair=10,
        min_source_tokens=None,
        max_source_tokens=None,
        min_target_tokens=None,
        max_target_tokens=None,
        backfill_shortfalls=False,
        require_full_limit=False,
        exact_high_only=True,
    )

    assert [row["doc_id"] for row in selected] == ["exact", "high"]


def _row(
    language_pair: str,
    source_language: str,
    target_language: str,
    doc_id: str,
    target_text: str = "Target chemistry abstract.",
    source_token_count: int = 180,
    target_token_count: int = 180,
) -> dict[str, object]:
    target_text = target_text if target_text == "" else " ".join(["target"] * target_token_count)
    return {
        "example_id": f"within-document:abstract:{language_pair}:{doc_id}",
        "doc_id": doc_id,
        "corpus_id": "google-patents-chem",
        "source": "US",
        "group_key": "family-1",
        "pub_date": "20200101",
        "field": "abstract",
        "language_pair": language_pair,
        "source_language": source_language,
        "target_language": target_language,
        "source_text": " ".join(["chemistry"] * source_token_count),
        "target_text": target_text,
        "source_char_count": 27,
        "target_char_count": len(target_text),
        "source_token_count": source_token_count,
        "target_token_count": target_token_count,
        "source_sentence_count": 1,
        "target_sentence_count": 1,
        "source_tokens_per_sentence": 4.0,
        "target_tokens_per_sentence": 4.0,
        "tokenizer": "o200k_base",
        "selection_rule": "same document",
    }
