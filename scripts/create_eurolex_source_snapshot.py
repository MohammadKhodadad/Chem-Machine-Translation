from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from chem_machine_translation.data.terminology import build_eurolex_descriptor_terms
from chem_machine_translation.utils.text import approximate_token_count, normalize_text

DEFAULT_LANGUAGES = ["en", "de", "fr", "sk"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create a small tracked EuroLex/MultiEURLEX source snapshot for benchmark builds."
        ),
    )
    parser.add_argument("--source-jsonl", type=Path, default=Path("data/multi_eurlex/train.jsonl"))
    parser.add_argument(
        "--descriptor-json",
        type=Path,
        default=Path("data/multi_eurlex/eurovoc_descriptors.json"),
    )
    parser.add_argument("--output-dir", type=Path, default=Path("benchmark_sources"))
    parser.add_argument("--output-name", default="eurolex_4000.jsonl")
    parser.add_argument("--descriptor-output-name", default="eurovoc_descriptors_subset.json")
    parser.add_argument("--metadata-output-name", default="eurolex_4000_metadata.json")
    parser.add_argument("--limit", type=int, default=4000)
    parser.add_argument("--language", action="append", dest="languages")
    parser.add_argument("--label-level", default="level_1")
    parser.add_argument("--min-input-tokens", type=int, default=32)
    parser.add_argument("--max-input-tokens", type=int, default=1024)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    languages = args.languages or DEFAULT_LANGUAGES
    descriptors = json.loads(args.descriptor_json.read_text(encoding="utf-8"))
    candidates = collect_candidates(
        source_jsonl=args.source_jsonl,
        descriptors=descriptors,
        languages=languages,
        label_level=args.label_level,
        min_input_tokens=args.min_input_tokens,
        max_input_tokens=args.max_input_tokens,
    )
    selected = candidates[: args.limit]

    args.output_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path = args.output_dir / args.output_name
    descriptor_path = args.output_dir / args.descriptor_output_name
    metadata_path = args.output_dir / args.metadata_output_name

    used_descriptors = write_snapshot(snapshot_path=snapshot_path, selected=selected)
    descriptor_path.write_text(
        json.dumps(used_descriptors, ensure_ascii=False, sort_keys=True, indent=2),
        encoding="utf-8",
    )
    metadata = {
        "source_jsonl": str(args.source_jsonl),
        "descriptor_json": str(args.descriptor_json),
        "languages": languages,
        "selected_rows": len(selected),
        "candidate_rows": len(candidates),
        "descriptor_count": len(used_descriptors),
        "selection": (
            "Rows with all selected languages and token counts within bounds, "
            "ranked by exact EuroVoc descriptor matches in selected-language text."
        ),
        "min_input_tokens": args.min_input_tokens,
        "max_input_tokens": args.max_input_tokens,
    }
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(metadata)
    print(
        {
            "snapshot_path": str(snapshot_path),
            "snapshot_size": snapshot_path.stat().st_size,
            "descriptor_path": str(descriptor_path),
            "descriptor_size": descriptor_path.stat().st_size,
        },
    )


def collect_candidates(
    *,
    source_jsonl: Path,
    descriptors: dict[str, Any],
    languages: list[str],
    label_level: str,
    min_input_tokens: int,
    max_input_tokens: int,
) -> list[tuple[int, str, dict[str, Any], dict[str, str], dict[str, Any]]]:
    candidates = []
    with source_jsonl.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            texts = {language: text_for_language(row, language) for language in languages}
            if any(not text for text in texts.values()):
                continue
            lengths = {language: approximate_token_count(text) for language, text in texts.items()}
            if any(
                length < min_input_tokens or length > max_input_tokens
                for length in lengths.values()
            ):
                continue
            row_descriptors = descriptors_for_row(row, descriptors, label_level)
            term_score = descriptor_match_count(
                descriptors_by_concept_id=row_descriptors,
                texts=texts,
            )
            candidates.append(
                (term_score, str(row.get("celex_id") or ""), row, texts, row_descriptors),
            )

    candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return candidates


def text_for_language(row: dict[str, Any], language: str) -> str:
    text = row.get("text", {}).get(language)
    if text is None and language != "en":
        text = row.get("text", {}).get(f"en2{language}")
    return normalize_text(str(text or ""))


def descriptors_for_row(
    row: dict[str, Any],
    descriptors: dict[str, Any],
    label_level: str,
) -> dict[str, Any]:
    label_ids = row.get("eurovoc_concepts", {}).get(label_level, row.get("labels", []))
    return {
        descriptor_id: descriptors[descriptor_id]
        for descriptor_id in map(str, label_ids)
        if descriptor_id in descriptors
    }


def descriptor_match_count(
    *,
    descriptors_by_concept_id: dict[str, Any],
    texts: dict[str, str],
) -> int:
    return sum(
        len(
            build_eurolex_descriptor_terms(
                descriptors_by_concept_id=descriptors_by_concept_id,
                target_language_code=language,
                target_text=text,
            ),
        )
        for language, text in texts.items()
    )


def write_snapshot(
    *,
    snapshot_path: Path,
    selected: list[tuple[int, str, dict[str, Any], dict[str, str], dict[str, Any]]],
) -> dict[str, Any]:
    used_descriptors: dict[str, Any] = {}
    with snapshot_path.open("w", encoding="utf-8") as handle:
        for _, _, row, texts, row_descriptors in selected:
            used_descriptors.update(row_descriptors)
            output = {
                "celex_id": row.get("celex_id"),
                "publication_date": row.get("publication_date"),
                "eurovoc_concepts": row.get("eurovoc_concepts", {}),
                "text": texts,
            }
            handle.write(json.dumps(output, ensure_ascii=False) + "\n")
    return used_descriptors


if __name__ == "__main__":
    main()
