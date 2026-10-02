from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = (
    PROJECT_ROOT / "benchmark_datasets" / "google_patents_judged_exact_high_glm_flash_local"
)
OUTPUT_PATH = (
    PROJECT_ROOT / "benchmark_sources" / "google_patents_within_document_pairs_judged_exact_high.jsonl"
)
METADATA_PATH = OUTPUT_PATH.with_name(
    "google_patents_within_document_pairs_judged_exact_high_metadata.json"
)
SELECTION_RULE = (
    "Reconstructed from paired source.csv and target.csv files in the judged-exact-high "
    "GLM Flash dataset; deterministic direction and source CSV order"
)


def main() -> None:
    rows: list[dict[str, object]] = []
    direction_counts: Counter[str] = Counter()

    for direction_dir in sorted(path for path in DATASET_DIR.iterdir() if path.is_dir()):
        direction = direction_dir.name
        source_rows = read_csv_rows(direction_dir / "source.csv")
        target_rows = {
            row["id"]: row
            for row in read_csv_rows(direction_dir / "target.csv")
        }
        manifest_rows = {
            row["source_id"]: row
            for row in read_jsonl_rows(next(direction_dir.glob("*-manifest.jsonl")))
        }

        if len(source_rows) != len(target_rows) or len(source_rows) != len(manifest_rows):
            raise ValueError(f"Mismatched row counts in {direction}")

        for source_row in source_rows:
            source_row_id = source_row["id"]
            if not source_row_id.endswith("_source"):
                raise ValueError(f"Unexpected source row ID: {source_row_id}")
            example_id = source_row_id.removesuffix("_source")
            target_row = target_rows.get(f"{example_id}_target")
            manifest_row = manifest_rows.get(example_id)
            if target_row is None or manifest_row is None:
                raise ValueError(f"Missing pair or manifest row for {example_id}")
            if manifest_row["direction"] != direction:
                raise ValueError(f"Direction mismatch for {example_id}")

            rows.append(
                {
                    "corpus_id": manifest_row["corpus_id"],
                    "doc_id": source_row["doc_id"],
                    "example_id": example_id,
                    "field": manifest_row["field"],
                    "group_key": manifest_row["family_id"],
                    "language_pair": direction,
                    "pub_date": manifest_row["publication_date"],
                    "selection_rule": SELECTION_RULE,
                    "source": manifest_row["country_code"],
                    "source_char_count": len(source_row["context"]),
                    "source_language": source_row["language"],
                    "source_text": source_row["context"],
                    "target_char_count": len(target_row["context"]),
                    "target_language": target_row["language"],
                    "target_text": target_row["context"],
                }
            )
            direction_counts[direction] += 1

    write_jsonl(OUTPUT_PATH, rows)
    METADATA_PATH.write_text(
        json.dumps(
            {
                "dataset": "google_patents",
                "source_dataset_dir": str(DATASET_DIR.relative_to(PROJECT_ROOT)),
                "selection_rule": SELECTION_RULE,
                "row_count": len(rows),
                "direction_count": len(direction_counts),
                "direction_counts": dict(sorted(direction_counts.items())),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(rows)} rows across {len(direction_counts)} directions to {OUTPUT_PATH}")


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def read_jsonl_rows(path: Path) -> list[dict[str, object]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()