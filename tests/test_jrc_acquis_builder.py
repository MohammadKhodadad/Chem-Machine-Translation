import importlib.util
import sys
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "create_jrc_acquis_source_pairs.py"
SPEC = importlib.util.spec_from_file_location("create_jrc_acquis_source_pairs", SCRIPT_PATH)
assert SPEC and SPEC.loader
source_builder = importlib.util.module_from_spec(SPEC)
sys.modules["create_jrc_acquis_source_pairs"] = source_builder
SPEC.loader.exec_module(source_builder)

AlignedSegment = source_builder.AlignedSegment
canonical_pair = source_builder.canonical_pair
chunk_segments = source_builder.chunk_segments
chunk_matches_section_type = source_builder.chunk_matches_section_type
doc_id_from_link_group = source_builder.doc_id_from_link_group


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
