import json
import runpy
from pathlib import Path

from chem_machine_translation.benchmark_generation.config import (
    BenchmarkBuildConfig,
    BenchmarkGenerationConfig,
    BenchmarkTerminologyConfig,
    load_benchmark_config,
)
from chem_machine_translation.benchmark_generation.pipeline import (
    TerminologyRuntime,
    attach_terminology_to_rows,
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


def test_load_benchmark_config_resolves_standard_chemistry_config() -> None:
    config = load_benchmark_config("config/benchmark_generation/chemistry.toml")

    assert config.name == "google_patents_chemistry"
    assert config.domain == "chemistry"
    assert config.builds[0].kind == "google_patents_snapshot"
    assert config.builds[0].limit == 250
    assert config.terminology.extractors == (
        "llm_chemistry",
        "stanza_ud",
        "xlmr_nobi",
        "spacy",
    )
    assert "pubchem" in config.terminology.verifiers
    assert config.terminology.refined_max_terms == 8


def test_load_benchmark_config_resolves_standard_legal_config() -> None:
    config = load_benchmark_config("config/benchmark_generation/legal.toml")

    assert config.name == "jrc_acquis_legal"
    assert config.domain == "jrc"
    assert [build.name for build in config.builds] == ["articles", "definitions"]
    assert all(build.kind == "jrc_acquis_snapshot" for build in config.builds)
    assert config.terminology.extractors == (
        "llm_legal",
        "stanza_ud",
        "xlmr_nobi",
        "spacy",
    )
    assert config.terminology.verifiers == ("iate", "wikidata", "unterm")


def test_generator_factories_map_extractor_and_verifier_flags() -> None:
    chemistry = BenchmarkTerminologyConfig(
        domain="chemistry",
        extractors=("llm_chemistry", "stanza_ud", "xlmr_nobi", "spacy"),
        verifiers=("iate", "wikidata", "pubchem"),
    )
    chemistry_generator = build_chemistry_generator(chemistry, client=object())

    assert chemistry_generator is not None
    assert chemistry_generator.use_llm is True
    assert chemistry_generator.use_iate is True
    assert chemistry_generator.use_wikidata is True
    assert chemistry_generator.use_pubchem is True
    assert chemistry_generator.extractor_names == (
        "TargetTerminologyExtractor",
        "XLMRNOBITerminologyExtractor",
        "SpaCyTerminologyExtractor",
    )

    legal = BenchmarkTerminologyConfig(
        domain="jrc",
        extractors=("llm_legal", "stanza_ud", "spacy"),
        verifiers=("iate", "wikidata", "unterm"),
    )
    legal_generator = build_legal_generator(legal, client=object())
    algorithmic_generator = build_algorithmic_generator(legal)

    assert legal_generator is not None
    assert legal_generator.use_iate is True
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
            extractors=(),
            verifiers=(),
            refiner=False,
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
        for direction in ("en-de", "de-en", "en-fr", "fr-en")
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

    assert sorted(selected) == ["de-en", "en-de", "en-fr", "fr-en"]
    assert sum(len(rows) for rows in selected.values()) == 4
    assert {row["anchor_id"] for rows in selected.values() for row in rows} == {"en:doc-1"}


def test_jrc_manifest_preserves_anchor_metadata(tmp_path: Path) -> None:
    source_path = tmp_path / "source.jsonl"
    output_dir = tmp_path / "benchmark"
    source_path.write_text(
        json.dumps(
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
            }
        )
        + "\n",
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
            extractors=(),
            verifiers=(),
            refiner=False,
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


def test_refiner_appends_refined_terms_to_manifest_rows() -> None:
    row = {
        "source_language": "German",
        "target_language": "French",
        "_source_text": "Natriumchlorid",
        "_target_text": "chlorure de sodium",
        "terminology": [],
    }
    terminology = BenchmarkTerminologyConfig(
        domain="chemistry",
        extractors=("llm_chemistry",),
        verifiers=(),
        refiner=True,
        refined_max_terms=8,
    )

    rows = attach_terminology_to_rows(
        [row],
        domain="chemistry",
        terminology=terminology,
        runtime=TerminologyRuntime(
            chemistry_generator=_FakeChemistryGenerator(),  # type: ignore[arg-type]
            refiner=_FakeRefiner(),  # type: ignore[arg-type]
        ),
    )

    assert [term["term_group"] for term in rows[0]["terminology"]] == ["llm", "refined"]
    assert refined_terms_from_manifest(rows[0])[0].target_terms == ("chlorure de sodium",)


def test_zero_argument_runner_config_paths() -> None:
    chemistry_globals = runpy.run_path("scripts/generate_chemistry_benchmark.py")
    legal_globals = runpy.run_path("scripts/generate_legal_benchmark.py")

    assert chemistry_globals["CONFIG_PATH"] == Path("config/benchmark_generation/chemistry.toml")
    assert legal_globals["CONFIG_PATH"] == Path("config/benchmark_generation/legal.toml")

