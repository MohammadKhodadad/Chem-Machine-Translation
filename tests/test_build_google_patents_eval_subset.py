import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "build_google_patents_eval_subset.py"
)
SPEC = importlib.util.spec_from_file_location("build_google_patents_eval_subset", SCRIPT_PATH)
assert SPEC and SPEC.loader
dataset_builder = importlib.util.module_from_spec(SPEC)
sys.modules["build_google_patents_eval_subset"] = dataset_builder
SPEC.loader.exec_module(dataset_builder)


def test_add_bidirectional_pair_rows_adds_reversed_rows() -> None:
    row = {
        "example_id": "example-1",
        "doc_id": "doc-1",
        "language_pair": "en-de",
        "source_language": "en",
        "target_language": "de",
        "source_text": "English chemistry abstract.",
        "target_text": "Deutscher Chemieabstract.",
        "selection_rule": "same document",
    }

    pair_rows = dataset_builder.add_bidirectional_pair_rows({"en-de": [row]})

    assert sorted(pair_rows) == ["de-en", "en-de"]
    reversed_row = pair_rows["de-en"][0]
    assert reversed_row["example_id"] == "example-1:reverse"
    assert reversed_row["source_language"] == "de"
    assert reversed_row["target_language"] == "en"
    assert reversed_row["source_text"] == "Deutscher Chemieabstract."
    assert reversed_row["target_text"] == "English chemistry abstract."


def test_build_generator_includes_spacy_without_llm_client() -> None:
    args = SimpleNamespace(
        extract_terminology=False,
        terminology_model="gpt-test",
        terminology_max_terms=10,
        use_stanza_extractor=False,
        use_nobi_extractor=False,
        nobi_model="test-nobi",
        use_nltk_extractor=False,
        use_spacy_extractor=True,
        spacy_model="",
        use_msplade_extractor=False,
        msplade_model="test-msplade",
        iate_terminology=False,
        wikidata_terminology=False,
        wikipedia_terminology=False,
        pubchem_terminology=False,
        chebi_terminology=False,
        chembl_terminology=False,
        mesh_terminology=False,
        nci_terminology=False,
        agrovoc_terminology=False,
        terminology_cache=None,
    )

    generator = dataset_builder.build_generator(args)

    assert generator is not None
    assert generator.extractor_names == ("SpaCyTerminologyExtractor",)
