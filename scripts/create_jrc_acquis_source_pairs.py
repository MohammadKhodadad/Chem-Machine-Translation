from __future__ import annotations

import argparse
import json
import re
import zipfile
from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen
from xml.etree.ElementTree import iterparse

from chem_machine_translation.utils.text import approximate_token_count, normalize_text

LANGUAGE_NAMES = {
    "de": "German",
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "pt": "Portuguese",
}
DEFAULT_LANGUAGES = ("en", "es", "de", "fr", "pt")
DEFAULT_BASE_URL = "https://object.pouta.csc.fi/OPUS-JRC-Acquis/v3.0/moses"
USER_AGENT = "chem-machine-translation/0.1 (JRC-Acquis benchmark source builder)"
_WORD_RE = re.compile(r"\w", re.UNICODE)


@dataclass(frozen=True)
class AlignedSegment:
    doc_id: str
    source_text: str
    target_text: str
    source_tokens: int
    target_tokens: int


@dataclass(frozen=True)
class ChunkCandidate:
    chunk_id: str
    doc_id: str
    source_text: str
    target_text: str
    source_tokens: int
    target_tokens: int
    segment_count: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create a benchmark source-pair JSONL from OPUS JRC-Acquis aligned segments."
        ),
    )
    parser.add_argument(
        "--output-jsonl",
        type=Path,
        default=Path("benchmark_sources/jrc_acquis_chunks_250_per_language_pair.jsonl"),
    )
    parser.add_argument(
        "--metadata-output",
        type=Path,
        default=None,
        help="Optional metadata JSON path. Defaults to <output-jsonl>_metadata.json.",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path("data/opus_jrc_acquis"),
        help="Directory for downloaded OPUS JRC-Acquis Moses zip files.",
    )
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument(
        "--language",
        action="append",
        dest="languages",
        choices=sorted(LANGUAGE_NAMES),
        help="Language included in all ordered pair generation. Repeat for multiple languages.",
    )
    parser.add_argument("--limit", type=int, default=250, help="Chunks per ordered direction.")
    parser.add_argument("--min-chunk-tokens", type=int, default=250)
    parser.add_argument("--target-chunk-tokens", type=int, default=450)
    parser.add_argument("--max-chunk-tokens", type=int, default=700)
    parser.add_argument("--min-segment-tokens", type=int, default=3)
    parser.add_argument("--max-segment-tokens", type=int, default=180)
    parser.add_argument("--max-token-ratio", type=float, default=3.0)
    parser.add_argument(
        "--max-chunks-per-doc",
        type=int,
        default=1,
        help="Maximum chunks selected from the same JRC document per ordered direction.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    languages = tuple(dict.fromkeys(args.languages or DEFAULT_LANGUAGES))
    if len(languages) < 2:
        raise ValueError("At least two languages are required.")
    args.output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    args.cache_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for source_language, target_language in ordered_language_pairs(languages):
        direction = f"{source_language}-{target_language}"
        chunks = list(
            select_chunks_for_direction(
                source_language=source_language,
                target_language=target_language,
                limit=args.limit,
                cache_dir=args.cache_dir,
                base_url=args.base_url,
                min_chunk_tokens=args.min_chunk_tokens,
                target_chunk_tokens=args.target_chunk_tokens,
                max_chunk_tokens=args.max_chunk_tokens,
                min_segment_tokens=args.min_segment_tokens,
                max_segment_tokens=args.max_segment_tokens,
                max_token_ratio=args.max_token_ratio,
                max_chunks_per_doc=args.max_chunks_per_doc,
            )
        )
        rows.extend(
            source_pair_row(
                chunk=chunk,
                source_language=source_language,
                target_language=target_language,
            )
            for chunk in chunks
        )
        print(f"Selected {len(chunks)} source pairs for {direction}.", flush=True)

    write_jsonl(args.output_jsonl, rows)
    metadata_output = args.metadata_output or default_metadata_path(args.output_jsonl)
    write_metadata(
        metadata_output,
        rows=rows,
        languages=languages,
        args=args,
    )
    print(f"Wrote {len(rows)} source pairs to {args.output_jsonl}")
    print(f"Wrote metadata to {metadata_output}")


def source_pair_row(
    *,
    chunk: Any,
    source_language: str,
    target_language: str,
) -> dict[str, Any]:
    direction = f"{source_language}-{target_language}"
    return {
        "source": "jrc_acquis_opus",
        "example_id": chunk.chunk_id,
        "doc_id": chunk.doc_id,
        "language_pair": direction,
        "source_language": source_language,
        "target_language": target_language,
        "source_text": chunk.source_text,
        "target_text": chunk.target_text,
        "approx_source_tokens": chunk.source_tokens,
        "approx_target_tokens": chunk.target_tokens,
        "segment_count": chunk.segment_count,
        "selection": "jrc_acquis_opus_aligned_segments_chunked_by_document",
    }


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with temp_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    temp_path.replace(path)


def write_metadata(
    path: Path,
    *,
    rows: list[dict[str, Any]],
    languages: tuple[str, ...],
    args: argparse.Namespace,
) -> None:
    by_direction = Counter(str(row["language_pair"]) for row in rows)
    source_tokens = [int(row["approx_source_tokens"]) for row in rows]
    metadata = {
        "source": "OPUS JRC-Acquis v3.0 Moses aligned segment files",
        "source_url": args.base_url,
        "rows": len(rows),
        "languages": list(languages),
        "language_pair_counts": dict(sorted(by_direction.items())),
        "limit_per_direction": args.limit,
        "chunking": {
            "min_chunk_tokens": args.min_chunk_tokens,
            "target_chunk_tokens": args.target_chunk_tokens,
            "max_chunk_tokens": args.max_chunk_tokens,
            "min_segment_tokens": args.min_segment_tokens,
            "max_segment_tokens": args.max_segment_tokens,
            "max_token_ratio": args.max_token_ratio,
            "max_chunks_per_doc": args.max_chunks_per_doc,
        },
        "source_token_stats": {
            "min": min(source_tokens) if source_tokens else 0,
            "max": max(source_tokens) if source_tokens else 0,
            "mean": round(sum(source_tokens) / len(source_tokens), 1) if source_tokens else 0,
        },
        "schema": [
            "source",
            "example_id",
            "doc_id",
            "language_pair",
            "source_language",
            "target_language",
            "source_text",
            "target_text",
            "approx_source_tokens",
            "approx_target_tokens",
            "segment_count",
            "selection",
        ],
    }
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temp_path.replace(path)


def default_metadata_path(output_jsonl: Path) -> Path:
    return output_jsonl.with_name(f"{output_jsonl.stem}_metadata.json")


def ordered_language_pairs(languages: tuple[str, ...]) -> Iterator[tuple[str, str]]:
    for source_language in languages:
        for target_language in languages:
            if source_language != target_language:
                yield source_language, target_language


def select_chunks_for_direction(
    *,
    source_language: str,
    target_language: str,
    limit: int,
    cache_dir: Path,
    base_url: str,
    min_chunk_tokens: int,
    target_chunk_tokens: int,
    max_chunk_tokens: int,
    min_segment_tokens: int,
    max_segment_tokens: int,
    max_token_ratio: float,
    max_chunks_per_doc: int | None = 1,
) -> Iterator[ChunkCandidate]:
    pair_languages = canonical_pair(source_language, target_language)
    zip_path = download_pair_zip(
        left_language=pair_languages[0],
        right_language=pair_languages[1],
        cache_dir=cache_dir,
        base_url=base_url,
    )
    segments = iter_aligned_segments(
        zip_path=zip_path,
        pair_languages=pair_languages,
        source_language=source_language,
        target_language=target_language,
        min_segment_tokens=min_segment_tokens,
        max_segment_tokens=max_segment_tokens,
        max_token_ratio=max_token_ratio,
    )
    yielded = 0
    chunks_by_doc: dict[str, int] = {}
    for chunk in chunk_segments(
        segments,
        direction=f"{source_language}-{target_language}",
        min_chunk_tokens=min_chunk_tokens,
        target_chunk_tokens=target_chunk_tokens,
        max_chunk_tokens=max_chunk_tokens,
    ):
        doc_chunk_count = chunks_by_doc.get(chunk.doc_id, 0)
        if max_chunks_per_doc is not None and doc_chunk_count >= max_chunks_per_doc:
            continue
        yield chunk
        chunks_by_doc[chunk.doc_id] = doc_chunk_count + 1
        yielded += 1
        if yielded >= limit:
            return


def canonical_pair(source_language: str, target_language: str) -> tuple[str, str]:
    left_language, right_language = sorted((source_language, target_language))
    return left_language, right_language


def download_pair_zip(
    *,
    left_language: str,
    right_language: str,
    cache_dir: Path,
    base_url: str,
) -> Path:
    pair = f"{left_language}-{right_language}"
    zip_path = cache_dir / f"JRC-Acquis.{pair}.txt.zip"
    if zip_path.exists():
        return zip_path
    url = f"{base_url.rstrip('/')}/{pair}.txt.zip"
    print(f"Downloading {url}", flush=True)
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=180.0) as response:
        payload = response.read()
    temp_path = zip_path.with_suffix(zip_path.suffix + ".tmp")
    temp_path.write_bytes(payload)
    temp_path.replace(zip_path)
    return zip_path


def iter_aligned_segments(
    *,
    zip_path: Path,
    pair_languages: tuple[str, str],
    source_language: str,
    target_language: str,
    min_segment_tokens: int,
    max_segment_tokens: int,
    max_token_ratio: float,
) -> Iterator[AlignedSegment]:
    left_language, right_language = pair_languages
    pair = f"{left_language}-{right_language}"
    source_member = f"JRC-Acquis.{pair}.{source_language}"
    target_member = f"JRC-Acquis.{pair}.{target_language}"
    metadata_member = f"JRC-Acquis.{pair}.xml"
    with zipfile.ZipFile(zip_path) as archive:
        with (
            archive.open(source_member) as source_raw,
            archive.open(target_member) as target_raw,
            archive.open(metadata_member) as metadata_raw,
        ):
            source_lines = iter_text_lines(source_raw)
            target_lines = iter_text_lines(target_raw)
            doc_ids = iter_doc_ids(metadata_raw, left_language, right_language)
            for doc_id, source_line, target_line in zip(
                doc_ids,
                source_lines,
                target_lines,
                strict=True,
            ):
                segment = build_segment(
                    doc_id=doc_id,
                    source_text=normalize_text(source_line),
                    target_text=normalize_text(target_line),
                )
                if segment and segment_is_usable(
                    segment,
                    min_segment_tokens=min_segment_tokens,
                    max_segment_tokens=max_segment_tokens,
                    max_token_ratio=max_token_ratio,
                ):
                    yield segment


def iter_text_lines(raw_file: Any) -> Iterator[str]:
    for raw_line in raw_file:
        yield raw_line.decode("utf-8", errors="replace").strip()


def iter_doc_ids(raw_file: Any, left_language: str, right_language: str) -> Iterator[str]:
    current_doc_id = ""
    for event, element in iterparse(raw_file, events=("start", "end")):
        if event == "start" and element.tag == "linkGrp":
            current_doc_id = doc_id_from_link_group(
                element.attrib.get("fromDoc", ""),
                left_language,
                right_language,
            )
        elif event == "end" and element.tag == "link":
            yield current_doc_id
            element.clear()
        elif event == "end" and element.tag == "linkGrp":
            element.clear()


def doc_id_from_link_group(from_doc: str, left_language: str, right_language: str) -> str:
    filename = from_doc.rsplit("/", 1)[-1]
    for suffix in (
        f"-{left_language}.xml.gz",
        f"-{right_language}.xml.gz",
        ".xml.gz",
        ".xml",
    ):
        if filename.endswith(suffix):
            filename = filename[: -len(suffix)]
            break
    return filename or "unknown"


def build_segment(doc_id: str, source_text: str, target_text: str) -> AlignedSegment | None:
    if not source_text or not target_text:
        return None
    return AlignedSegment(
        doc_id=doc_id,
        source_text=source_text,
        target_text=target_text,
        source_tokens=approximate_token_count(source_text),
        target_tokens=approximate_token_count(target_text),
    )


def segment_is_usable(
    segment: AlignedSegment,
    *,
    min_segment_tokens: int,
    max_segment_tokens: int,
    max_token_ratio: float,
) -> bool:
    if segment.source_tokens < min_segment_tokens or segment.target_tokens < min_segment_tokens:
        return False
    if segment.source_tokens > max_segment_tokens or segment.target_tokens > max_segment_tokens:
        return False
    if not _WORD_RE.search(segment.source_text) or not _WORD_RE.search(segment.target_text):
        return False
    ratio = max(segment.source_tokens, segment.target_tokens) / max(
        min(segment.source_tokens, segment.target_tokens),
        1,
    )
    return ratio <= max_token_ratio


def chunk_segments(
    segments: Iterator[AlignedSegment],
    *,
    direction: str,
    min_chunk_tokens: int,
    target_chunk_tokens: int,
    max_chunk_tokens: int,
) -> Iterator[ChunkCandidate]:
    buffer: list[AlignedSegment] = []
    chunk_index = 0
    current_doc_id = ""

    for segment in segments:
        if current_doc_id and segment.doc_id != current_doc_id:
            emitted = maybe_emit_chunk(buffer, direction, chunk_index, min_chunk_tokens)
            if emitted:
                yield emitted
                chunk_index += 1
            buffer = []
        current_doc_id = segment.doc_id

        next_token_count = sum(item.source_tokens for item in buffer) + segment.source_tokens
        if buffer and next_token_count > max_chunk_tokens:
            emitted = maybe_emit_chunk(buffer, direction, chunk_index, min_chunk_tokens)
            if emitted:
                yield emitted
                chunk_index += 1
                buffer = []

        if segment.source_tokens <= max_chunk_tokens:
            buffer.append(segment)

        if sum(item.source_tokens for item in buffer) >= target_chunk_tokens:
            emitted = maybe_emit_chunk(buffer, direction, chunk_index, min_chunk_tokens)
            if emitted:
                yield emitted
                chunk_index += 1
                buffer = []

    emitted = maybe_emit_chunk(buffer, direction, chunk_index, min_chunk_tokens)
    if emitted:
        yield emitted


def maybe_emit_chunk(
    segments: list[AlignedSegment],
    direction: str,
    chunk_index: int,
    min_chunk_tokens: int,
) -> ChunkCandidate | None:
    if not segments:
        return None
    source_tokens = sum(segment.source_tokens for segment in segments)
    if source_tokens < min_chunk_tokens:
        return None
    target_tokens = sum(segment.target_tokens for segment in segments)
    doc_id = segments[0].doc_id
    return ChunkCandidate(
        chunk_id=f"{direction}:{doc_id}:chunk-{chunk_index + 1:04d}",
        doc_id=doc_id,
        source_text=normalize_text(" ".join(segment.source_text for segment in segments)),
        target_text=normalize_text(" ".join(segment.target_text for segment in segments)),
        source_tokens=source_tokens,
        target_tokens=target_tokens,
        segment_count=len(segments),
    )


if __name__ == "__main__":
    main()
