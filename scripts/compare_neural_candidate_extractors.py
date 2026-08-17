from __future__ import annotations

import argparse
import json
import math
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Candidate:
    surface: str
    start_char: int
    end_char: int
    language: str
    method: str
    score: float
    candidate_type: str


@dataclass(frozen=True)
class ExtractorResult:
    method: str
    status: str
    candidates: list[Candidate]
    error: str = ""


class XLMRNOBIExtractor:
    def __init__(self, model_name: str) -> None:
        from transformers import pipeline

        self.model_name = model_name
        self.pipeline = pipeline(
            "token-classification",
            model=model_name,
            aggregation_strategy="none",
        )

    def extract(self, text: str, language: str, max_candidates: int) -> ExtractorResult:
        outputs = self.pipeline(text)
        candidates = decode_token_classifier_spans(
            text=text,
            language=language,
            method="xlmr_nobi",
            outputs=outputs,
        )
        return ExtractorResult(
            method="xlmr_nobi",
            status="ok",
            candidates=rank_candidates(candidates)[:max_candidates],
        )


class XLMRSpanEmbeddingExtractor:
    """Experimental unsupervised span scorer over exact text spans.

    This is not a trained ATE model. It enumerates exact spans and ranks them with contextual
    XLM-R embeddings, so it is useful as a baseline for whether embeddings alone help.
    """

    def __init__(self, model_name: str, max_span_tokens: int) -> None:
        import torch
        from transformers import AutoModel, AutoTokenizer

        self.torch = torch
        self.max_span_tokens = max_span_tokens
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.model.eval()

    def extract(self, text: str, language: str, max_candidates: int) -> ExtractorResult:
        spans = enumerate_word_spans(text, max_span_tokens=self.max_span_tokens)
        if not spans:
            return ExtractorResult("xlmr_span_embedding", "ok", [])

        encoded = self.tokenizer(
            text,
            return_offsets_mapping=True,
            return_tensors="pt",
            truncation=True,
            max_length=512,
        )
        offsets = encoded.pop("offset_mapping")[0].tolist()
        with self.torch.no_grad():
            hidden = self.model(**encoded).last_hidden_state[0]

        sentence_embedding = hidden.mean(dim=0)
        candidates = []
        for start_char, end_char, surface in spans:
            token_indexes = [
                index
                for index, (token_start, token_end) in enumerate(offsets)
                if token_start < end_char and token_end > start_char and token_end > token_start
            ]
            if not token_indexes:
                continue
            span_embedding = hidden[token_indexes].mean(dim=0)
            score = cosine_similarity(span_embedding, sentence_embedding)
            score *= min(1.0, 0.75 + 0.05 * len(surface.split()))
            candidates.append(
                Candidate(
                    surface=surface,
                    start_char=start_char,
                    end_char=end_char,
                    language=language,
                    method="xlmr_span_embedding",
                    score=float(score),
                    candidate_type="embedding_ranked_span",
                )
            )
        return ExtractorResult(
            method="xlmr_span_embedding",
            status="ok",
            candidates=rank_candidates(candidates)[:max_candidates],
        )


class GLiNERExtractor:
    def __init__(self, model_name: str, labels: list[str]) -> None:
        from gliner import GLiNER

        self.model = GLiNER.from_pretrained(model_name)
        self.labels = labels

    def extract(self, text: str, language: str, max_candidates: int) -> ExtractorResult:
        entities = self.model.predict_entities(text, self.labels, threshold=0.2)
        candidates = [
            Candidate(
                surface=clean_span(str(entity.get("text", ""))),
                start_char=int(entity.get("start", 0)),
                end_char=int(entity.get("end", 0)),
                language=language,
                method="gliner",
                score=float(entity.get("score", 0.0)),
                candidate_type=str(entity.get("label", "term")),
            )
            for entity in entities
            if clean_span(str(entity.get("text", "")))
        ]
        return ExtractorResult(
            method="gliner",
            status="ok",
            candidates=rank_candidates(candidates)[:max_candidates],
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare neural and embedding-based terminology candidate extractors.",
    )
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--text", help="Text to extract candidates from.")
    input_group.add_argument("--text-file", type=Path, help="UTF-8 text file to extract from.")
    input_group.add_argument("--source-jsonl", type=Path, help="JSONL source rows to extract from.")
    parser.add_argument("--language", help="Language code for --text or --text-file input.")
    parser.add_argument("--text-field", default="target_text")
    parser.add_argument("--language-field", default="target_language")
    parser.add_argument("--id-field", default="example_id")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--max-candidates", type=int, default=15)
    parser.add_argument(
        "--methods",
        default="xlmr-nobi,xlmr-span-embedding,gliner",
        help="Comma-separated methods: xlmr-nobi,xlmr-span-embedding,gliner.",
    )
    parser.add_argument("--nobi-model", default="tthhanh/xlm-ate-nobi-en-nes")
    parser.add_argument("--span-model", default="xlm-roberta-base")
    parser.add_argument("--max-span-tokens", type=int, default=6)
    parser.add_argument("--gliner-model", default="urchade/gliner_multi-v2.1")
    parser.add_argument(
        "--gliner-labels",
        default="technical term,chemical term,legal term,scientific concept",
    )
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    args = parse_args()
    rows = load_input_rows(args)
    methods = [method.strip() for method in args.methods.split(",") if method.strip()]
    extractors = build_extractors(args, methods)

    outputs = []
    for row in rows:
        results = []
        for method, extractor_or_error in extractors.items():
            if isinstance(extractor_or_error, str):
                results.append(
                    ExtractorResult(
                        method=method,
                        status="unavailable",
                        candidates=[],
                        error=extractor_or_error,
                    )
                )
                continue
            try:
                results.append(
                    extractor_or_error.extract(
                        text=row["text"],
                        language=row["language"],
                        max_candidates=args.max_candidates,
                    )
                )
            except Exception as exc:
                results.append(ExtractorResult(method, "error", [], str(exc)))
        outputs.append({**row, "results": results})

    if args.json:
        print_json(outputs)
    else:
        print_markdown(outputs)


def build_extractors(args: argparse.Namespace, methods: list[str]) -> dict[str, Any | str]:
    extractors: dict[str, Any | str] = {}
    for method in methods:
        try:
            if method == "xlmr-nobi":
                extractors["xlmr_nobi"] = XLMRNOBIExtractor(args.nobi_model)
            elif method == "xlmr-span-embedding":
                extractors["xlmr_span_embedding"] = XLMRSpanEmbeddingExtractor(
                    args.span_model,
                    max_span_tokens=args.max_span_tokens,
                )
            elif method == "gliner":
                labels = [label.strip() for label in args.gliner_labels.split(",") if label.strip()]
                extractors["gliner"] = GLiNERExtractor(args.gliner_model, labels)
            else:
                extractors[method] = f"Unknown method: {method}"
        except Exception as exc:
            extractors[method.replace("-", "_")] = str(exc)
    return extractors


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
            }
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
                }
            )
    return rows


def decode_token_classifier_spans(
    *,
    text: str,
    language: str,
    method: str,
    outputs: list[dict[str, Any]],
) -> list[Candidate]:
    candidates = []
    current: list[dict[str, Any]] = []

    def flush_current() -> None:
        if not current:
            return
        start_char = int(current[0]["start"])
        end_char = int(current[-1]["end"])
        surface = clean_span(text[start_char:end_char])
        if surface:
            score = sum(float(token.get("score", 0.0)) for token in current) / len(current)
            candidates.append(
                Candidate(
                    surface=surface,
                    start_char=start_char,
                    end_char=end_char,
                    language=language,
                    method=method,
                    score=score,
                    candidate_type="token_classifier_span",
                )
            )
        current.clear()

    for output in outputs:
        label = str(output.get("entity") or output.get("entity_group") or "").lower()
        if label in {"o", "label_0"}:
            flush_current()
            continue
        if "b" in label and current:
            flush_current()
        current.append(output)
        if "bn" in label or "in" in label:
            surface = clean_span(text[int(output["start"]) : int(output["end"])])
            if surface:
                candidates.append(
                    Candidate(
                        surface=surface,
                        start_char=int(output["start"]),
                        end_char=int(output["end"]),
                        language=language,
                        method=method,
                        score=float(output.get("score", 0.0)),
                        candidate_type="nobi_nested_token",
                    )
                )
    flush_current()
    return deduplicate_candidates(candidates)


def enumerate_word_spans(text: str, max_span_tokens: int) -> list[tuple[int, int, str]]:
    tokens = [
        (match.start(), match.end(), match.group(0))
        for match in re.finditer(r"\b[^\W_]+(?:[-'][^\W_]+)*\b", text, flags=re.UNICODE)
    ]
    spans = []
    for size in range(1, max_span_tokens + 1):
        for index in range(0, max(len(tokens) - size + 1, 0)):
            span_tokens = tokens[index : index + size]
            start_char = span_tokens[0][0]
            end_char = span_tokens[-1][1]
            surface = clean_span(text[start_char:end_char])
            if surface:
                spans.append((start_char, end_char, surface))
    return spans


def cosine_similarity(left: Any, right: Any) -> float:
    denominator = float(left.norm() * right.norm())
    if math.isclose(denominator, 0.0):
        return 0.0
    return float((left @ right) / denominator)


def rank_candidates(candidates: list[Candidate]) -> list[Candidate]:
    return sorted(
        deduplicate_candidates(candidates),
        key=lambda candidate: (
            candidate.score,
            candidate.end_char - candidate.start_char,
            -candidate.start_char,
        ),
        reverse=True,
    )


def deduplicate_candidates(candidates: list[Candidate]) -> list[Candidate]:
    by_key: dict[tuple[int, int, str, str], Candidate] = {}
    for candidate in candidates:
        key = (
            candidate.start_char,
            candidate.end_char,
            candidate.surface.casefold(),
            candidate.method,
        )
        existing = by_key.get(key)
        if existing is None or candidate.score > existing.score:
            by_key[key] = candidate
    return list(by_key.values())


def clean_span(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip(" ,.;:()[]{}")


def print_json(outputs: list[dict[str, Any]]) -> None:
    serializable = []
    for output in outputs:
        serializable.append(
            {
                **{key: value for key, value in output.items() if key != "results"},
                "results": [
                    {
                        "method": result.method,
                        "status": result.status,
                        "error": result.error,
                        "candidates": [asdict(candidate) for candidate in result.candidates],
                    }
                    for result in output["results"]
                ],
            }
        )
    print(json.dumps(serializable, ensure_ascii=False, indent=2))


def print_markdown(outputs: list[dict[str, Any]]) -> None:
    for output in outputs:
        print(f"\n## {output['id']} ({output['language']})")
        print()
        text = str(output["text"])
        print(f"Text: {text[:350]}{'...' if len(text) > 350 else ''}")
        for result in output["results"]:
            print(f"\n### {result.method}: {result.status}")
            if result.error:
                print(result.error)
                continue
            if not result.candidates:
                print("- no candidates")
                continue
            for candidate in result.candidates:
                offsets = f"{candidate.start_char}:{candidate.end_char}"
                print(
                    f"- {candidate.surface} "
                    f"[{candidate.candidate_type}; {offsets}; score={candidate.score:.3f}]"
                )


if __name__ == "__main__":
    main()
