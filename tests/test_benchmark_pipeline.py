import json
import runpy
from pathlib import Path

from chem_machine_translation.benchmark.pipeline import generate_candidate_extraction_terms
from chem_machine_translation.benchmark_generation.config import (
    BenchmarkBuildConfig,
    BenchmarkCheckpointConfig,
    BenchmarkGenerationConfig,
    BenchmarkTerminologyConfig,
    load_benchmark_config,
)
from chem_machine_translation.benchmark_generation.pipeline import (
    TerminologyRuntime,
    attach_terminology_to_rows,
    build_terminology_runtime,
    refined_terms_from_manifest,
    run_benchmark_generation,
    select_source_pair_rows,
)
from chem_machine_translation.benchmark_generation.terminology_pipeline import (
    build_algorithmic_generator,
    build_chemistry_generator,
    build_legal_generator,
)
from chem_machine_translation.config import Settings
from chem_machine_translation.data.terminology import DatasetTerminologyTerm
from chem_machine_translation.translation.iate import LocalIATEClient


class _FakeChemistryGenerator:
    def generate(self, **kwargs: object) -> list[DatasetTerminologyTerm]:
        assert kwargs["target_language"] == "French"
        return [
            DatasetTerminologyTerm(
                source_term="",
                target_terms=("chlorure de sodium",),
                reference_candidates=("chlorure de sodium",),
                category="chemical",
                source="llm_target",
                term_group="llm",
                confidence=0.91,
            )
        ]


class _FakeRefiner:
    def refine(self, **kwargs: object) -> list[DatasetTerminologyTerm]:
        candidates = kwargs["candidates"]
        assert len(candidates) == 1
        assert kwargs["max_terms"] == 8
        return [
            DatasetTerminologyTerm(
                source_term="",
                target_terms=("chlorure de sodium",),
                reference_candidates=("chlorure de sodium",),
                category="chemical",
                source="llm_target+llm_refiner_chem",
                term_group="refined",
                confidence=0.95,
                decision="keep_refined",
            )
        ]


class _FailingGenerator:
    def generate(self, **kwargs: object) -> list[DatasetTerminologyTerm]:
        raise AssertionError("checkpointed extractor stage should have been reused")


class _FailingRefiner:
    def refine(self, **kwargs: object) -> list[DatasetTerminologyTerm]:
        raise AssertionError("checkpointed refiner stage should have been reused")


def test_load_benchmark_config_resolves_standard_chemistry_config() -> None:
    config = load_benchmark_config("config/benchmark_generation/chemistry.toml")

    assert config.name == "google_patents_chemistry"
    assert config.domain == "chemistry"
    assert config.builds[0].kind == "google_patents_snapshot"
    assert config.builds[0].selection_mode == "per_direction"
    assert config.builds[0].limit == 250
    assert config.builds[0].bidirectional is True
    assert config.checkpoint.enabled is True
    assert config.checkpoint.resume is True
    assert config.checkpoint.work_dir.name == "benchmark_work"
    assert config.terminology.candidate_extractors == (
        "llm_chemistry",
        "stanza_ud",
        "xlmr_nobi",
        "spacy",
    )
    assert "local_iate" in config.terminology.external_evidence_sources
    assert "pubchem" in config.terminology.external_evidence_sources
    assert config.terminology.refined_max_terms == 8
    assert config.terminology.local_iate_path is not None
    assert config.terminology.local_iate_path.name == "iate"


def test_load_benchmark_config_resolves_standard_legal_config() -> None:
    config = load_benchmark_config("config/benchmark_generation/legal.toml")

    assert config.name == "jrc_acquis_legal"
    assert config.domain == "jrc"
    assert [build.name for build in config.builds] == ["articles", "definitions"]
    assert all(build.kind == "jrc_acquis_snapshot" for build in config.builds)
    assert all(build.selection_mode == "anchored" for build in config.builds)
    assert all(build.anchor_limit == 250 for build in config.builds)
    assert config.checkpoint.enabled is True
    assert config.checkpoint.resume is True
    assert [build.output_dir.name for build in config.builds] == [
        "jrc_acquis_anchored_articles_250_anchors",
        "jrc_acquis_anchored_definitions_250_anchors",
    ]
    assert config.terminology.candidate_extractors == (
        "llm_legal",
        "stanza_ud",
        "xlmr_nobi",
        "spacy",
    )
    assert config.terminology.external_evidence_sources == (
        "local_iate",
        "wikidata",
        "unterm",
    )


def test_external_dataset_terms_are_merged_before_generated_candidates(tmp_path: Path) -> None:
    manifest_path = tmp_path / "external-manifest.jsonl"
    manifest_path.write_text(
        json.dumps(
            {
                "source_id": "example-1",
                "terminology": [
                    {
                        "target_terms": ["Council of Europe"],
                        "source": "legal_llm",
                        "term_group": "llm",
                        "confidence": 0.9,
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    terminology = BenchmarkTerminologyConfig(
        domain="jrc",
        candidate_max_terms=1,
        candidate_extractors=("external_dataset",),
        external_dataset_manifest=manifest_path,
        external_dataset_source="glm_flash_ext",
        llm_curation=False,
    )
    runtime = build_terminology_runtime(terminology, settings=Settings())

    terms = generate_candidate_extraction_terms(
        {
            "source_id": "example-1",
            "_source_text": "Source text.",
            "_target_text": "Council of Europe.",
            "source_language": "English",
            "target_language": "English",
        },
        domain="jrc",
        terminology=terminology,
        runtime=runtime,
    )

    assert [term.target_terms for term in terms] == [("Council of Europe",)]
    assert terms[0].source == "glm_flash_ext+legal_llm"


def test_generator_factories_map_extractor_and_verifier_flags() -> None:
    chemistry = BenchmarkTerminologyConfig(
        domain="chemistry",
        candidate_extractors=("llm_chemistry", "stanza_ud", "xlmr_nobi", "spacy"),
        external_evidence_sources=("local_iate", "wikidata", "pubchem"),
    )
    chemistry_generator = build_chemistry_generator(chemistry, client=object())

    assert chemistry_generator is not None
    assert chemistry_generator.use_llm is True
    assert chemistry_generator.use_iate is True
    assert isinstance(chemistry_generator.iate_client, LocalIATEClient)
    assert chemistry_generator.iate_source_name == "local_iate"
    assert chemistry_generator.use_wikidata is True
    assert chemistry_generator.use_pubchem is True
    assert chemistry_generator.extractor_names == (
        "TargetTerminologyExtractor",
        "XLMRNOBITerminologyExtractor",
        "SpaCyTerminologyExtractor",
    )

    legal = BenchmarkTerminologyConfig(
        domain="jrc",
        candidate_extractors=("llm_legal", "stanza_ud", "spacy"),
        external_evidence_sources=("local_iate", "wikidata", "unterm"),
    )
    legal_generator = build_legal_generator(legal, client=object())
    algorithmic_generator = build_algorithmic_generator(legal)

    assert legal_generator is not None
    assert legal_generator.use_iate is True
    assert isinstance(legal_generator.iate_client, LocalIATEClient)
    assert legal_generator.iate_source_name == "local_iate"
    assert legal_generator.use_wikidata is True
    assert legal_generator.use_unterm is True
    assert algorithmic_generator is not None
    assert algorithmic_generator.extractor_names == (
        "TargetTerminologyExtractor",
        "SpaCyTerminologyExtractor",
    )


def test_run_benchmark_generation_smoke_without_terminology(tmp_path: Path) -> None:
    source_path = tmp_path / "source.jsonl"
    output_dir = tmp_path / "benchmark"
    source_path.write_text(
        json.dumps(
            {
                "example_id": "example-1",
                "doc_id": "doc-1",
                "language_pair": "de-fr",
                "source_language": "de",
                "target_language": "fr",
                "source_text": "Quelle mit einem chemischen Verfahren.",
                "target_text": "Cible avec un procédé chimique.",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    config = BenchmarkGenerationConfig(
        name="smoke",
        domain="chemistry",
        builds=(
            BenchmarkBuildConfig(
                name="tiny",
                kind="google_patents_snapshot",
                source_pairs_jsonl=source_path,
                output_dir=output_dir,
                languages=("de", "fr"),
                limit=1,
            ),
        ),
        terminology=BenchmarkTerminologyConfig(
            domain="chemistry",
            candidate_extractors=(),
            external_evidence_sources=(),
            llm_curation=False,
        ),
    )

    result = run_benchmark_generation(
        config,
        settings=Settings(openai_api_key=None),
        runtime=TerminologyRuntime(),
    )

    assert result.builds[0].row_count == 1
    manifest_path = output_dir / "de-fr" / "google-patents-de-fr-1-manifest.jsonl"
    row = json.loads(manifest_path.read_text(encoding="utf-8").strip())
    assert row["direction"] == "de-fr"
    assert row["terminology"] == []
    metadata = json.loads((output_dir / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["row_count"] == 1
    assert metadata["direction_count"] == 1
    assert metadata["overall"]["source_tokens"]["count"] == 1
    assert metadata["overall"]["candidate_terms_per_row"]["buckets"]["0"] == {
        "count": 1,
        "pct": 100.0,
    }


def test_anchor_limit_selects_complete_jrc_anchor(tmp_path: Path) -> None:
    source_path = tmp_path / "source.jsonl"
    rows = [
        {
            "example_id": f"{anchor}:{direction}",
            "doc_id": anchor,
            "anchor_id": f"en:{anchor}",
            "language_pair": direction,
            "source_language": direction.split("-")[0],
            "target_language": direction.split("-")[1],
            "source_text": f"source {anchor} {direction}",
            "target_text": f"target {anchor} {direction}",
        }
        for anchor in ("doc-1", "doc-2")
        for direction in ("en-de", "de-en", "en-fr", "fr-en", "de-fr", "fr-de")
    ]
    source_path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )
    build = BenchmarkBuildConfig(
        name="tiny-anchored",
        kind="jrc_acquis_snapshot",
        source_pairs_jsonl=source_path,
        output_dir=tmp_path / "out",
        languages=("en", "de", "fr"),
        limit=250,
        anchor_limit=1,
    )

    selected = select_source_pair_rows(build)

    assert sorted(selected) == ["de-en", "de-fr", "en-de", "en-fr", "fr-de", "fr-en"]
    assert sum(len(rows) for rows in selected.values()) == 6
    assert {row["anchor_id"] for rows in selected.values() for row in rows} == {"en:doc-1"}


def test_jrc_manifest_preserves_anchor_metadata(tmp_path: Path) -> None:
    source_path = tmp_path / "source.jsonl"
    output_dir = tmp_path / "benchmark"
    source_path.write_text(
        "".join(
            json.dumps(row) + "\n"
            for row in [
                {
                    "example_id": "en:doc-1:chunk-0001",
                    "doc_id": "doc-1",
                    "anchor_id": "en:doc-1",
                    "language_pair": "en-de",
                    "source_language": "en",
                    "target_language": "de",
                    "source_text": "Source legal text.",
                    "target_text": "Target legal text.",
                    "section_type": "article",
                },
                {
                    "example_id": "de:doc-1:chunk-0001",
                    "doc_id": "doc-1",
                    "anchor_id": "en:doc-1",
                    "language_pair": "de-en",
                    "source_language": "de",
                    "target_language": "en",
                    "source_text": "Target legal text.",
                    "target_text": "Source legal text.",
                    "section_type": "article",
                },
            ]
        ),
        encoding="utf-8",
    )
    config = BenchmarkGenerationConfig(
        name="smoke",
        domain="jrc",
        builds=(
            BenchmarkBuildConfig(
                name="tiny",
                kind="jrc_acquis_snapshot",
                source_pairs_jsonl=source_path,
                output_dir=output_dir,
                languages=("en", "de"),
                limit=1,
                anchor_limit=1,
            ),
        ),
        terminology=BenchmarkTerminologyConfig(
            domain="jrc",
            candidate_extractors=(),
            external_evidence_sources=(),
            llm_curation=False,
        ),
    )

    run_benchmark_generation(
        config,
        settings=Settings(openai_api_key=None),
        runtime=TerminologyRuntime(),
    )

    manifest_path = output_dir / "en-de" / "jrc-acquis-en-de-1-manifest.jsonl"
    row = json.loads(manifest_path.read_text(encoding="utf-8").strip())
    assert row["anchor_id"] == "en:doc-1"
    assert row["section_type"] == "article"


def test_llm_curation_appends_refined_terms_to_manifest_rows() -> None:
    row = {
        "source_language": "German",
        "target_language": "French",
        "_source_text": "Natriumchlorid",
        "_target_text": "chlorure de sodium",
        "terminology": [],
    }
    terminology = BenchmarkTerminologyConfig(
        domain="chemistry",
        candidate_extractors=("llm_chemistry",),
        external_evidence_sources=(),
        llm_curation=True,
        refined_max_terms=8,
    )

    rows = attach_terminology_to_rows(
        [row],
        domain="chemistry",
        terminology=terminology,
        runtime=TerminologyRuntime(
            chemistry_generator=_FakeChemistryGenerator(),  # type: ignore[arg-type]
            curator=_FakeRefiner(),  # type: ignore[arg-type]
        ),
    )

    assert [term["term_group"] for term in rows[0]["terminology"]] == ["llm", "refined"]
    assert refined_terms_from_manifest(rows[0])[0].target_terms == ("chlorure de sodium",)


def test_checkpointed_generation_resumes_completed_terminology_stages(tmp_path: Path) -> None:
    source_path = tmp_path / "source.jsonl"
    output_dir = tmp_path / "benchmark"
    work_dir = tmp_path / "benchmark_work"
    source_path.write_text(
        json.dumps(
            {
                "example_id": "example-1",
                "doc_id": "doc-1",
                "language_pair": "de-fr",
                "source_language": "de",
                "target_language": "fr",
                "source_text": "Quelle mit Natriumchlorid.",
                "target_text": "Cible avec chlorure de sodium.",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    config = BenchmarkGenerationConfig(
        name="resume-smoke",
        domain="chemistry",
        builds=(
            BenchmarkBuildConfig(
                name="tiny",
                kind="google_patents_snapshot",
                source_pairs_jsonl=source_path,
                output_dir=output_dir,
                languages=("de", "fr"),
                limit=1,
            ),
        ),
        terminology=BenchmarkTerminologyConfig(
            domain="chemistry",
            candidate_extractors=("llm_chemistry",),
            external_evidence_sources=(),
            llm_curation=True,
        ),
        checkpoint=BenchmarkCheckpointConfig(work_dir=work_dir),
    )

    run_benchmark_generation(
        config,
        settings=Settings(openai_api_key=None),
        runtime=TerminologyRuntime(
            chemistry_generator=_FakeChemistryGenerator(),  # type: ignore[arg-type]
            curator=_FakeRefiner(),  # type: ignore[arg-type]
        ),
    )
    run_benchmark_generation(
        config,
        settings=Settings(openai_api_key=None),
        runtime=TerminologyRuntime(
            chemistry_generator=_FailingGenerator(),  # type: ignore[arg-type]
            curator=_FailingRefiner(),  # type: ignore[arg-type]
        ),
    )

    checkpoint_dir = work_dir / "resume-smoke" / "tiny" / "directions" / "de-fr"
    assert (checkpoint_dir / "02_candidate_extraction.jsonl").exists()
    assert (checkpoint_dir / "03_external_evidence.jsonl").exists()
    assert (checkpoint_dir / "04_llm_curated_terms.jsonl").exists()
    assert (checkpoint_dir / "05_manifest_rows.jsonl").exists()

    manifest_path = output_dir / "de-fr" / "google-patents-de-fr-1-manifest.jsonl"
    row = json.loads(manifest_path.read_text(encoding="utf-8").strip())
    assert [term["term_group"] for term in row["terminology"]] == ["llm", "refined"]


def test_zero_argument_runner_config_paths() -> None:
    chemistry_globals = runpy.run_path("scripts/generate_chemistry_benchmark.py")
    legal_globals = runpy.run_path("scripts/generate_legal_benchmark.py")

    assert chemistry_globals["CONFIG_PATH"] == Path("config/benchmark_generation/chemistry.toml")
    assert legal_globals["CONFIG_PATH"] == Path("config/benchmark_generation/legal.toml")

