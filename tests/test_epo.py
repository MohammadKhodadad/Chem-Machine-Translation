import csv
from pathlib import Path

from chem_machine_translation.data.epo import (
    iter_epo_translation_documents,
    normalize_language_code,
)
from chem_machine_translation.utils.text import normalize_text


def _write_epo_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = [
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
        "ipc_codes",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_epo_language_code_maps_target_languages() -> None:
    assert normalize_language_code("German") == "de"
    assert normalize_language_code("French") == "fr"
    assert normalize_language_code("de") == "de"


def test_iter_epo_translation_documents_loads_aligned_context(tmp_path: Path) -> None:
    source_context = "Title: Solid electrolyte battery\n\nFirst claim: " + " ".join(
        ["solid electrolyte separator"] * 50
    )
    target_context = "Title: Festelektrolytbatterie\n\nFirst claim: " + " ".join(
        ["Festelektrolyt Separator"] * 50
    )
    common = {
        "abstract": "",
        "description": "",
        "first_claim": "claim",
        "publication_number": "3686982",
        "country_code": "EP",
        "publication_date": "20260527",
        "source": "epo",
        "ipc_codes": "H01M 10/0565|H01M 10/0562",
    }
    _write_epo_csv(
        tmp_path / "en.csv",
        [
            {
                **common,
                "id": "3686982_en",
                "language": "en",
                "title": "Solid electrolyte battery",
                "context": source_context,
            }
        ],
    )
    _write_epo_csv(
        tmp_path / "de.csv",
        [
            {
                **common,
                "id": "3686982_de",
                "language": "de",
                "title": "Festelektrolytbatterie",
                "context": target_context,
            }
        ],
    )

    documents = list(
        iter_epo_translation_documents(
            data_dir=tmp_path,
            target_language="German",
            limit=1,
            min_input_tokens=10,
            max_input_tokens=500,
        )
    )

    assert len(documents) == 1
    assert documents[0].dataset == "epo"
    assert documents[0].source_id == "3686982"
    assert documents[0].ground_truth == normalize_text(target_context)
    assert documents[0].metadata["target_language_code"] == "de"
    assert documents[0].metadata["ipc_codes"] == "H01M 10/0565|H01M 10/0562"
