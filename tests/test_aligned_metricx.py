from pathlib import Path
from types import SimpleNamespace

import pytest

from chem_machine_translation.evaluation.aligned_comet import AlignedCometConfig, AlignedCometResult
from chem_machine_translation.evaluation.aligned_metricx import (
    MetricXConfig,
    ReferenceAssignmentMetricXScorer,
    SentAlignMetricXScorer,
    TokenCheckedMetricXScorer,
    metricx_input,
)
from chem_machine_translation.evaluation.metrics import (
    DEFAULT_METRIC_NAMES,
    compute_translation_metrics,
    parse_metric_names,
)
from chem_machine_translation.experiment.config import evaluation_config_from_mapping
from chem_machine_translation.experiment.pipeline import score_prediction_row


class Segmenter:
    def segment(self, text, language):
        return [part.strip() for part in text.split("|") if part.strip()]


class Embedder:
    def encode(self, texts):
        return [[1, 0] if text.endswith("A") else [0, 1] for text in texts]


class MetricX:
    def __init__(self):
        self.calls = []

    def prepare(self, blocks):
        return [], [10] * len(blocks)

    def score_many(self, blocks):
        self.calls.extend(blocks)
        return [2.0] * len(blocks)


def test_reference_assignment_metricx_uses_native_error_scale_and_gap_penalty():
    backend = MetricX()
    scorer = ReferenceAssignmentMetricXScorer(
        segmenter=Segmenter(), embedder=Embedder(), metricx_scorer=backend,
    )
    result = scorer.score_document("s A | s B", "p A", "r A | r B")
    assert result.score == pytest.approx((2 + 25) / 2)
    assert result.null_alignment_ratio == 0.5
    assert result.config["score_direction"] == "lower_is_better"
    assert "comet_model" not in result.config
    assert result.blocks[0]["token_counts"] == {"combined_including_eos": 10}
    assert len(backend.calls) == 1


def test_sentalign_metricx_reuses_many_to_many_closure():
    class Aligner:
        def align(self, left, right):
            return SimpleNamespace(links=[SimpleNamespace(src=(0, 1), trg=(0,))])

    backend = MetricX()
    result = SentAlignMetricXScorer(
        segmenter=Segmenter(), aligner=Aligner(), metricx_scorer=backend,
    ).score_document("s", "p", "r A | r B")
    assert result.score == 2
    assert backend.calls[0]["reference"] == "r A r B"
    assert result.config["alignment"] == "sentalign_2_reference_span_closure"


class Tokenizer:
    eos_token_id = 1

    def __call__(self, texts, **kwargs):
        assert kwargs["truncation"] is False
        return {"input_ids": [[3] * len(text.split()) + [1] for text in texts]}


def test_metricx_budget_is_combined_and_eos_is_removed_only_after_validation():
    block = {"source": "s", "prediction": "p", "reference": "r"}
    assert metricx_input(block) == "source: s candidate: p reference: r"
    scorer = TokenCheckedMetricXScorer(MetricXConfig(max_input_tokens=7), tokenizer=Tokenizer())
    features, counts = scorer.prepare([block])
    assert counts == [7]
    assert features[0]["input_ids"] == [3] * 6
    with pytest.raises(ValueError, match="combined token budget exceeded"):
        scorer.score_many([block | {"prediction": "p extra"}])
    assert scorer._model is None


def test_long_input_extrapolation_requires_explicit_opt_in():
    with pytest.raises(ValueError, match="allow_long_inputs"):
        MetricXConfig(max_input_tokens=4096)
    assert MetricXConfig(max_input_tokens=4096, allow_long_inputs=True).max_input_tokens == 4096


@pytest.mark.parametrize("name", ["reference_assignment_metricx", "sentalign_metricx"])
def test_metricx_registry_is_opt_in_and_requires_source(name):
    assert parse_metric_names([name]) == (name,)
    assert name not in DEFAULT_METRIC_NAMES
    with pytest.raises(ValueError, match="requires source"):
        compute_translation_metrics(prediction="p", reference="r", metric_names=[name])


class DocumentScorer:
    def score_document(self, **kwargs):
        assert kwargs["source_language"] == "en"
        assert kwargs["target_language"] == "de"
        return AlignedCometResult(
            score=3.0, null_alignment_ratio=0.25, blocks=(),
            config={"score_direction": "lower_is_better"},
        )


def test_pipeline_preserves_both_metricx_scores_and_direction_metadata(tmp_path):
    evaluation = evaluation_config_from_mapping({
        "metrics": ["reference_assignment_metricx", "sentalign_metricx"],
        "metricx": {"batch_size": 2, "null_score": 24.0},
        "reference_assignment_comet": {"minimum_similarity": 0.6},
        "sentalign_comet": {"max_concatenations": 1},
    }, base_dir=tmp_path)
    assert evaluation.metricx.batch_size == 2
    assert evaluation.metricx.null_score == 24
    assert evaluation.aligned_comet.minimum_similarity == 0.6
    assert evaluation.sentalign_comet.max_concatenations == 1
    result = score_prediction_row(
        {"source_text": "s", "ground_truth_translation": "r", "predicted_translation": "p",
         "source_language": "en", "target_language": "de"},
        evaluation=evaluation, bertscore_scorer=None, bleurt_scorer=None,
        comet_scorer=None, cometkiwi_scorer=None, xcomet_scorer=None, mqm_judge=None,
        reference_assignment_metricx_scorer=DocumentScorer(),
        sentalign_metricx_scorer=DocumentScorer(),
    )
    for name in evaluation.metrics:
        assert result["metrics"][name] == 3
        assert result["metrics"][name + "_null_alignment_ratio"] == 0.25
        assert result["metric_details"][name]["config"]["score_direction"] == "lower_is_better"


def test_metricx_matches_official_decoder_logit_computation_on_tiny_mt5():
    import torch
    from transformers import BatchEncoding, MT5Config, MT5ForConditionalGeneration

    class PaddingTokenizer(Tokenizer):
        def pad(self, features, **kwargs):
            maximum = max(len(item["input_ids"]) for item in features)
            return BatchEncoding({
                name: torch.tensor([item[name] + [0] * (maximum - len(item[name]))
                                    for item in features])
                for name in ("input_ids", "attention_mask")
            })

    model = MT5ForConditionalGeneration(MT5Config(
        vocab_size=250100, d_model=8, d_ff=16, d_kv=4, num_heads=2,
        num_layers=1, num_decoder_layers=1, dropout_rate=0,
        decoder_start_token_id=0, pad_token_id=0, eos_token_id=1,
    )).eval()
    tokenizer = PaddingTokenizer()
    scorer = TokenCheckedMetricXScorer(
        MetricXConfig(batch_size=2), tokenizer=tokenizer, model=model,
    )
    blocks = [{"source": "s", "prediction": "p", "reference": "r"},
              {"source": "s extra", "prediction": "p", "reference": "r"}]
    features, _ = scorer.prepare(blocks)
    batch = tokenizer.pad(features)
    with torch.inference_mode():
        encoded = model.encoder(**batch, return_dict=True)
        decoded = model.decoder(
            input_ids=torch.zeros((2, 1), dtype=torch.long),
            encoder_hidden_states=encoded.last_hidden_state,
            encoder_attention_mask=batch["attention_mask"],
            use_cache=False, return_dict=True,
        )
        expected = model.lm_head(decoded.last_hidden_state)[:, 0, 250089].clamp(0, 25)
    assert scorer.score_many(blocks) == pytest.approx(expected.tolist(), abs=1e-6)


@pytest.mark.parametrize("bad_score", [float("nan"), float("inf"), -1.0, 26.0])
def test_metricx_rejects_invalid_backend_scores(bad_score):
    class BadMetricX(MetricX):
        def score_many(self, blocks):
            return [bad_score] * len(blocks)

    with pytest.raises(ValueError, match="invalid segment scores"):
        ReferenceAssignmentMetricXScorer(
            segmenter=Segmenter(), embedder=Embedder(), metricx_scorer=BadMetricX(),
        ).score_document("s A", "p A", "r A")


def test_empty_candidate_receives_gap_penalty_without_loading_metricx():
    class UnusedMetricX:
        def prepare(self, blocks):
            raise AssertionError("Gap-only documents must not load a model or tokenizer.")

    result = ReferenceAssignmentMetricXScorer(
        segmenter=Segmenter(), embedder=Embedder(), metricx_scorer=UnusedMetricX(),
    ).score_document("s A", "", "r A")
    assert result.score == 25
    assert result.null_alignment_ratio == 1


def test_sentalign_checks_combined_budget_after_merging_before_model_load():
    class Aligner:
        def align(self, left, right):
            return SimpleNamespace(links=[SimpleNamespace(src=(0, 1), trg=(0,))])

    backend = TokenCheckedMetricXScorer(
        MetricXConfig(max_input_tokens=9), tokenizer=Tokenizer(),
    )
    with pytest.raises(ValueError, match="combined token budget exceeded"):
        SentAlignMetricXScorer(
            segmenter=Segmenter(), aligner=Aligner(), metricx_scorer=backend,
        ).score_document("s", "p", "r A | r B")
    assert backend._model is None


def test_metricx_does_not_inherit_the_comet_per_text_token_guard():
    result = ReferenceAssignmentMetricXScorer(
        alignment_config=AlignedCometConfig(max_comet_tokens=1),
        segmenter=Segmenter(), embedder=Embedder(), metricx_scorer=MetricX(),
    ).score_document("s A", "p A", "r A")
    assert result.score == 2
    assert "max_comet_tokens" not in result.config


def test_metricx_preset_loads_both_opt_in_metrics(tmp_path):
    preset = Path(__file__).resolve().parents[1] / "config/evaluation/aligned_metricx.toml"
    evaluation = evaluation_config_from_mapping({"config": str(preset)}, base_dir=tmp_path)
    assert evaluation.metrics == ("reference_assignment_metricx", "sentalign_metricx")
    assert evaluation.metricx.max_input_tokens == 1536
    assert evaluation.metricx.model == "google/metricx-24-hybrid-xl-v2p6"
    assert evaluation.metricx.null_score == 25


@pytest.mark.parametrize("marker", ["<extra_id_10>", "\u2581<extra_id_10>"])
def test_tokenizer_validation_uses_numeric_regression_index(monkeypatch, marker):
    from transformers import AutoTokenizer

    class SentencePieceTokenizer(Tokenizer):
        def convert_ids_to_tokens(self, index):
            assert index == 250089
            return marker

        def convert_tokens_to_ids(self, token):
            raise AssertionError("Literal lookup is not reliable for mT5 SentencePiece markers.")

    monkeypatch.setattr(AutoTokenizer, "from_pretrained", lambda model: SentencePieceTokenizer())
    backend = TokenCheckedMetricXScorer()
    features, counts = backend.prepare([{"source": "s", "reference": "r", "prediction": "p"}])
    assert counts == [7]
    assert len(features[0]["input_ids"]) == 6


def test_incompatible_tokenizer_mapping_is_rejected(monkeypatch):
    from transformers import AutoTokenizer

    tokenizer = SimpleNamespace(convert_ids_to_tokens=lambda index: "incorrect")
    monkeypatch.setattr(AutoTokenizer, "from_pretrained", lambda model: tokenizer)
    backend = TokenCheckedMetricXScorer()
    with pytest.raises(ValueError, match="official mT5 extra-token mapping"):
        backend._load_tokenizer()
    assert backend._tokenizer is None


def test_empty_backend_batch_does_not_load_tokenizer_or_weights():
    backend = TokenCheckedMetricXScorer()
    assert backend.score_many([]) == []
    assert backend._tokenizer is None
    assert backend._model is None