import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "evaluate_parallel_manifest.py"
SPEC = importlib.util.spec_from_file_location("evaluate_parallel_manifest", SCRIPT_PATH)
assert SPEC and SPEC.loader
evaluator = importlib.util.module_from_spec(SPEC)
sys.modules["evaluate_parallel_manifest"] = evaluator
SPEC.loader.exec_module(evaluator)


def test_resolve_translator_maps_openai_alias() -> None:
    assert evaluator.resolve_translator(None, "openai") == "one-shot"
    assert evaluator.resolve_translator("dry-run", None) == "dry-run"


def test_resolve_translator_rejects_two_options() -> None:
    with pytest.raises(ValueError, match="Use either --translator"):
        evaluator.resolve_translator("one-shot", "openai")


def test_resolve_translation_domain_infers_legal_source() -> None:
    assert (
        evaluator.resolve_translation_domain(
            "auto",
            [{"dataset": "jrc_acquis", "direction": "en-es"}],
        )
        == "legal"
    )


def test_resolve_translation_domain_infers_chemistry_source() -> None:
    assert (
        evaluator.resolve_translation_domain(
            "auto",
            [{"dataset": "google_patents", "direction": "en-de"}],
        )
        == "chemistry"
    )


def test_aligned_comet_cli_accepts_configuration(monkeypatch) -> None:
    monkeypatch.setattr(sys, "argv", [
        "evaluate_parallel_manifest", "--dataset-dir", "unused", "--output", "unused.jsonl",
        "--metric", "aligned_comet", "--aligned-comet-config", "custom.toml",
    ])
    args = evaluator.parse_args()
    assert args.metric == ["aligned_comet"]
    assert args.aligned_comet_config == Path("custom.toml")


@pytest.mark.parametrize("metric_name", ["reference_assignment_metricx", "sentalign_metricx"])
def test_metricx_cli_accepts_shared_configuration(monkeypatch, metric_name):
    monkeypatch.setattr(sys, "argv", [
        "evaluate_parallel_manifest", "--dataset-dir", "unused", "--output", "unused.jsonl",
        "--metric", metric_name, "--metricx-config", "metricx.toml",
    ])
    args = evaluator.parse_args()
    assert args.metric == [metric_name]
    assert args.metricx_config == Path("metricx.toml")


@pytest.mark.parametrize("metric_name", ["reference_assignment_comet", "sentalign_comet"])
def test_named_document_metrics_accept_configuration(monkeypatch, metric_name):
    monkeypatch.setattr(sys, "argv", [
        "evaluate_parallel_manifest", "--dataset-dir", "unused", "--output", "unused.jsonl",
        "--metric", metric_name, f"--{metric_name.replace('_', '-')}-config", "custom.toml",
    ])
    args = evaluator.parse_args()
    assert args.metric == [metric_name]
    attribute = "aligned_comet_config" if metric_name == "reference_assignment_comet" else (
        "sentalign_comet_config"
    )
    assert getattr(args, attribute) == Path("custom.toml")
