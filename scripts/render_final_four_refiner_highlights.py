from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from matplotlib import font_manager
from PIL import Image, ImageDraw, ImageFont

from chem_machine_translation.data.terminology import (
    DatasetTerminologyTerm,
    dataset_term_from_json,
    deduplicate_terms,
)
from refine_final_four_terms import CASES, OUTPUT_PATH, load_case_from_root, load_terms


ROOT = Path(__file__).resolve().parents[1]
FIGURE_DIR = ROOT / "docs" / "figures"
MAX_CHARS_PER_LINE = 112
FONT_SIZE = 18
LEFT_MARGIN = 28
TOP_MARGIN = 58
RIGHT_MARGIN = 28
LINE_GAP = 50

LANES = [
    ("Extracted", (140, 140, 140), 0),
    ("Refined", (31, 119, 180), 7),
    ("Verified refined", (44, 160, 44), 14),
]


def main() -> None:
    results = json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
    result_by_item = {result["item"]: result for result in results}
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    for case in CASES:
        rows = [load_case_from_root(case, root) for root in case["roots"]]
        rows = [row for row in rows if row is not None]
        if not rows:
            raise ValueError(f"Could not find case row: {case['example_id']}")
        target_text = rows[0]["target_text"]
        extracted_terms = deduplicate_terms(
            [
                term
                for row in rows
                for term in load_terms(row["manifest"].get("terminology", []))
            ]
        )
        refined_terms = [
            dataset_term_from_json(term)
            for term in result_by_item[case["item"]]["refined_terms"]
        ]
        verified_refined_terms = [term for term in refined_terms if term.verified_by]
        output_path = FIGURE_DIR / f"final-four-item-{case['item']}-refiner-highlights.png"
        render_case(
            title=f"Item {case['item']}: {case['label']}",
            text=target_text,
            extracted_terms=extracted_terms,
            refined_terms=refined_terms,
            verified_refined_terms=verified_refined_terms,
            output_path=output_path,
        )
        print(f"Wrote {output_path}")


def render_case(
    title: str,
    text: str,
    extracted_terms: list[DatasetTerminologyTerm],
    refined_terms: list[DatasetTerminologyTerm],
    verified_refined_terms: list[DatasetTerminologyTerm],
    output_path: Path,
) -> None:
    font_path = font_manager.findfont("DejaVu Sans Mono")
    text_font = ImageFont.truetype(font_path, FONT_SIZE)
    title_font = ImageFont.truetype(font_path, FONT_SIZE + 2)
    lines = wrap_with_offsets(text, MAX_CHARS_PER_LINE)
    line_width = int(text_font.getlength("M" * MAX_CHARS_PER_LINE))
    width = LEFT_MARGIN + line_width + RIGHT_MARGIN
    height = TOP_MARGIN + len(lines) * LINE_GAP + 30
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)

    draw.text((LEFT_MARGIN, 16), title, fill=(20, 20, 20), font=title_font)
    legend_x = LEFT_MARGIN
    for label, color, lane_offset in LANES:
        y = 45 + lane_offset
        draw.line((legend_x, y, legend_x + 46, y), fill=color, width=4)
        draw.text((legend_x + 54, 35), label, fill=(30, 30, 30), font=text_font)
        legend_x += int(text_font.getlength(label)) + 115

    spans_by_lane = [
        term_spans(text, extracted_terms),
        term_spans(text, refined_terms),
        term_spans(text, verified_refined_terms),
    ]
    for line_index, (line, line_start, line_end) in enumerate(lines):
        y = TOP_MARGIN + line_index * LINE_GAP
        draw.text((LEFT_MARGIN, y), line, fill=(15, 15, 15), font=text_font)
        underline_base = y + FONT_SIZE + 8
        for lane_index, (_, color, lane_offset) in enumerate(LANES):
            draw_spans_for_line(
                draw=draw,
                font=text_font,
                line=line,
                line_start=line_start,
                line_end=line_end,
                spans=spans_by_lane[lane_index],
                y=underline_base + lane_offset,
                color=color,
            )

    image.save(output_path)


def draw_spans_for_line(
    draw: ImageDraw.ImageDraw,
    font: ImageFont.FreeTypeFont,
    line: str,
    line_start: int,
    line_end: int,
    spans: list[tuple[int, int]],
    y: int,
    color: tuple[int, int, int],
) -> None:
    for span_start, span_end in spans:
        if span_end <= line_start or span_start >= line_end:
            continue
        start = max(span_start, line_start) - line_start
        end = min(span_end, line_end) - line_start
        x1 = LEFT_MARGIN + int(font.getlength(line[:start]))
        x2 = LEFT_MARGIN + int(font.getlength(line[:end]))
        if x2 > x1:
            draw.line((x1, y, x2, y), fill=color, width=4)


def term_spans(
    text: str,
    terms: list[DatasetTerminologyTerm],
) -> list[tuple[int, int]]:
    spans: set[tuple[int, int]] = set()
    surfaces = sorted(
        {
            target
            for term in terms
            for target in term.target_terms
            if target and len(target.strip()) >= 3
        },
        key=len,
        reverse=True,
    )
    for surface in surfaces:
        for match in re.finditer(re.escape(surface), text, flags=re.IGNORECASE):
            spans.add((match.start(), match.end()))
    return sorted(spans)


def wrap_with_offsets(text: str, max_chars: int) -> list[tuple[str, int, int]]:
    chunks = list(re.finditer(r"\S+\s*", text))
    lines: list[tuple[str, int, int]] = []
    current: list[str] = []
    line_start: int | None = None
    line_end = 0
    for chunk in chunks:
        token = chunk.group(0)
        if line_start is None:
            line_start = chunk.start()
        candidate = "".join(current) + token
        if current and len(candidate.rstrip()) > max_chars:
            line = "".join(current).rstrip()
            lines.append((line, line_start, line_end))
            current = [token]
            line_start = chunk.start()
        else:
            current.append(token)
        line_end = chunk.end()
    if current and line_start is not None:
        lines.append(("".join(current).rstrip(), line_start, line_end))
    return lines


if __name__ == "__main__":
    main()
