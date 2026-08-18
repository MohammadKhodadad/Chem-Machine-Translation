import importlib.util
import sys
from pathlib import Path
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
