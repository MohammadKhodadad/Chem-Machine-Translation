from __future__ import annotations

from collections.abc import Iterator
from typing import Any, Literal

from datasets import IterableDataset, load_dataset

from chem_machine_translation.schemas import Document
from chem_machine_translation.text import approximate_token_count, normalize_text

DatasetName = Literal["dolma", "chemrxiv"]

DATASET_REPOS: dict[DatasetName, str] = {
    "dolma": "BASF-AI/dolma-chem-only-query-generated",
    "chemrxiv": "BASF-AI/ChemRxiv-Papers",
}

DEFAULT_TEXT_FIELDS: dict[DatasetName, tuple[str, ...]] = {
    "dolma": ("paragraph", "generated_query"),
    "chemrxiv": ("title", "abstract"),
}


def load_streaming_dataset(name: DatasetName, split: str = "train") -> IterableDataset:
    return load_dataset(DATASET_REPOS[name], split=split, streaming=True)


def row_to_document(
    dataset_name: DatasetName,
    row: dict[str, Any],
    text_fields: tuple[str, ...] | None = None,
) -> Document:
    fields = text_fields or DEFAULT_TEXT_FIELDS[dataset_name]
    text_parts = [str(row[field]) for field in fields if row.get(field)]
    text = normalize_text("\n\n".join(text_parts))
    source_id = str(row.get("id") or row.get("doi") or row.get("index") or "unknown")
    metadata = {key: value for key, value in row.items() if key not in fields}

    return Document(
        dataset=dataset_name,
        source_id=source_id,
        text=text,
        metadata=metadata,
    )


def iter_documents(
    dataset_name: DatasetName,
    split: str = "train",
    limit: int = 10,
    skip: int = 0,
    text_fields: tuple[str, ...] | None = None,
    min_input_tokens: int = 192,
    max_input_tokens: int = 256,
    max_rows_scanned: int = 100_000,
) -> Iterator[Document]:
    dataset = load_streaming_dataset(dataset_name, split=split)
    yielded = 0
    scanned = 0

    for row_index, row in enumerate(dataset):
        if row_index < skip:
            continue
        scanned += 1
        if scanned > max_rows_scanned:
            break

        document = row_to_document(dataset_name, row, text_fields)
        token_count = approximate_token_count(document.text)
        if token_count < min_input_tokens or token_count > max_input_tokens:
            continue
        yield document
        yielded += 1
        if yielded >= limit:
            break
