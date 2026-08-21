import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from chem_machine_translation.data.terminology import make_target_term

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "build_jrc_acquis_eval_subset.py"
SPEC = importlib.util.spec_from_file_location("build_jrc_acquis_eval_subset", SCRIPT_PATH)
assert SPEC and SPEC.loader
dataset_builder = importlib.util.module_from_spec(SPEC)
sys.modules["build_jrc_acquis_eval_subset"] = dataset_builder
SPEC.loader.exec_module(dataset_builder)


class CountingGenerator:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def generate(
        self,
        source_text: str,
        target_language: str,
        reference_text: str,
    ) -> list[Any]:
        del source_text
        self.calls.append((target_language, reference_text))
        return [
            make_target_term(
                target_term=f"{target_language} term",
                category="other",
                source="test",
                confidence=1.0,
            )
        ]


def _manifest_row(
    *,
    chunk_id: str,
    target_language: str,
    target_language_code: str,
    target_text: str,
) -> dict[str, Any]:
    return {
        "chunk_id": chunk_id,
        "target_language": target_language,
        "target_language_code": target_language_code,
        "_source_text": f"source for {chunk_id}",
        "_target_text": target_text,
        "terminology": [],
    }


def test_add_stanza_terms_reuses_terms_for_same_target_language_and_text() -> None:
    generator = CountingGenerator()
    term_cache: dict[tuple[str, str], list[dict[str, Any]]] = {}
    rows = [
        _manifest_row(
            chunk_id="de-en:doc-a:chunk-0001",
            target_language="English",
            target_language_code="en",
            target_text="The same English target chunk.",
        ),
        _manifest_row(
            chunk_id="fr-en:doc-a:chunk-0001",
            target_language="English",
            target_language_code="en",
            target_text="The same English target chunk.",
        ),
        _manifest_row(
            chunk_id="en-de:doc-a:chunk-0001",
            target_language="German",
            target_language_code="de",
            target_text="The same surface text but different language.",
        ),
    ]

    updated_rows = dataset_builder.add_stanza_terms(
        rows=rows,
        generator=generator,
        term_cache=term_cache,
    )

    assert generator.calls == [
        ("English", "The same English target chunk."),
        ("German", "The same surface text but different language."),
    ]
    assert len(term_cache) == 2
    assert [row["terminology"][0]["target_terms"][0] for row in updated_rows] == [
        "English term",
        "English term",
        "German term",
    ]


def test_collect_stanza_term_jobs_keeps_only_uncached_unique_targets() -> None:
    rows = [
        _manifest_row(
            chunk_id="de-en:doc-a:chunk-0001",
            target_language="English",
            target_language_code="en",
            target_text="The same English target chunk.",
        ),
        _manifest_row(
            chunk_id="fr-en:doc-a:chunk-0001",
            target_language="English",
            target_language_code="en",
            target_text="The same English target chunk.",
        ),
        _manifest_row(
            chunk_id="en-de:doc-a:chunk-0001",
            target_language="German",
            target_language_code="de",
            target_text="The same German target chunk.",
        ),
    ]
    term_cache = {
        ("de", "The same German target chunk."): [
            make_target_term(
                target_term="German cached term",
                category="other",
                source="test",
                confidence=1.0,
            ).to_json()
        ]
    }
    config = dataset_builder.StanzaTerminologyConfig(max_terms=10)

    jobs = dataset_builder.collect_stanza_term_jobs(
        rows=rows,
        term_cache=term_cache,
        config=config,
    )

    assert len(jobs) == 1
    assert jobs[0].cache_key == ("en", "The same English target chunk.")
    assert jobs[0].target_language == "English"


def test_build_stanza_config_includes_optional_extractors() -> None:
    args = SimpleNamespace(
        extract_stanza_terms=True,
        stanza_terminology_max_terms=10,
        use_stanza_extractor=False,
        use_nobi_extractor=True,
        nobi_model="test-nobi",
        use_nltk_extractor=True,
        use_spacy_extractor=True,
        spacy_model="test-spacy",
        use_msplade_extractor=True,
        msplade_model="test-msplade",
        iate_terminology=False,
        wikipedia_terminology=False,
        pubchem_terminology=False,
        chebi_terminology=False,
        chembl_terminology=False,
        mesh_terminology=False,
        nci_terminology=False,
        agrovoc_terminology=False,
        unterm_terminology=False,
    )

    config = dataset_builder.build_stanza_config(args)

    assert config is not None
    assert config.use_stanza_extractor is False
    assert config.use_nobi_extractor is True
    assert config.use_nltk_extractor is True
    assert config.use_spacy_extractor is True
    assert config.spacy_model == "test-spacy"
    assert config.use_msplade_extractor is True
    assert config.msplade_model == "test-msplade"


def test_generate_stanza_terms_for_job_passes_spacy_config() -> None:
    job = dataset_builder.StanzaTerminologyJob(
        cache_key=("en", "The controlled substances include carbon tetrachloride."),
        source_text="Ignored.",
        target_language="English",
        target_text="The controlled substances include carbon tetrachloride.",
        config=dataset_builder.StanzaTerminologyConfig(
            max_terms=10,
            use_stanza_extractor=False,
            use_spacy_extractor=True,
        ),
    )

    _, terms = dataset_builder.generate_stanza_terms_for_job(job)

    target_terms = [term["target_terms"][0] for term in terms]
    assert "carbon tetrachloride" in target_terms
    assert all(term["source"].startswith("spacy_") for term in terms)
