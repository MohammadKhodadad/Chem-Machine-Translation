import importlib.util
import json
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location(
    "evaluate_real_document_metrics", SCRIPTS / "evaluate_real_document_metrics.py",
)
assert SPEC and SPEC.loader
runner = importlib.util.module_from_spec(SPEC)
try:
    SPEC.loader.exec_module(runner)
finally:
    sys.path.remove(str(SCRIPTS))

def test_coverage_summary_uses_pooled_counts_not_mean_document_percentages():
    rows = []
    for matched, excluded in ((2, 1), (8, 0)):
        coverage = {
            "total_blocks": matched, "matched_blocks": matched,
            "scored_blocks": matched - excluded, "excluded_blocks": excluded,
            "sentences": {side: {"total_sentences": matched, "excluded_sentences": excluded,
                                 "scored_sentences": matched - excluded}
                          for side in ("source", "reference", "prediction")},
        }
        rows.append({
            "dataset": "sample", "direction": "en-de",
            "scores": {metric: 0.9 for metric in runner.METRICS},
            "metric_details": {metric: {"coverage": coverage} for metric in runner.METRICS[1:]},
        })
    summary = runner.summarize_coverage(rows)
    assert len(summary) == 4
    assert all(item["excluded_matched_block_percentage"] == 10 for item in summary)
    assert all(item["sentences"]["reference"]["excluded_percentage"] == 10 for item in summary)


REAL_DOCUMENTS = json.loads(
    (Path(__file__).parent / "fixtures" / "real_document_metrics.json").read_text(encoding="utf-8")
)["documents"]
CHINESE_DOCUMENTS = json.loads(
    (
        Path(__file__).parent / "fixtures" / "real_document_metrics_chinese_length_safe.json"
    ).read_text(encoding="utf-8")
)["documents"]


def test_real_variants_use_only_reference_and_real_donor_sentences():
    document = {"id": "one", "dataset": "patents", "target_language": "de",
                "reference": "a\nb\nc\nd", "reference_sentences": ["a", "b", "c", "d"]}
    donor = {"id": "two", "dataset": "patents", "target_language": "de",
             "reference": "x\ny", "reference_sentences": ["x", "y"]}
    variants = {item["condition"]: item for item in runner.build_variants(document, donor)}
    assert len(variants) == 8
    assert variants["reference_control"]["prediction"] == document["reference"]
    assert variants["tail_omission_50"]["prediction"] == "a\nb"
    assert variants["tail_replacement_50"]["prediction"] == "a\nb\nx\ny"
    assert variants["tail_replacement_75"]["prediction"] == "a\nx\ny\nx"
    assert variants["wrong_document"]["prediction"] == donor["reference"]
    assert variants["tail_replacement_50"]["changed_reference_indices"] == [2, 3]


def test_real_variants_reject_cross_language_donor():
    with pytest.raises(ValueError, match="same target language"):
        runner.build_variants({"target_language": "de"}, {"target_language": "fr"})


def test_real_summary_reports_scoring_failures_without_imputation():
    result = runner.summarize([
        {"dataset": "patents", "condition": "control",
         "scores": {"comet": 0.9, "reference_assignment_comet": 0.8, "sentalign_comet": None}},
    ])
    sentalign = next(row for row in result if row["metric"] == "sentalign_comet")
    assert sentalign["case_count"] == 1
    assert sentalign["scored_count"] == 0
    assert sentalign["mean"] is None


def test_quality_checks_record_failures_instead_of_assuming_expected_order():
    results = []
    for condition, score in (
        ("reference_control", 0.9), ("tail_omission_25", 0.9), ("tail_omission_50", 0.8),
        ("tail_omission_75", 0.5), ("tail_replacement_25", 0.8),
        ("tail_replacement_50", 0.7), ("tail_replacement_75", 0.3), ("wrong_document", 0.1),
    ):
        results.append({"document_id": "one", "dataset": "patents", "condition": condition,
                        "scores": dict.fromkeys(runner.METRICS, score)})
    checks = runner.quality_checks(results)
    assert len(checks) == 27
    assert sum(check["passed"] is False for check in checks) == 6


def test_real_fixture_covers_all_three_datasets_and_directions():
    assert len(REAL_DOCUMENTS) == 9
    assert {document["dataset"] for document in REAL_DOCUMENTS} == {
        "google_patents", "jrc_articles", "jrc_definitions",
    }
    for dataset in {document["dataset"] for document in REAL_DOCUMENTS}:
        documents = [document for document in REAL_DOCUMENTS if document["dataset"] == dataset]
        assert {document["direction"] for document in documents} == {"en-de", "en-fr", "en-es"}
        assert len({document["provenance"]["doc_id"] for document in documents}) == 3


def test_chinese_fixture_uses_same_eligibility_as_original_cohort():
    assert len(REAL_DOCUMENTS) == 9
    assert len(CHINESE_DOCUMENTS) == 1
    document = CHINESE_DOCUMENTS[0]
    assert document["dataset"] == "google_patents"
    assert document["direction"] == "en-zh"
    assert document["source_language"] == "en"
    assert document["target_language"] == "zh"
    assert document["selection_allow_overlong_sentences"] is False
    assert document["maximum_sentence_tokens"] == 388
    assert len(document["reference_sentences"]) == 5
    assert document["provenance"]["publication_number"] == "TW-201519892-A"
    assert document["donor"]["selection_allow_overlong_sentences"] is False


@pytest.mark.parametrize(
    "document", REAL_DOCUMENTS + CHINESE_DOCUMENTS, ids=lambda document: document["id"],
)
def test_actual_long_record_provenance_and_all_eight_variants(document):
    donor = document["donor"]
    for item in (document, donor):
        assert runner.text_hash(item["source"]) == item["source_sha256"]
        assert runner.text_hash(item["reference"]) == item["reference_sha256"]
        assert min(item["full_token_counts"].values()) >= 600
        assert max(item["full_token_counts"].values()) <= 2000
        assert item["maximum_sentence_tokens"] <= 510
        assert item["provenance"]["manifest_line"] >= 1
    assert donor["dataset"] == document["dataset"]
    assert donor["target_language"] == document["target_language"]
    assert donor["provenance"]["doc_id"] != document["provenance"]["doc_id"]
    variants = runner.build_variants(document, donor)
    assert len(variants) == 8
    assert variants[0]["prediction"] == document["reference"]
    assert variants[-1]["prediction"] == donor["reference"]
    allowed_sentences = set(document["reference_sentences"] + donor["reference_sentences"])
    for variant in variants[1:-1]:
        assert variant["prediction"]
        assert variant["prediction"] != document["reference"]
        assert set(variant["prediction"].splitlines()).issubset(allowed_sentences)
        assert runner.text_hash(variant["prediction"]) == variant["prediction_sha256"]


@pytest.mark.parametrize("allow_overlong, expected_primary, expected_donor, eligible", [
    (False, "2", "1", 3), (True, "3", "2", 4),
])
def test_selection_reads_actual_context_column_and_keeps_distinct_donor(
    tmp_path, monkeypatch, allow_overlong, expected_primary, expected_donor, eligible,
):
    metadata = []
    pairs = {}
    for index, count in enumerate((4, 5, 6, 600)):
        identity = str(index)
        source = " | ".join(["word " * count] * 4)
        reference = " | ".join([f"target{index} " * count] * 4)
        if index == 3:
            source = " | ".join(["word " * count] + ["word"] * 3)
            reference = " | ".join([f"target{index} " * count] + [f"target{index}"] * 3)
        pairs[identity] = ({"context": source}, {"context": reference})
        metadata.append({
            "dataset": "patents", "source_id": identity, "source_row_id": identity,
            "target_row_id": identity, "doc_id": identity, "direction": "en-de",
            "source_language_code": "en", "target_language_code": "de",
        })
    manifest = tmp_path / "sample-manifest.jsonl"
    manifest.write_text("\n".join(json.dumps(row) for row in metadata), encoding="utf-8")

    class Loader:
        def __init__(self, path):
            pass

        def rows_for_manifest(self, row):
            return pairs[row["source_id"]]

    class Tokenizer:
        def encode(self, text, **kwargs):
            return text.split()

    class Segmenter:
        def segment(self, text, language):
            return [part.strip() for part in text.split("|")]

    monkeypatch.setattr(runner, "ParallelRowsLoader", Loader)
    documents, screening = runner.select_documents(
        {"patents": tmp_path}, Tokenizer(), Segmenter(), ["en-de"], min_tokens=10,
        allow_overlong_sentences=allow_overlong,
    )
    assert documents[0]["provenance"]["source_id"] == expected_primary
    assert documents[0]["donor"]["provenance"]["source_id"] == expected_donor
    assert documents[0]["selection_allow_overlong_sentences"] is allow_overlong
    assert screening[0]["eligible_count"] == eligible