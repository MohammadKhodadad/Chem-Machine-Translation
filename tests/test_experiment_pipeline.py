import json
from pathlib import Path

from chem_machine_translation.config import Settings
from chem_machine_translation.experiment.config import load_experiment_config
from chem_machine_translation.experiment.pipeline import run_experiment


def test_load_standard_experiment_config() -> None:
    config = load_experiment_config("config/experiments/legal_one_anchor_smoke.toml")

    assert config.name == "legal_one_anchor_smoke"
    assert config.benchmark.run_generation is False
    assert config.model_runs[0].name == "dry_run_baseline"
    assert config.model_runs[0].translator == "dry-run"
    assert config.evaluation.metrics == (
        "sequence_similarity",
        "bleu",
        "chrf2++",
        "terminology_success_rate",
        "variant_aware_terminology_success_rate",
        "target_term_coverage",
        "variant_aware_target_term_coverage",
    )


def test_run_experiment_generates_predictions_scores_and_summary(tmp_path: Path) -> None:
    source_path = tmp_path / "source.jsonl"
    benchmark_dir = tmp_path / "benchmark"
    run_dir = tmp_path / "runs" / "tiny_experiment"
    source_path.write_text(
        json.dumps(
            {
                "example_id": "example-1",
                "doc_id": "doc-1",
                "language_pair": "en-de",
                "source_language": "en",
                "target_language": "de",
                "source_text": "Source legal text.",
                "target_text": "Zieltext.",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    benchmark_config_path = tmp_path / "benchmark.toml"
    benchmark_config_path.write_text(
        f"""
name = "tiny_legal"
domain = "jrc"

[[builds]]
name = "articles"
kind = "jrc_acquis_snapshot"
source_pairs_jsonl = "{source_path.as_posix()}"
output_dir = "{benchmark_dir.as_posix()}"

[selection]
mode = "per_direction"
languages = ["en", "de"]
limit = 1

[terminology]
domain = "jrc"
candidate_extractors = []
external_evidence_sources = []
llm_curation = false
""",
        encoding="utf-8",
    )
    experiment_config = load_experiment_config(
        write_experiment_config(tmp_path, benchmark_config_path, run_dir)
    )

    result = run_experiment(experiment_config, settings=Settings(openai_api_key=None))

    assert result.name == "tiny_experiment"
    assert result.benchmark_builds[0].row_count == 1
    assert result.model_results[0].row_count == 1
    predictions = load_jsonl(result.model_results[0].predictions_path)
    scores = load_jsonl(result.model_results[0].scores_path)
    summary = json.loads(result.summary_json_path.read_text(encoding="utf-8"))
    assert predictions[0]["predicted_translation"] == "Source legal text."
    assert "sequence_similarity" in scores[0]["metrics"]
    assert summary["row_count"] == 1
    assert result.summary_markdown_path.exists()


def test_prediction_resume_retries_previous_error_rows(tmp_path: Path) -> None:
    source_path = tmp_path / "source.jsonl"
    benchmark_dir = tmp_path / "benchmark"
    run_dir = tmp_path / "runs" / "retry_experiment"
    source_path.write_text(
        json.dumps(
            {
                "example_id": "example-1",
                "doc_id": "doc-1",
                "language_pair": "en-de",
                "source_language": "en",
                "target_language": "de",
                "source_text": "Source legal text.",
                "target_text": "Zieltext.",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    benchmark_config_path = tmp_path / "benchmark.toml"
    benchmark_config_path.write_text(
        f'''
name = "tiny_legal"
domain = "jrc"

[[builds]]
name = "articles"
kind = "jrc_acquis_snapshot"
source_pairs_jsonl = "{source_path.as_posix()}"
output_dir = "{benchmark_dir.as_posix()}"

[selection]
mode = "per_direction"
languages = ["en", "de"]
limit = 1

[terminology]
domain = "jrc"
candidate_extractors = []
external_evidence_sources = []
llm_curation = false
''',
        encoding="utf-8",
    )
    config = load_experiment_config(write_experiment_config(tmp_path, benchmark_config_path, run_dir))
    first_result = run_experiment(config, settings=Settings(openai_api_key=None))
    predictions_path = first_result.model_results[0].predictions_path
    predictions_path.write_text(
        json.dumps({"source_id": "example-1", "error": "AuthenticationError: unavailable"})
        + "\n",
        encoding="utf-8",
    )

    result = run_experiment(config, settings=Settings(openai_api_key=None))
    rows = load_jsonl(result.model_results[0].predictions_path)

    assert len(rows) == 1
    assert any(row["predicted_translation"] == "Source legal text." for row in rows)


def write_experiment_config(tmp_path: Path, benchmark_config_path: Path, run_dir: Path) -> Path:
    config_path = tmp_path / "experiment.toml"
    config_path.write_text(
        f"""
name = "tiny_experiment"

[benchmark]
config = "{benchmark_config_path.as_posix()}"
run_generation = true

[[model_runs]]
name = "dry_run_baseline"
translator = "dry-run"
translation_domain = "auto"
use_manifest_terminology = false

[evaluation]
name = "cheap"
metrics = ["sequence_similarity"]
terminology_groups = ["refined"]

[output]
run_dir = "{run_dir.as_posix()}"
""",
        encoding="utf-8",
    )
    return config_path


def load_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
