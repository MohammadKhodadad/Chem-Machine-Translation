import csv
from pathlib import Path

from chem_machine_translation.google_patents import (
    iter_google_patent_translation_documents,
    normalize_language_code,
)

FIELDNAMES = [
    "id",
    "language",
    "title",
    "abstract",
    "description",
    "first_claim",
    "context",
    "publication_number",
    "country_code",
    "publication_date",
    "source",
]


def write_patent_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def test_iter_google_patent_translation_documents_aligns_ground_truth(tmp_path) -> None:
    source_context = " ".join(["source"] * 200)
    target_context = " ".join(["target"] * 200)
    write_patent_csv(
        tmp_path / "en.csv",
        [
            {
                "id": "EP-1_en",
                "language": "en",
                "context": source_context,
                "publication_number": "EP-1",
            }
        ],
    )
    write_patent_csv(
        tmp_path / "fr.csv",
        [
            {
                "id": "EP-1_fr",
                "language": "fr",
                "context": target_context,
                "publication_number": "EP-1",
            }
        ],
    )

    documents = list(
        iter_google_patent_translation_documents(
            data_dir=tmp_path,
            target_language="French",
            limit=10,
        )
    )

    assert len(documents) == 1
    assert documents[0].source_id == "EP-1"
    assert documents[0].text == source_context
    assert documents[0].ground_truth == target_context
    assert documents[0].metadata["target_language_code"] == "fr"


def test_normalize_language_code_supports_dutch() -> None:
    assert normalize_language_code("Dutch") == "nl"
    assert normalize_language_code("nl") == "nl"
