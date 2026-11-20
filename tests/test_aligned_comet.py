from pathlib import Path
from types import SimpleNamespace

import pytest

from chem_machine_translation.evaluation.aligned_comet import (
    AlignedCometConfig,
    AlignedCometScorer,
    SentAlignCometConfig,
    SentAlignCometScorer,
    SpacySentenceSegmenter,
    TokenCheckedCometScorer,
    TransformersSentenceEmbedder,
)
from chem_machine_translation.evaluation.metrics import (
    DEFAULT_METRIC_NAMES,
    compute_translation_metrics,
    parse_metric_names,
)
from chem_machine_translation.experiment.config import evaluation_config_from_mapping
from chem_machine_translation.experiment.pipeline import score_prediction_row


def test_aligned_comet_is_opt_in():
    assert parse_metric_names(["aligned_comet"]) == ("aligned_comet",)
    assert "aligned_comet" not in DEFAULT_METRIC_NAMES
    assert parse_metric_names(["reference_assignment_comet"]) == ("reference_assignment_comet",)
    assert "reference_assignment_comet" not in DEFAULT_METRIC_NAMES


class FakeSegmenter:
    def segment(self, text, language):
        return [part.strip() for part in text.split("|") if part.strip()]


class FakeEmbedder:
    def encode(self, texts):
        vectors = {
            "source A": [1, 0, 0, 0],
            "reference A": [1, 0, 0, 0],
            "translation A": [1, 0, 0, 0],
            "source B": [0, 1, 0, 0],
            "reference B": [0, 1, 0, 0],
            "translation B": [0, 1, 0, 0],
            "addition": [0, 0, 1, 0],
        }
        return [vectors[text] for text in texts]


class FakeComet:
    def __init__(self):
        self.calls = []

    def token_count(self, text):
        return len(text.split()) + 2

    def token_limit(self):
        return 512

    def score(self, source, prediction, reference):
        self.calls.append((source, prediction, reference))
        return 0.9


class FakeSentAlign:
    def __init__(self, *paths):
        self.paths = iter(paths)

    def align(self, left, right):
        return SimpleNamespace(links=[
            SimpleNamespace(src=source, trg=target) for source, target in next(self.paths)
        ])


def test_sentalign_span_closure_handles_merges_without_reusing_sentences():
    comet = FakeComet()
    scorer = SentAlignCometScorer(
        segmenter=FakeSegmenter(), comet_scorer=comet,
        aligner=FakeSentAlign(
            [((0, 1), (0,)), ((2,), (1,))],
            [((0,), (0,)), ((1, 2), (1,))],
        ),
    )
    result = scorer.score_document("s0 | s1", "c0 | c1", "r0 | r1 | r2")
    assert result.score == pytest.approx(0.9)
    assert comet.calls == [("s0 s1", "c0 c1", "r0 r1 r2")]
    assert result.blocks[0]["reference_indices"] == [0, 1, 2]
    assert result.config["alignment"] == "sentalign_2_reference_span_closure"
    assert result.config["alignment_model"] == "BAAI/bge-m3"
    assert result.config["alignment_pooling"] == "cls"
    assert result.config["alignment_max_tokens"] == 8192


def test_sentalign_keeps_omissions_additions_and_source_only_blocks():
    scorer = SentAlignCometScorer(
        segmenter=FakeSegmenter(), comet_scorer=FakeComet(),
        aligner=FakeSentAlign(
            [((0,), (0,)), ((1,), (1,)), ((), (2,))],
            [((0,), (0,)), ((1,), ()), ((), (1,))],
        ),
    )
    result = scorer.score_document("s0 | s1 | extra", "c0 | extra", "r0 | r1")
    assert [block["state"] for block in result.blocks] == [
        "matched", "omission", "addition", "source_only",
    ]
    assert result.score == pytest.approx(0.9 / 4)
    assert result.null_alignment_ratio == 0.75


def test_sentalign_rejects_duplicate_sentence_coverage():
    scorer = SentAlignCometScorer(
        segmenter=FakeSegmenter(), comet_scorer=FakeComet(),
        aligner=FakeSentAlign([((0,), (0,)), ((0,), (1,))]),
    )
    with pytest.raises(ValueError, match="exactly once"):
        scorer.score_document("s0 | s1", "c0", "r0")


def test_sentalign_checks_merged_comet_budget_before_scoring():
    comet = FakeComet()
    scorer = SentAlignCometScorer(
        SentAlignCometConfig(max_comet_tokens=3),
        segmenter=FakeSegmenter(), comet_scorer=comet,
        aligner=FakeSentAlign([((0, 1), (0,))], [((0, 1), (0,))]),
    )
    with pytest.raises(ValueError, match="token budget"):
        scorer.score_document("s0", "c0", "r0 | r1")
    assert not comet.calls


def test_sentalign_empty_candidate_needs_no_target_alignment():
    scorer = SentAlignCometScorer(
        segmenter=FakeSegmenter(), comet_scorer=FakeComet(),
        aligner=FakeSentAlign([((0,), (0,))]),
    )
    result = scorer.score_document("s0", "", "r0")
    assert result.score == 0
    assert result.blocks[0]["state"] == "omission"


def test_sentalign_lazy_backend_receives_bge_pooling_and_budget(monkeypatch):
    import sys

    options = {}

    def backend(**kwargs):
        options.update(kwargs)
        return FakeSentAlign([((0,), (0,))], [((0,), (0,))])

    monkeypatch.setitem(sys.modules, "sentalign", SimpleNamespace(SentAlign=backend))
    scorer = SentAlignCometScorer(segmenter=FakeSegmenter(), comet_scorer=FakeComet())
    scorer.score_document("s0", "c0", "r0")
    assert options["encoder"] == "BAAI/bge-m3"
    assert options["pooling"] == "cls"
    assert options["max_tokens"] == 8192
    assert options["compat"] == "none"
    assert options["half"] is False


def test_sentalign_partial_null_in_merged_group_is_visible_in_audit():
    scorer = SentAlignCometScorer(
        segmenter=FakeSegmenter(), comet_scorer=FakeComet(),
        aligner=FakeSentAlign(
            [((0,), (0,)), ((1,), ())], [((0, 1), (0,))],
        ),
    )
    result = scorer.score_document("s0", "c0", "r0 | r1")
    assert result.blocks[0]["state"] == "matched"
    assert result.blocks[0]["source_null_reference_indices"] == [1]
    assert result.blocks[0]["candidate_null_reference_indices"] == []


def make_scorer(**options):
    comet = FakeComet()
    scorer = AlignedCometScorer(
        config=AlignedCometConfig(**options),
        segmenter=FakeSegmenter(),
        embedder=FakeEmbedder(),
        comet_scorer=comet,
    )
    return scorer, comet


def test_pairs_reference_and_translation_and_retains_omissions_and_additions():
    scorer, comet = make_scorer()
    result = scorer.score_document(
        source="source A | source B",
        reference="reference A | reference B",
        prediction="translation A | addition",
        source_language="en",
        target_language="de",
    )
    assert result.score == pytest.approx(0.9 / 3)
    assert result.null_alignment_ratio == pytest.approx(2 / 3)
    assert comet.calls == [("source A", "translation A", "reference A")]
    assert [block["state"] for block in result.blocks] == ["matched", "omission", "addition"]
    assert result.config["embedding_model"] == "BAAI/bge-m3"


def test_source_is_aligned_instead_of_repeating_the_document():
    scorer, comet = make_scorer()
    result = scorer.score_document(
        source="source B | source A",
        reference="reference A | reference B",
        prediction="translation A | translation B",
    )
    assert result.score == pytest.approx(0.9)
    assert comet.calls == [
        ("source A", "translation A", "reference A"),
        ("source B", "translation B", "reference B"),
    ]


def test_empty_translation_is_penalized_without_comet_calls():
    scorer, comet = make_scorer(null_score=0.1)
    result = scorer.score_document(source="source A", reference="reference A", prediction="")
    assert result.score == pytest.approx(0.1)
    assert result.null_alignment_ratio == 1
    assert comet.calls == []


def test_comet_inputs_over_budget_raise_instead_of_truncating():
    scorer, comet = make_scorer(max_comet_tokens=3)
    with pytest.raises(ValueError, match="token budget"):
        scorer.score_document(
            source="source A", reference="reference A", prediction="translation A"
        )
    assert comet.calls == []


@pytest.mark.parametrize("config_class, scorer_class", [
    (AlignedCometConfig, AlignedCometScorer), (SentAlignCometConfig, SentAlignCometScorer),
])
@pytest.mark.parametrize("tokens", [510, 511])
@pytest.mark.parametrize("long_side", ["source", "reference", "prediction"])
def test_filtered_blocks_keep_gaps_and_report_original_sentence_coverage(
    config_class, scorer_class, tokens, long_side,
):
    comet = FakeComet()
    scorer = scorer_class(config_class(exclude_overlong_blocks=True), comet_scorer=comet)
    blocks = [
        {"source": "s0", "reference": "r0", "prediction": "c0",
         "source_index": 0, "reference_index": 0, "prediction_index": 0,
         "state": "matched", "score": 0},
        {"source": "s1", "reference": "r1", "prediction": "c1",
         "source_index": 1, "reference_index": 1, "prediction_index": 1,
         "state": "matched", "score": 0},
        {"source": "s2", "reference": "r2", "prediction": "",
         "source_index": 2, "reference_index": 2, "prediction_index": None,
         "state": "omission", "score": 0},
    ]
    blocks[0][long_side] = "word " * (tokens - 2)
    result = scorer._score_blocks(blocks, "en", "de", "test")
    removed = int(tokens > 510)
    assert result.score == pytest.approx((2 - removed) * 0.9 / (3 - removed))
    assert len(comet.calls) == 2 - removed
    assert result.null_alignment_ratio == pytest.approx(1 / 3)
    assert result.coverage["excluded_blocks"] == removed
    assert result.coverage["excluded_matched_block_percentage"] == 50 * removed
    assert result.coverage["sentences"]["source"]["excluded_percentage"] == pytest.approx(
        100 * removed / 3,
    )
    assert result.blocks[0]["score"] is None if removed else result.blocks[0]["score"] == 0.9


@pytest.mark.parametrize("scorer_class, config_class", [
    (AlignedCometScorer, AlignedCometConfig), (SentAlignCometScorer, SentAlignCometConfig),
])
def test_filtering_all_matched_blocks_returns_unscored_with_audit(scorer_class, config_class):
    comet = FakeComet()
    scorer = scorer_class(config_class(exclude_overlong_blocks=True, max_comet_tokens=2),
                          comet_scorer=comet)
    result = scorer._score_blocks([
        {"source": "s0", "reference": "r0", "prediction": "c0", "state": "matched",
         "source_index": 0, "reference_index": 0, "prediction_index": 0, "score": 0},
    ], "en", "de", "test")
    assert result.score is None
    assert result.coverage["score_status"] == "unscored_no_matched_blocks"
    assert result.coverage["sentences"]["reference"]["excluded_percentage"] == 100
    assert result.blocks[0]["exclusion_reason"] == "comet_token_limit"
    assert not comet.calls


def test_sentalign_filters_after_span_closure_and_retains_coverage():
    comet = FakeComet()
    scorer = SentAlignCometScorer(
        SentAlignCometConfig(exclude_overlong_blocks=True, max_comet_tokens=3),
        segmenter=FakeSegmenter(), comet_scorer=comet,
        aligner=FakeSentAlign(
            [((0, 1), (0,)), ((2,), (1,))],
            [((0, 1), (0,)), ((2,), (1,))],
        ),
    )
    result = scorer.score_document("s0 | s1", "c0 | c1", "r0 | r1 | r2")
    assert result.score == 0.9
    assert comet.calls == [("s1", "c1", "r2")]
    assert result.blocks[0]["reference_indices"] == [0, 1]
    assert result.coverage["sentences"]["reference"]["excluded_percentage"] == pytest.approx(
        200 / 3,
    )
    assert result.coverage["sentences"]["source"]["excluded_percentage"] == 50


def test_filtered_metric_dispatch_preserves_unscored_audit_without_zero_score():
    scorer, _ = make_scorer(exclude_overlong_blocks=True, max_comet_tokens=3)
    details = {}
    metrics = compute_translation_metrics(
        source="source A", reference="reference A", prediction="translation A",
        metric_names=["reference_assignment_comet"], aligned_comet_scorer=scorer,
        metric_details=details,
    )
    assert "reference_assignment_comet" not in metrics
    assert metrics["reference_assignment_comet_unscored"] == 1
    assert metrics["reference_assignment_comet_excluded_matched_block_percentage"] == 100
    assert details["reference_assignment_comet"]["score"] is None
    assert details["reference_assignment_comet"]["coverage"]["excluded_blocks"] == 1


def test_filtered_empty_candidate_is_unscored_but_not_counted_as_length_exclusion():
    scorer, comet = make_scorer(exclude_overlong_blocks=True)
    result = scorer.score_document(source="source A", reference="reference A", prediction="")
    assert result.score is None
    assert result.coverage["matched_blocks"] == result.coverage["excluded_blocks"] == 0
    assert result.coverage["excluded_matched_block_percentage"] is None
    assert result.coverage["sentences"]["reference"]["scored_percentage"] == 0
    assert result.null_alignment_ratio == 1
    assert not comet.calls


@pytest.mark.parametrize("metric_name", [
    "aligned_comet", "reference_assignment_comet", "sentalign_comet",
])
def test_metric_dispatch_preserves_alignment_details(metric_name):
    scorer, _ = make_scorer()
    details = {}
    metrics = compute_translation_metrics(
        source="source A",
        reference="reference A",
        prediction="translation A",
        metric_names=[metric_name],
        aligned_comet_scorer=scorer,
        sentalign_comet_scorer=scorer,
        source_language="en",
        target_language="de",
        metric_details=details,
    )
    assert metrics[metric_name] == pytest.approx(0.9)
    assert details[metric_name]["config"]["target_language"] == "de"
    assert details[metric_name]["blocks"][0]["token_counts"]["source"] == 4


@pytest.mark.parametrize("metric_name", ["reference_assignment_comet", "sentalign_comet"])
def test_named_metric_presets_load(metric_name, tmp_path):
    from chem_machine_translation.experiment.config import load_mapping_from_file

    config = evaluation_config_from_mapping(
        load_mapping_from_file(Path(f"config/evaluation/{metric_name}.toml")), base_dir=tmp_path,
    )
    assert config.metrics == (metric_name,)
    assert "sentalign_comet" not in DEFAULT_METRIC_NAMES
    assert config.sentalign_comet == SentAlignCometConfig()
    assert config.aligned_comet == AlignedCometConfig()


def test_evaluation_config_overrides_models_and_propagates_languages(tmp_path):
    config = evaluation_config_from_mapping(
        {
            "metrics": ["aligned_comet"],
            "aligned_comet": {
                "embedding_model": "custom-embedder",
                "comet_model": "custom-comet",
                "minimum_similarity": 0.4,
                "null_score": 0.2,
                "segmenter_models": {"de": "custom-segmenter"},
            },
        },
        base_dir=tmp_path,
    )
    assert config.aligned_comet.embedding_model == "custom-embedder"
    assert config.aligned_comet.comet_model == "custom-comet"
    assert config.aligned_comet.segmenter_models == {"de": "custom-segmenter"}
    scorer, _ = make_scorer()
    result = score_prediction_row(
        {
            "source_text": "source A",
            "ground_truth_translation": "reference A",
            "predicted_translation": "translation A",
            "source_language": "en",
            "target_language": "de",
        },
        evaluation=config,
        bertscore_scorer=None,
        bleurt_scorer=None,
        comet_scorer=None,
        cometkiwi_scorer=None,
        xcomet_scorer=None,
        mqm_judge=None,
        aligned_comet_scorer=scorer,
    )
    assert result["metrics"]["aligned_comet"] == pytest.approx(0.9)
    assert result["metric_details"]["aligned_comet"]["config"]["source_language"] == "en"


@pytest.mark.parametrize("metric_name, config_key", [
    ("reference_assignment_comet", "aligned_comet"), ("sentalign_comet", "sentalign_comet"),
])
@pytest.mark.parametrize("filtered", [False, True])
def test_filter_configuration_reaches_benchmark_and_only_batches_retained_blocks(
    tmp_path, metric_name, config_key, filtered,
):
    evaluation = evaluation_config_from_mapping({
        "metrics": [metric_name], config_key: {"exclude_overlong_blocks": filtered},
    }, base_dir=tmp_path)

    class BatchComet(FakeComet):
        def token_count(self, text):
            return 511 if text == "source A" else super().token_count(text)

        def score_many(self, blocks):
            assert [block["source"] for block in blocks] == ["source B"]
            return [self.score(block["source"], block["prediction"], block["reference"])
                    for block in blocks]

    comet = BatchComet()
    config = getattr(evaluation, config_key)
    assert config.exclude_overlong_blocks is filtered
    if metric_name == "reference_assignment_comet":
        scorer = AlignedCometScorer(config, segmenter=FakeSegmenter(),
                                    embedder=FakeEmbedder(), comet_scorer=comet)
    else:
        scorer = SentAlignCometScorer(
            config, segmenter=FakeSegmenter(), comet_scorer=comet,
            aligner=FakeSentAlign(
                [((0,), (0,)), ((1,), (1,))],
                [((0,), (0,)), ((1,), (1,)), ((), (2,))],
            ),
        )
    result = score_prediction_row({
        "source_text": "source A | source B",
        "ground_truth_translation": "reference A | reference B",
        "predicted_translation": "translation A | translation B | addition",
        "source_language": "en", "target_language": "de",
    }, evaluation=evaluation, bertscore_scorer=None, bleurt_scorer=None, comet_scorer=None,
        cometkiwi_scorer=None, xcomet_scorer=None, mqm_judge=None,
        aligned_comet_scorer=scorer, sentalign_comet_scorer=scorer)
    if not filtered:
        assert result["metrics"] == {}
        assert "token budget" in result["evaluation_error"]
        assert not comet.calls
        return
    assert not result.get("evaluation_error")
    assert comet.calls == [("source B", "translation B", "reference B")]
    assert result["metrics"][metric_name] == pytest.approx(0.45)
    assert result["metrics"][f"{metric_name}_excluded_matched_block_percentage"] == 50
    assert result["metrics"][f"{metric_name}_reference_scored_percentage"] == 50
    assert result["metric_details"][metric_name]["blocks"][0]["score"] is None
    assert result["metric_details"][metric_name]["blocks"][2]["state"] == "addition"


@pytest.mark.parametrize("language", ["en", "de", "es", "fr", "pt", "ru", "zh", "ja"])
def test_default_segmenter_needs_no_language_model_download(language):
    segmenter = SpacySentenceSegmenter({})
    assert segmenter.segment("First sentence. Second sentence.\nThird sentence.", language) == [
        "First sentence.",
        "Second sentence.",
        "Third sentence.",
    ]


def test_bundled_preset_loads_without_downloading_models(tmp_path):
    from chem_machine_translation.experiment.config import load_mapping_from_file

    config = evaluation_config_from_mapping(
        load_mapping_from_file(Path("config/evaluation/aligned_comet.toml")),
        base_dir=tmp_path,
    )
    assert config.metrics == ("aligned_comet",)
    assert config.aligned_comet == AlignedCometConfig()


@pytest.mark.parametrize("pooling", ["cls", "mean"])
def test_transformer_embedding_backend_is_lazy_and_does_not_truncate(monkeypatch, pooling):
    import torch
    import transformers

    calls = []

    class TokenBatch(dict):
        def to(self, device):
            return self

    class Tokenizer:
        model_max_length = 8

        def __call__(self, texts, **options):
            assert options["truncation"] is False
            tokens = [[1] * (len(text.split()) + 2) for text in texts]
            if "return_tensors" not in options:
                return {"input_ids": tokens}
            width = max(map(len, tokens))
            return TokenBatch(
                input_ids=torch.ones((len(tokens), width), dtype=torch.long),
                attention_mask=torch.ones((len(tokens), width), dtype=torch.long),
            )

    class Model:
        def eval(self):
            return self

        def to(self, device):
            return self

        def __call__(self, **inputs):
            shape = inputs["input_ids"].shape
            return SimpleNamespace(last_hidden_state=torch.ones((*shape, 3)))

    def load_model(name):
        calls.append(name)
        return Model()

    monkeypatch.setattr(transformers.AutoTokenizer, "from_pretrained", lambda name: Tokenizer())
    monkeypatch.setattr(transformers.AutoModel, "from_pretrained", load_model)
    embedder = TransformersSentenceEmbedder(
        AlignedCometConfig(
            embedding_model="custom-model",
            embedding_pooling=pooling,
            embedding_batch_size=1,
        )
    )
    assert calls == []
    assert embedder.encode(["short text", "another text"]) == [[1, 1, 1], [1, 1, 1]]
    assert calls == ["custom-model"]
    with pytest.raises(ValueError, match="embedding token budget"):
        embedder.encode(["word " * 10])
    assert calls == ["custom-model"]


def test_comet_wrapper_batches_all_matched_blocks_and_uses_encoder_budget():
    scorer = TokenCheckedCometScorer(model_name="custom-comet", batch_size=2)
    calls = []

    class Model:
        encoder = SimpleNamespace(
            max_positions=512,
            tokenizer=SimpleNamespace(encode=lambda text, **kwargs: [1, 2, 3]),
        )

        def requires_references(self):
            return True

        def predict(self, data, **options):
            calls.append((data, options))
            return SimpleNamespace(scores=[0.8] * len(data))

    scorer._model = Model()
    assert scorer.token_limit() == 510
    assert scorer.token_count("text") == 3
    blocks = [{"source": "source", "reference": "reference", "prediction": "prediction"}] * 2
    assert scorer.score_many(blocks) == [0.8, 0.8]
    assert len(calls) == 1
    assert calls[0][0][0] == {"src": "source", "ref": "reference", "mt": "prediction"}
    assert calls[0][1] == {"batch_size": 2, "gpus": 0}


@pytest.mark.parametrize(
    "options",
    [
        {"minimum_similarity": 1},
        {"null_score": float("nan")},
        {"embedding_batch_size": 0},
        {"max_comet_tokens": 0},
        {"embedding_pooling": "invalid"},
    ],
)
def test_invalid_config_is_rejected(options):
    with pytest.raises(ValueError):
        AlignedCometConfig(**options)
