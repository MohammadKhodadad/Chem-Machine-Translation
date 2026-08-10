import importlib.util
import json
import sys
from pathlib import Path

import pytest


def _load_script(name: str):
    script_path = Path(__file__).resolve().parents[1] / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, script_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


google_builder = _load_script("build_google_patents_eval_subset")
eurolex_builder = _load_script("build_eurolex_eval_subset")


def test_google_builder_requires_source_pairs_jsonl(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["build_google_patents_eval_subset.py"])

    with pytest.raises(SystemExit):
        google_builder.parse_args()


def test_google_builder_selects_source_pair_rows(tmp_path: Path) -> None:
    source_pairs = tmp_path / "google_pairs.jsonl"
    source_pairs.write_text(
        json.dumps(
            {
                "example_id": "gp-1",
                "doc_id": "US-1",
                "language_pair": "en-de",
                "source_language": "en",
                "target_language": "de",
                "source_text": "chemical catalyst reaction",
                "target_text": "chemischer Katalysator Reaktion",
            },
        )
        + "\n",
        encoding="utf-8",
    )

    selected = google_builder.select_source_pair_rows(
        source_pairs_jsonl=source_pairs,
        languages=["en", "de"],
        limit=10,
        min_input_tokens=1,
        max_input_tokens=20,
    )

    row = selected["en-de"][0]
    manifest_row = google_builder.build_source_pair_manifest_row(row)
    assert manifest_row["dataset"] == "google_patents"
    assert manifest_row["source_language_code"] == "en"
    assert manifest_row["target_language_code"] == "de"
    assert manifest_row["_source_row"]["context"] == "chemical catalyst reaction"


def test_eurolex_builder_requires_source_pairs_jsonl(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["build_eurolex_eval_subset.py"])

    with pytest.raises(SystemExit):
        eurolex_builder.parse_args()


def test_eurolex_builder_selects_source_pair_rows(tmp_path: Path) -> None:
    source_pairs = tmp_path / "eurolex_pairs.jsonl"
    source_pairs.write_text(
        json.dumps(
            {
                "example_id": "eu-1",
                "doc_id": "32000R0001",
                "language_pair": "en-fr",
                "source_language": "en",
                "target_language": "fr",
                "source_text": "Council regulation on agricultural policy",
                "target_text": "Règlement du Conseil sur la politique agricole",
                "eurovoc_labels": ["1000"],
                "eurovoc_descriptors": {"1000": {"fr": "politique agricole"}},
                "eurovoc_target_terms": [
                    {
                        "target": "politique agricole",
                        "term_group": "verified",
                        "verified_by": ["eurovoc"],
                    },
                ],
            },
        )
        + "\n",
        encoding="utf-8",
    )

    selected = eurolex_builder.select_source_pair_rows(
        source_pairs_jsonl=source_pairs,
        languages=["en", "fr"],
        limit=10,
        min_input_tokens=1,
        max_input_tokens=20,
    )

    row = selected["en-fr"][0]
    manifest_row = eurolex_builder.build_source_pair_manifest_row(
        row=row,
        include_eurovoc_terminology=True,
    )
    assert manifest_row["dataset"] == "eurolex"
    assert manifest_row["source_language_code"] == "en"
    assert manifest_row["target_language_code"] == "fr"
    assert manifest_row["terminology"][0]["target"] == "politique agricole"
