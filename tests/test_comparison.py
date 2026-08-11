import csv
import json

from chem_machine_translation.core.schemas import Document, TranslationResult
from chem_machine_translation.evaluation.comparison import write_csv, write_jsonl


def test_reports_include_terminology_section(tmp_path) -> None:
    document = Document(
        dataset="dolma",
        source_id="1",
        text="The catalyst was stable.",
        metadata={"split": "test"},
    )
    result = TranslationResult(
        document=document,
        source_language="English",
        target_language="German",
        translated_text="Der Katalysator war stabil.",
        strategy="one-shot",
        model="gpt-4.1-mini",
        terminology_section="Approved terminology instructions:\ncatalyst -> Katalysator",
    )

    jsonl_path = tmp_path / "report.jsonl"
    csv_path = tmp_path / "report.csv"

    write_jsonl([result], jsonl_path)
    write_csv([result], csv_path)

    jsonl_row = json.loads(jsonl_path.read_text(encoding="utf-8"))
    assert jsonl_row["terminology_section"] == result.terminology_section

    with csv_path.open(encoding="utf-8", newline="") as handle:
        csv_row = next(csv.DictReader(handle))

    assert csv_row["terminology_section"] == result.terminology_section
