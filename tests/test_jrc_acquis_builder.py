import importlib.util
import sys
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "create_jrc_acquis_source_pairs.py"
SPEC = importlib.util.spec_from_file_location("create_jrc_acquis_source_pairs", SCRIPT_PATH)
assert SPEC and SPEC.loader
source_builder = importlib.util.module_from_spec(SPEC)
sys.modules["create_jrc_acquis_source_pairs"] = source_builder
SPEC.loader.exec_module(source_builder)

AlignedSegment = source_builder.AlignedSegment
ChunkCandidate = source_builder.ChunkCandidate
build_anchored_rows = source_builder.build_anchored_rows
canonical_pair = source_builder.canonical_pair
chunk_segments = source_builder.chunk_segments
chunk_matches_section_type = source_builder.chunk_matches_section_type
chunk_passes_quality_mode = source_builder.chunk_passes_quality_mode
doc_id_from_link_group = source_builder.doc_id_from_link_group
preprocess_jrc_text = source_builder.preprocess_jrc_text


def _segment(doc_id: str, source_text: str, target_text: str) -> AlignedSegment:
    source_tokens = len(source_text.split())
    target_tokens = len(target_text.split())
    return AlignedSegment(
        doc_id=doc_id,
        source_text=source_text,
        target_text=target_text,
        source_tokens=source_tokens,
        target_tokens=target_tokens,
    )


def test_canonical_pair_uses_opus_file_order() -> None:
    assert canonical_pair("en", "de") == ("de", "en")
    assert canonical_pair("pt", "es") == ("es", "pt")


def test_doc_id_from_link_group_strips_language_suffix() -> None:
    assert (
        doc_id_from_link_group(
            "de/1972/jrc21972A0722_03-de.xml.gz",
            "de",
            "en",
        )
        == "jrc21972A0722_03"
    )


def test_chunk_segments_keeps_document_boundaries() -> None:
    segments = iter(
        [
            _segment("doc-a", "alpha beta gamma", "eins zwei drei"),
            _segment("doc-a", "delta epsilon zeta", "vier fünf sechs"),
            _segment("doc-b", "eta theta iota", "sieben acht neun"),
            _segment("doc-b", "kappa lambda mu", "zehn elf zwölf"),
        ]
    )

    chunks = list(
        chunk_segments(
            segments,
            direction="en-de",
            min_chunk_tokens=5,
            target_chunk_tokens=8,
            max_chunk_tokens=12,
        )
    )

    assert [chunk.doc_id for chunk in chunks] == ["doc-a", "doc-b"]
    assert chunks[0].source_text == "alpha beta gamma delta epsilon zeta"
    assert chunks[0].target_text == "eins zwei drei vier fünf sechs"
    assert chunks[0].segment_count == 2


def test_chunk_matches_article_section_type() -> None:
    chunk = source_builder.ChunkCandidate(
        chunk_id="en-fr:doc:chunk-0001",
        doc_id="doc",
        source_text="Article 4 The contracting parties shall notify the committee.",
        target_text="Article 4 Les parties contractantes notifient le comité.",
        source_tokens=8,
        target_tokens=8,
        segment_count=1,
    )

    assert chunk_matches_section_type(chunk, "article")
    assert chunk_matches_section_type(chunk, "all")
    assert not chunk_matches_section_type(chunk, "definition")


def test_chunk_matches_definition_section_type() -> None:
    chunk = source_builder.ChunkCandidate(
        chunk_id="en-es:doc:chunk-0001",
        doc_id="doc",
        source_text='For the purposes of this Agreement, "goods" means products.',
        target_text='A efectos del presente Acuerdo, "mercancías" significa productos.',
        source_tokens=9,
        target_tokens=9,
        segment_count=1,
    )

    assert chunk_matches_section_type(chunk, "definition")
    assert not chunk_matches_section_type(chunk, "article")


def test_preprocess_jrc_text_removes_legacy_opus_markup() -> None:
    text = (
        'Decision establishing holdings<(BLK0)LA ORG="CCF">EN</(BLK0)LA> '
        "CHAPTER I Community typology"
    )

    cleaned = preprocess_jrc_text(text, clean_legacy_markup=True)

    assert "<(BLK0)" not in cleaned
    assert "</(BLK0)" not in cleaned
    assert "Decision establishing holdings CHAPTER I Community typology" == cleaned
    assert preprocess_jrc_text(text, clean_legacy_markup=False) == text


def test_strict_quality_rejects_mid_list_article_chunk() -> None:
    chunk = ChunkCandidate(
        chunk_id="en-fr:doc:chunk-0001",
        doc_id="doc",
        source_text="(g) this starts in the middle of a legal list.",
        target_text="(g) ceci commence au milieu d'une liste juridique.",
        source_tokens=10,
        target_tokens=10,
        segment_count=1,
    )

    assert chunk_passes_quality_mode(chunk, "article", "loose")
    assert not chunk_passes_quality_mode(chunk, "article", "strict")


def test_strict_quality_accepts_clean_article_chunk() -> None:
    chunk = ChunkCandidate(
        chunk_id="en-fr:doc:chunk-0001",
        doc_id="doc",
        source_text="Article 4 The contracting parties shall notify the committee.",
        target_text="Article 4 Les parties contractantes notifient le comité.",
        source_tokens=8,
        target_tokens=8,
        segment_count=1,
    )

    assert chunk_passes_quality_mode(chunk, "article", "strict")


def test_strict_quality_rejects_residual_markup() -> None:
    chunk = ChunkCandidate(
        chunk_id="en-de:doc:chunk-0001",
        doc_id="doc",
        source_text='For the purposes of this Agreement <bad>tag</bad> "goods" shall mean goods.',
        target_text='Im Sinne dieses Abkommens bedeutet "Waren" Waren.',
        source_tokens=11,
        target_tokens=7,
        segment_count=1,
    )

    assert not chunk_passes_quality_mode(chunk, "definition", "strict")


def test_build_anchored_rows_expands_common_docs_to_all_ordered_pairs(monkeypatch) -> None:
    languages = ("en", "de", "fr")
    doc_ids = ["doc-a", "doc-b", "doc-c"]

    def fake_select_chunks_for_direction(**kwargs):
        direction = f"{kwargs['source_language']}-{kwargs['target_language']}"
        return [
            ChunkCandidate(
                chunk_id=f"{direction}:{doc_id}:chunk-0001",
                doc_id=doc_id,
                source_text=f"{direction} source {doc_id}",
                target_text=f"{direction} target {doc_id}",
                source_tokens=4,
                target_tokens=4,
                segment_count=1,
            )
            for doc_id in doc_ids
        ]

    monkeypatch.setattr(
        source_builder,
        "select_chunks_for_direction",
        fake_select_chunks_for_direction,
    )
    monkeypatch.setattr(
        source_builder,
        "common_document_ids_for_languages",
        lambda **kwargs: doc_ids,
    )
    args = SimpleNamespace(
        limit=2,
        anchor_search_multiplier=1,
        anchor_language="en",
        cache_dir=Path("cache"),
        base_url="https://example.test",
        min_chunk_tokens=1,
        target_chunk_tokens=4,
        max_chunk_tokens=10,
        min_segment_tokens=1,
        max_segment_tokens=20,
        max_token_ratio=3.0,
        section_type="article",
        clean_legacy_markup=False,
        quality_mode="loose",
    )

    rows = build_anchored_rows(languages=languages, args=args)

    assert len(rows) == 12
    assert Counter(row["language_pair"] for row in rows) == {
        "en-de": 2,
        "en-fr": 2,
        "de-en": 2,
        "de-fr": 2,
        "fr-en": 2,
        "fr-de": 2,
    }
    assert {row["doc_id"] for row in rows} == {"doc-a", "doc-b"}
    assert {row["selection_mode"] for row in rows} == {"anchored"}
    assert {row["anchor_id"] for row in rows} == {"en:doc-a", "en:doc-b"}

    by_anchor_direction = {(row["anchor_id"], row["language_pair"]): row for row in rows}
    forward = by_anchor_direction[("en:doc-a", "en-de")]
    reverse = by_anchor_direction[("en:doc-a", "de-en")]
    assert forward["source_text"] == reverse["target_text"]
    assert forward["target_text"] == reverse["source_text"]
    assert forward["approx_source_tokens"] == reverse["approx_target_tokens"]
    assert forward["approx_target_tokens"] == reverse["approx_source_tokens"]
