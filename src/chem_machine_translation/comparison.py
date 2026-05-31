from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from pathlib import Path

from chem_machine_translation.schemas import TranslationResult
from chem_machine_translation.text import approximate_token_count

REPORT_COLUMNS = [
    "dataset",
    "source_id",
    "source_language",
    "target_language",
    "strategy",
    "model",
    "approved",
    "review_rounds",
    "approx_source_tokens",
    "source_text",
    "translated_text",
    "review_notes_json",
    "metadata_json",
]


def write_jsonl(results: list[TranslationResult], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for result in results:
            handle.write(
                json.dumps(
                    {
                        "dataset": result.document.dataset,
                        "source_id": result.document.source_id,
                        "source_language": result.source_language,
                        "target_language": result.target_language,
                        "strategy": result.strategy,
                        "model": result.model,
                        "approved": result.approved,
                        "review_rounds": result.review_rounds,
                        "review_notes": result.review_notes,
                        "approx_source_tokens": approximate_token_count(result.document.text),
                        "source_text": result.document.text,
                        "translated_text": result.translated_text,
                        "metadata": result.document.metadata,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )


def write_csv(results: list[TranslationResult], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REPORT_COLUMNS)
        writer.writeheader()
        for result in results:
            writer.writerow(
                {
                    "dataset": result.document.dataset,
                    "source_id": result.document.source_id,
                    "source_language": result.source_language,
                    "target_language": result.target_language,
                    "strategy": result.strategy,
                    "model": result.model or "",
                    "approved": result.approved if result.approved is not None else "",
                    "review_rounds": result.review_rounds,
                    "approx_source_tokens": approximate_token_count(result.document.text),
                    "source_text": result.document.text,
                    "translated_text": result.translated_text,
                    "review_notes_json": json.dumps(result.review_notes, ensure_ascii=False),
                    "metadata_json": json.dumps(result.document.metadata, ensure_ascii=False),
                }
            )


def timestamped_report_path(reports_dir: Path, suffix: str) -> Path:
    timestamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    return reports_dir / f"translation-sample-{timestamp}.{suffix}"
