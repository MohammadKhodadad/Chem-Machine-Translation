from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from chem_machine_translation.data.terminology import (
    DatasetTerminologyTerm,
    TargetTerminologyExtractor,
)

SOURCE_TO_CANDIDATE_TYPE = {
    "stanza_ud_dependency": "nominal_dependency_span",
    "stanza_ud_ngram": "content_ngram",
    "stanza_ud_proper_name": "proper_name",
}


@dataclass(frozen=True)
class Candidate:
    surface: str
    start_char: int
    end_char: int
    language: str
    generators: tuple[str, ...]
    candidate_type: str
    score: float
    lemma: str = ""
    upos: tuple[str, ...] = ()
    lookup_forms: tuple[str, ...] = ()


class DeterministicCandidateExtractor:
    """CLI adapter around the production Stanza/UD terminology extractor."""

    def __init__(self) -> None:
        self.extractor = TargetTerminologyExtractor()

    def extract(
        self,
        text: str,
        language: str,
        max_candidates: int | None = None,
    ) -> list[Candidate]:
        max_terms = max_candidates or 50
        terms = self.extractor.extract(
            text=text,
            target_language=language,
            max_terms=max_terms,
        )
        candidates = [
            term_to_candidate(term=term, text=text, language=language)
            for term in terms
            if term.target_terms
        ]
        return candidates[:max_candidates] if max_candidates else candidates


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract deterministic multilingual terminology candidates.",
    )
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--text", help="Text to extract candidates from.")
    input_group.add_argument("--text-file", type=Path, help="UTF-8 text file to extract from.")
    input_group.add_argument("--source-jsonl", type=Path, help="JSONL source rows to extract from.")
    parser.add_argument("--language", help="Language code for --text or --text-file input.")
    parser.add_argument("--text-field", default="target_text")
    parser.add_argument("--language-field", default="target_language")
    parser.add_argument("--id-field", default="example_id")
    parser.add_argument("--limit", type=int, default=None, help="Maximum JSONL rows to process.")
    parser.add_argument("--max-candidates", type=int, default=50)
    parser.add_argument(
        "--download-stanza-models",
        action="store_true",
        help="Download Stanza models for languages present in the selected input.",
    )
    parser.add_argument("--json", action="store_true", help="Write JSON/JSONL instead of Markdown.")
    return parser.parse_args()


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    args = parse_args()
    rows = load_input_rows(args)
    if args.download_stanza_models:
        download_stanza_models(sorted({row["language"] for row in rows}))

    extractor = DeterministicCandidateExtractor()
    outputs = []
    for row in rows:
        candidates = extractor.extract(
            text=row["text"],
            language=row["language"],
            max_candidates=args.max_candidates,
        )
        outputs.append({**row, "candidates": [asdict(candidate) for candidate in candidates]})

    if args.json:
        write_json_output(outputs, from_jsonl=bool(args.source_jsonl))
    else:
        write_markdown_output(outputs)


def load_input_rows(args: argparse.Namespace) -> list[dict[str, str]]:
    if args.text is not None:
        if not args.language:
            raise ValueError("--language is required with --text.")
        return [{"id": "text", "language": args.language, "text": args.text}]

    if args.text_file is not None:
        if not args.language:
            raise ValueError("--language is required with --text-file.")
        return [
            {
                "id": str(args.text_file),
                "language": args.language,
                "text": args.text_file.read_text(encoding="utf-8"),
            },
        ]

    rows = []
    assert args.source_jsonl is not None
    with args.source_jsonl.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if args.limit is not None and len(rows) >= args.limit:
                break
            if not line.strip():
                continue
            raw_row = json.loads(line)
            text = str(raw_row.get(args.text_field) or "")
            language = str(raw_row.get(args.language_field) or "")
            if not text or not language:
                continue
            rows.append(
                {
                    "id": str(raw_row.get(args.id_field) or len(rows)),
                    "language": language,
                    "text": text,
                },
            )
    return rows


def download_stanza_models(languages: list[str]) -> None:
    import stanza

    for language in languages:
        print(f"Downloading Stanza model for {language}...", file=sys.stderr)
        stanza.download(
            language,
            processors="tokenize,pos,lemma,depparse",
            verbose=False,
        )


def term_to_candidate(
    *,
    term: DatasetTerminologyTerm,
    text: str,
    language: str,
) -> Candidate:
    surface = term.target_terms[0]
    start_char, end_char = find_span_offsets(text=text, surface=surface)
    generators = tuple(source for source in term.source.split("+") if source)
    return Candidate(
        surface=surface,
        start_char=start_char,
        end_char=end_char,
        language=language,
        generators=generators or (term.source,),
        candidate_type=SOURCE_TO_CANDIDATE_TYPE.get(term.source, term.source),
        score=term.confidence,
        lookup_forms=lookup_forms_for_candidate(surface),
    )


def find_span_offsets(*, text: str, surface: str) -> tuple[int, int]:
    start_char = text.find(surface)
    if start_char < 0:
        start_char = text.casefold().find(surface.casefold())
    if start_char < 0:
        return -1, -1
    return start_char, start_char + len(surface)


def lookup_forms_for_candidate(surface: str) -> tuple[str, ...]:
    forms = [
        surface,
        surface.casefold(),
        normalize_spacing_and_punctuation(surface),
    ]
    return tuple(dict.fromkeys(form for form in forms if form))


def normalize_spacing_and_punctuation(text: str) -> str:
    text = text.casefold()
    text = text.replace("’", "'").replace("‐", "-").replace("‑", "-").replace("–", "-")
    return re.sub(r"\s+", " ", text).strip()


def write_json_output(outputs: list[dict[str, Any]], *, from_jsonl: bool) -> None:
    if from_jsonl:
        for output in outputs:
            print(json.dumps(output, ensure_ascii=False))
        return
    print(json.dumps(outputs[0], ensure_ascii=False, indent=2))


def write_markdown_output(outputs: list[dict[str, Any]]) -> None:
    for output in outputs:
        print(f"\n## {output['id']} ({output['language']})")
        print()
        text = str(output["text"])
        print(f"Text: {text[:350]}{'...' if len(text) > 350 else ''}")
        print()
        candidates = [Candidate(**candidate) for candidate in output["candidates"]]
        if not candidates:
            print("- no candidates")
            continue
        for candidate in candidates:
            generators = "+".join(candidate.generators)
            offsets = f"{candidate.start_char}:{candidate.end_char}"
            print(
                f"- {candidate.surface} "
                f"[{candidate.candidate_type}; {generators}; {offsets}; "
                f"score={candidate.score:.3f}]",
            )


if __name__ == "__main__":
    main()
