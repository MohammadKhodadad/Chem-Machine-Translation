from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

UD_HEAD_UPOS = {"NOUN", "PROPN", "NUM", "SYM", "X"}
UD_CONTENT_UPOS = {"ADJ", "NOUN", "NUM", "PROPN", "SYM", "X"}
UD_EXPANSION_DEPRELS = {
    "amod",
    "appos",
    "case",
    "compound",
    "fixed",
    "flat",
    "nmod",
    "nummod",
}
UD_BLOCKED_BOUNDARY_UPOS = {"ADP", "AUX", "CCONJ", "DET", "PART", "PRON", "SCONJ"}
SPAN_SEPARATOR_RE = re.compile(r"[,;:]")
LEGAL_CITATION_RE = re.compile(
    r"\b(?:articles?|artikels?|articulos?|artículos?|artigos?|paragraphs?|"
    r"paragraphes?|absatz|absätze|apartados?|sections?)\s+\d+\b|"
    r"\b\d+\s+(?:of|de|del|des|do|du|von)\s+"
    r"(?:this|the|present|cet|cette|dies(?:es|em|er)?|el|la|le|o)?\s*"
    r"(?:articles?|artikels?|articulos?|artículos?|artigos?|paragraphs?|"
    r"paragraphes?|absatz|absätze|apartados?)\b",
    re.IGNORECASE,
)
DATE_FRAGMENT_RE = re.compile(
    r"\b(?:from|of|de|del|des|do|du|von|vom)\s+\d{1,2}\b|"
    r"\b\d{1,2}\.?\s+"
    r"(?:january|february|march|april|may|june|july|august|september|october|"
    r"november|december|janvier|fevrier|février|mars|avril|mai|juin|juillet|"
    r"aout|août|septembre|octobre|novembre|decembre|décembre|januar|februar|"
    r"marz|märz|april|mai|juni|juli|august|september|oktober|november|dezember|"
    r"enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|"
    r"noviembre|diciembre|janeiro|fevereiro|marco|março|abril|maio|junho|"
    r"julho|agosto|setembro|outubro|novembro|dezembro)\b|"
    r"\b(?:19|20)\d{2}\b",
    re.IGNORECASE,
)
MONTH_NAME_RE = re.compile(
    r"^(?:january|february|march|april|may|june|july|august|september|october|"
    r"november|december|janvier|fevrier|février|mars|avril|mai|juin|juillet|"
    r"aout|août|septembre|octobre|novembre|decembre|décembre|januar|februar|"
    r"marz|märz|april|mai|juni|juli|august|september|oktober|november|dezember|"
    r"enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|"
    r"noviembre|diciembre|janeiro|fevereiro|marco|março|abril|maio|junho|"
    r"julho|agosto|setembro|outubro|novembro|dezembro)$",
    re.IGNORECASE,
)
MAX_STANZA_TERM_TOKENS = 6


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
    """High-recall multilingual candidate extraction from Universal Dependencies."""

    def __init__(self) -> None:
        self._stanza_pipelines: dict[str, Any] = {}

    def extract(
        self,
        text: str,
        language: str,
        max_candidates: int | None = None,
    ) -> list[Candidate]:
        candidates = [
            *self.stanza_ud_dependency_candidates(text=text, language=language),
            *self.stanza_relaxed_ngram_candidates(text=text, language=language),
            *self.stanza_proper_name_candidates(text=text, language=language),
        ]
        merged = self.merge_candidate_generators(candidates)
        sorted_candidates = sorted(
            merged,
            key=lambda candidate: (
                candidate.start_char,
                -(candidate.end_char - candidate.start_char),
                candidate.surface.casefold(),
            ),
        )
        return sorted_candidates[:max_candidates] if max_candidates else sorted_candidates

    def stanza_ud_dependency_candidates(self, *, text: str, language: str) -> list[Candidate]:
        doc = self.parse_with_stanza(text=text, language=language)
        if doc is None:
            return []

        candidates = []
        for sentence in doc.sentences:
            words = list(sentence.words)
            for head in words:
                if head.upos not in UD_HEAD_UPOS:
                    continue
                span_words = dependency_span_words(head, words)
                candidates.extend(
                    stanza_span_candidates(
                        text=text,
                        words=span_words,
                        language=language,
                        generator="ud_dependency",
                        candidate_type="nominal_dependency_span",
                    ),
                )
        return candidates

    def stanza_relaxed_ngram_candidates(self, *, text: str, language: str) -> list[Candidate]:
        doc = self.parse_with_stanza(text=text, language=language)
        if doc is None:
            return []

        candidates = []
        for sentence in doc.sentences:
            words = list(sentence.words)
            for size in range(1, 7):
                for index in range(0, max(len(words) - size + 1, 0)):
                    span_words = words[index : index + size]
                    if not stanza_ngram_is_plausible(span_words):
                        continue
                    candidates.extend(
                        stanza_span_candidates(
                            text=text,
                            words=span_words,
                            language=language,
                            generator="stanza_relaxed_ngram",
                            candidate_type="content_ngram",
                        ),
                    )
        return candidates

    def stanza_proper_name_candidates(self, *, text: str, language: str) -> list[Candidate]:
        doc = self.parse_with_stanza(text=text, language=language)
        if doc is None:
            return []

        candidates = []
        for sentence in doc.sentences:
            current = []
            for word in sentence.words:
                if word.upos == "PROPN":
                    current.append(word)
                    continue
                candidates.extend(proper_name_sequence(text, current, language))
                current = []
            candidates.extend(proper_name_sequence(text, current, language))
        return candidates

    def parse_with_stanza(self, *, text: str, language: str) -> object | None:
        try:
            import stanza
        except ImportError:
            return None

        try:
            if language not in self._stanza_pipelines:
                self._stanza_pipelines[language] = stanza.Pipeline(
                    lang=language,
                    processors="tokenize,pos,lemma,depparse",
                    verbose=False,
                )
            return self._stanza_pipelines[language](text)
        except Exception:
            return None

    def merge_candidate_generators(self, candidates: list[Candidate]) -> list[Candidate]:
        by_key: dict[tuple[int, int, str], Candidate] = {}
        generators_by_key: defaultdict[tuple[int, int, str], set[str]] = defaultdict(set)
        for candidate in candidates:
            key = (candidate.start_char, candidate.end_char, normalize_key(candidate.surface))
            by_key.setdefault(key, candidate)
            generators_by_key[key].update(candidate.generators)

        merged = []
        for key, candidate in by_key.items():
            merged.append(
                Candidate(
                    surface=candidate.surface,
                    start_char=candidate.start_char,
                    end_char=candidate.end_char,
                    language=candidate.language,
                    generators=tuple(sorted(generators_by_key[key])),
                    candidate_type=candidate.candidate_type,
                    score=candidate.score,
                    lemma=candidate.lemma,
                    upos=candidate.upos,
                    lookup_forms=candidate.lookup_forms,
                ),
            )
        return merged


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


def dependency_span_words(head: object, words: list[object]) -> list[object]:
    selected = [head]
    for word in words:
        if word.head == head.id and dependency_relation(word.deprel) in UD_EXPANSION_DEPRELS:
            selected.append(word)
            selected.extend(
                child
                for child in words
                if child.head == word.id
                and dependency_relation(child.deprel) in UD_EXPANSION_DEPRELS
            )
    return sorted({word.id: word for word in selected}.values(), key=lambda word: word.id)


def dependency_relation(deprel: str) -> str:
    return deprel.split(":", 1)[0]


def stanza_span_candidates(
    *,
    text: str,
    words: list[object],
    language: str,
    generator: str,
    candidate_type: str,
) -> list[Candidate]:
    if not words:
        return []
    words = sorted(words, key=lambda word: word.id)
    if len(words) > MAX_STANZA_TERM_TOKENS:
        return []
    if words[0].upos in UD_BLOCKED_BOUNDARY_UPOS or words[-1].upos in UD_BLOCKED_BOUNDARY_UPOS:
        return []
    start_char = min(word.start_char for word in words if word.start_char is not None)
    end_char = max(word.end_char for word in words if word.end_char is not None)
    surface = clean_span(text[start_char:end_char])
    if not surface:
        return []
    if not stanza_candidate_surface_is_clean(surface):
        return []
    lemma = " ".join(word.lemma or word.text for word in words)
    return [
        make_candidate(
            surface=surface,
            start_char=start_char,
            end_char=end_char,
            language=language,
            generator=generator,
            candidate_type=candidate_type,
            score=stanza_candidate_score(words),
            lemma=lemma,
            upos=tuple(word.upos for word in words),
        ),
    ]


def stanza_ngram_is_plausible(words: list[object]) -> bool:
    if not words:
        return False
    if words[0].upos in UD_BLOCKED_BOUNDARY_UPOS or words[-1].upos in UD_BLOCKED_BOUNDARY_UPOS:
        return False
    if any(word.upos in {"CCONJ", "SCONJ"} for word in words):
        return False
    if any(dependency_relation(word.deprel) == "punct" for word in words):
        return False
    if any(word.upos in {"VERB", "AUX"} for word in words):
        return False
    return any(word.upos in UD_CONTENT_UPOS for word in words)


def proper_name_sequence(text: str, words: list[object], language: str) -> list[Candidate]:
    if len(words) < 2:
        return []
    return stanza_span_candidates(
        text=text,
        words=words,
        language=language,
        generator="stanza_proper_name",
        candidate_type="proper_name",
    )


def stanza_candidate_score(words: list[object]) -> float:
    content_words = sum(1 for word in words if word.upos in UD_CONTENT_UPOS)
    score = min(1.0, content_words / max(len(words), 1))
    if len(words) == 1:
        surface = str(getattr(words[0], "text", "") or "")
        score = 0.6 if "-" in surface and len(surface) > 4 else 0.5
    score -= max(0, len(words) - 3) * 0.04
    if len(words) > 1 and any(word.upos == "PROPN" for word in words):
        score += 0.03
    return max(0.4, min(1.0, score))


def stanza_candidate_surface_is_clean(surface: str) -> bool:
    if SPAN_SEPARATOR_RE.search(surface):
        return False
    if LEGAL_CITATION_RE.search(surface):
        return False
    if DATE_FRAGMENT_RE.search(surface):
        return False
    if surface.isdecimal():
        return False
    if MONTH_NAME_RE.match(surface):
        return False
    if len(surface) <= 3 and surface.isupper():
        return False
    return True


def make_candidate(
    *,
    surface: str,
    start_char: int,
    end_char: int,
    language: str,
    generator: str,
    candidate_type: str,
    score: float,
    lemma: str = "",
    upos: tuple[str, ...] = (),
) -> Candidate:
    surface = clean_span(surface)
    lookup_forms = lookup_forms_for_candidate(surface=surface, lemma=lemma)
    return Candidate(
        surface=surface,
        start_char=start_char,
        end_char=end_char,
        language=language,
        generators=(generator,),
        candidate_type=candidate_type,
        score=score,
        lemma=lemma,
        upos=upos,
        lookup_forms=lookup_forms,
    )


def lookup_forms_for_candidate(surface: str, lemma: str = "") -> tuple[str, ...]:
    forms = [
        surface,
        surface.casefold(),
        normalize_spacing_and_punctuation(surface),
    ]
    if lemma:
        forms.extend([lemma, normalize_spacing_and_punctuation(lemma)])
    return tuple(dict.fromkeys(form for form in forms if form))


def normalize_spacing_and_punctuation(text: str) -> str:
    text = text.casefold()
    text = text.replace("’", "'").replace("‐", "-").replace("‑", "-").replace("–", "-")
    return re.sub(r"\s+", " ", text).strip()


def normalize_key(text: str) -> str:
    return normalize_spacing_and_punctuation(text)


def clean_span(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip(" ,.;:()[]{}")


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
