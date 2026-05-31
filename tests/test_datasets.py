from chem_machine_translation.datasets import iter_documents, row_to_document


def test_dolma_row_to_document_uses_paragraph_and_query() -> None:
    row = {
        "id": "paper-1",
        "paragraph": "CO2 reacts with epichlorohydrin under pressure.",
        "generated_query": "What catalyst was used?",
        "index": 3,
    }

    document = row_to_document("dolma", row)

    assert document.dataset == "dolma"
    assert document.source_id == "paper-1"
    assert "CO2 reacts" in document.text
    assert "What catalyst" in document.text
    assert document.metadata == {"id": "paper-1", "index": 3}


def test_chemrxiv_row_to_document_uses_title_and_abstract() -> None:
    row = {
        "id": "abc",
        "doi": "10.26434/example",
        "title": "Photocatalytic C-H Amination",
        "abstract": "A visible-light method is reported.",
        "authors": "A. Chemist",
    }

    document = row_to_document("chemrxiv", row)

    assert document.dataset == "chemrxiv"
    assert document.source_id == "abc"
    assert document.text.startswith("Photocatalytic C-H Amination")
    assert document.metadata["doi"] == "10.26434/example"


def test_iter_documents_filters_to_token_range(monkeypatch) -> None:
    rows = [
        {"id": "too-short", "paragraph": "short text", "generated_query": ""},
        {"id": "match", "paragraph": " ".join(["token"] * 200), "generated_query": ""},
        {"id": "too-long", "paragraph": " ".join(["token"] * 300), "generated_query": ""},
    ]

    monkeypatch.setattr(
        "chem_machine_translation.datasets.load_streaming_dataset",
        lambda dataset_name, split: rows,
    )

    documents = list(
        iter_documents(
            dataset_name="dolma",
            min_input_tokens=192,
            max_input_tokens=256,
            limit=10,
        )
    )

    assert [document.source_id for document in documents] == ["match"]
