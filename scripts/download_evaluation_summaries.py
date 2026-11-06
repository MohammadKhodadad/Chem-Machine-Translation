from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

SOURCE_FOLDERS = {
    ("original_glm", "all_terms"): "1M8UdpWpL2heLEdcRXJ2AuK_0KmDu3J4g",
    ("original_glm", "externally_verified"): "1K56pWHMIhwPyr88p0VN3VTf3xp-7N9uQ",
    ("original_glm", "llm_enriched"): "1cIatPRGnj77koWnMQodCUtDR8NFugj5o",
    ("luna", "all_terms"): "1QoJzY--vDVxAooJrOk36sNbSGfusNj5i",
    ("luna", "externally_verified"): "1EMQQUesGvayRFuvgB-4B35SOUiKlqaa3",
    ("luna", "llm_enriched"): "1VUmQ2XUizwagQyPI0rdyLp7tpCB2dMJ4",
}
VOID_TAGS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}


class DriveRows(HTMLParser):
    def __init__(self):
        super().__init__()
        self.depth = 0
        self.current = None
        self.rows = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if attributes.get("role") == "row" and self.current is None:
            self.current = {"id": attributes.get("data-id"), "text": []}
            self.depth = 1
        elif self.current is not None and tag not in VOID_TAGS:
            self.depth += 1

    def handle_endtag(self, tag):
        if self.current is not None and tag not in VOID_TAGS:
            self.depth -= 1
            if self.depth == 0:
                if self.current["id"]:
                    self.rows.append(self.current)
                self.current = None

    def handle_data(self, data):
        if self.current is not None and data.strip():
            self.current["text"].append(data.strip())


def list_folder(session, identifier):
    with session.get(
        f"https://drive.google.com/drive/folders/{identifier}", timeout=(20, 90)
    ) as response:
        response.raise_for_status()
        parser = DriveRows()
        parser.feed(response.text)
    if not parser.rows or len(parser.rows) >= 50:
        raise RuntimeError(f"Empty or potentially truncated Drive listing: {identifier}")
    return parser.rows


def validate_summary(payload, run):
    summary = json.loads(payload)
    if summary.get("run") != run or not summary.get("dataset_settings"):
        raise ValueError(f"Unexpected summary identity or missing scores: {run}")
    for settings in summary["dataset_settings"].values():
        for result in settings.values():
            if not isinstance(result.get("by_direction"), dict):
                raise ValueError(f"Missing direction-level results: {run}")
    return summary


def download_translation_timing_summaries(root):
    manifest = json.loads((root / "download_manifest.json").read_text(encoding="utf-8"))
    runs = {
        entry["run"]
        for entry in manifest["files"]
        if "__historical_untimed" not in entry["run"] and "__native_sample" not in entry["run"]
    }
    entries = []
    with requests.Session() as session:
        folders = list_folder(session, "1FMj3M8ikv2h0CMmZMkIBUJqxd4gjGwg9")
        selected = {row["text"][0]: row for row in folders if row["text"][0] in runs}
        if set(selected) != runs:
            raise ValueError("Missing current-model translation input folders")
        for run in sorted(runs):
            files = list_folder(session, selected[run]["id"])
            matches = [row for row in files if "summary.json" in row["text"]]
            if len(matches) != 1:
                raise ValueError(f"Expected one original translation summary: {run}")
            identifier = matches[0]["id"]
            relative = Path("translation_timing") / run / "summary.json"
            destination = root / relative
            if destination.exists():
                payload = destination.read_bytes()
            else:
                response = session.get(
                    "https://drive.google.com/uc",
                    params={"export": "download", "id": identifier},
                    timeout=(20, 90),
                )
                response.raise_for_status()
                payload = response.content
            document = json.loads(payload)
            if not isinstance(document.get("datasets"), dict):
                raise ValueError(f"Missing translation dataset aggregates: {run}")
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(payload)
            entries.append(
                {
                    "run": run,
                    "path": relative.as_posix(),
                    "bytes": len(payload),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                    "source_url": f"https://drive.google.com/file/d/{identifier}/view",
                }
            )
            print(f"[{len(entries)}/{len(runs)}] Translation summary: {run}", flush=True)
    timing_manifest = {
        "scope": "Original translation summary aggregates only; no raw translations or scores.",
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_folder_url": "https://drive.google.com/drive/folders/1FMj3M8ikv2h0CMmZMkIBUJqxd4gjGwg9",
        "complete": len(entries) == len(runs),
        "files": entries,
    }
    (root / "translation_timing_manifest.json").write_text(
        json.dumps(timing_manifest, indent=2) + "\n", encoding="utf-8"
    )


def main():
    parser = argparse.ArgumentParser(description="Download grouped performance summaries only.")
    parser.add_argument("--output", type=Path, default=Path("reports/evaluation-e452b88"))
    parser.add_argument("--limit", type=int, help="Limit downloads for a focused smoke check.")
    parser.add_argument(
        "--translation-timing",
        action="store_true",
        help="Download original translation summary aggregates for timing analysis.",
    )
    args = parser.parse_args()
    if args.translation_timing:
        download_translation_timing_summaries(args.output)
        return
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be positive")
    session = requests.Session()
    session.mount(
        "https://",
        HTTPAdapter(
            max_retries=Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        ),
    )
    entries = []
    expected_runs = None
    stop = False
    for (view, category), identifier in SOURCE_FOLDERS.items():
        runs = list_folder(session, identifier)
        names = {row["text"][0] for row in runs}
        if len(runs) != 14 or len(names) != 14:
            raise RuntimeError(f"Expected 14 distinct runs in {view}/{category}, found {len(runs)}")
        if expected_runs is None:
            expected_runs = names
        elif names != expected_runs:
            raise RuntimeError(f"Run populations differ in {view}/{category}")
        for row in runs:
            run = row["text"][0]
            if Path(run).name != run or run in {".", ".."}:
                raise ValueError(f"Unsafe run directory: {run}")
            files = list_folder(session, row["id"])
            matches = [item for item in files if "summary.json" in item["text"]]
            if len(matches) != 1:
                raise RuntimeError(f"Expected one summary in {view}/{category}/{run}")
            file_id = matches[0]["id"]
            relative = Path(view) / category / run / "summary.json"
            destination = args.output / relative
            if destination.exists():
                payload = destination.read_bytes()
            else:
                with session.get(
                    "https://drive.google.com/uc",
                    params={"export": "download", "id": file_id},
                    timeout=(20, 120),
                ) as response:
                    response.raise_for_status()
                    payload = response.content
                validate_summary(payload, run)
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(payload)
            summary = validate_summary(payload, run)
            entries.append(
                {
                    "terminology_view": view,
                    "category": category,
                    "run": run,
                    "path": relative.as_posix(),
                    "drive_file_id": file_id,
                    "source_url": f"https://drive.google.com/file/d/{file_id}/view",
                    "sha256": hashlib.sha256(payload).hexdigest(),
                    "bytes": len(payload),
                    "datasets": sorted(summary["dataset_settings"]),
                }
            )
            print(f"[{len(entries)}/84] {relative.as_posix()} ({len(payload):,} bytes)", flush=True)
            if args.limit is not None and len(entries) >= args.limit:
                stop = True
                break
        if stop:
            break
    session.close()
    complete = len(entries) == 84
    manifest = {
        "source_folder_url": "https://drive.google.com/drive/folders/1AdqKt8Qr8riI3J1fzpX1uCrZlpl2EnHZ",
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Grouped performance summaries; no per-translation scores, logs, caches, "
        "or runtime artifacts.",
        "expected_summary_files": 84,
        "downloaded_summary_files": len(entries),
        "complete": complete,
        "files": entries,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    manifest_name = "download_manifest.json" if complete else "download_manifest.partial.json"
    (args.output / manifest_name).write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    if complete:
        (args.output / "download_manifest.partial.json").unlink(missing_ok=True)
    print(
        f"Downloaded {len(entries)} summaries, "
        f"{sum(item['bytes'] for item in entries):,} bytes. Complete: {complete}"
    )


if __name__ == "__main__":
    main()
