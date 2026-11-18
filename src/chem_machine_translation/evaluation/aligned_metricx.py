from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any

from chem_machine_translation.evaluation.aligned_comet import (
    AlignedCometResult,
    AlignedCometScorer,
    SentAlignCometScorer,
)


@dataclass(frozen=True)
class MetricXConfig:
    model: str = "google/metricx-24-hybrid-xl-v2p6"
    tokenizer: str = "google/mt5-xl"
    device: str = "cpu"
    dtype: str = "auto"
    batch_size: int = 1
    max_input_tokens: int = 1536
    null_score: float = 25.0
    allow_long_inputs: bool = False

    def __post_init__(self):
        if not self.model.strip() or not self.tokenizer.strip() or not self.device.strip():
            raise ValueError("MetricX model, tokenizer, and device must not be empty.")
        if self.dtype not in {"auto", "float32", "float16", "bfloat16"}:
            raise ValueError("Unsupported MetricX dtype.")
        if self.batch_size <= 0 or self.max_input_tokens <= 1:
            raise ValueError("MetricX batch size and input budget must be positive.")
        if self.max_input_tokens > 1536 and not self.allow_long_inputs:
            raise ValueError("MetricX budgets above 1536 require allow_long_inputs=true.")
        if not math.isfinite(self.null_score) or not 0 <= self.null_score <= 25:
            raise ValueError("MetricX null_score must be between 0 and 25.")


def metricx_input(block):
    return (f"source: {block['source']} candidate: {block['prediction']} "
            f"reference: {block['reference']}")


class TokenCheckedMetricXScorer:
    def __init__(self, config=None, *, tokenizer=None, model=None):
        self.config = config or MetricXConfig()
        self._tokenizer = tokenizer
        self._model = model

    def _load_tokenizer(self):
        if self._tokenizer is None:
            from transformers import AutoTokenizer

            tokenizer = AutoTokenizer.from_pretrained(self.config.tokenizer)
            regression_token = tokenizer.convert_ids_to_tokens(250089)
            if regression_token not in {"<extra_id_10>", "\u2581<extra_id_10>"}:
                raise ValueError("MetricX requires the official mT5 extra-token mapping.")
            self._tokenizer = tokenizer
        return self._tokenizer

    def prepare(self, blocks):
        if not blocks:
            return [], []
        tokenizer = self._load_tokenizer()
        encoded = tokenizer(
            [metricx_input(block) for block in blocks],
            add_special_tokens=True, truncation=False, padding=False,
        )
        features, counts = [], []
        for token_ids in encoded["input_ids"]:
            count = len(token_ids)
            if count > self.config.max_input_tokens:
                raise ValueError(
                    f"Aligned MetricX combined token budget exceeded "
                    f"({self.config.max_input_tokens} tokens): {count}. "
                    "Inputs were not truncated."
                )
            if not token_ids or token_ids[-1] != tokenizer.eos_token_id:
                raise ValueError("MetricX tokenizer must append an EOS token.")
            counts.append(count)
            features.append({"input_ids": token_ids[:-1],
                             "attention_mask": [1] * (count - 1)})
        return features, counts

    def _load_model(self):
        if self._model is None:
            import torch
            from transformers import MT5ForConditionalGeneration

            dtype = self.config.dtype
            model = MT5ForConditionalGeneration.from_pretrained(
                self.config.model,
                torch_dtype="auto" if dtype == "auto" else getattr(torch, dtype),
            )
            if model.config.model_type != "mt5" or model.config.vocab_size <= 250089:
                raise ValueError("MetricX-24 requires the mT5 regression checkpoint architecture.")
            self._model = model.eval().to(self.config.device)
        return self._model

    def score_many(self, blocks):
        import torch

        features, _ = self.prepare(blocks)
        if not features:
            return []
        model = self._load_model()
        tokenizer = self._load_tokenizer()
        scores = []
        for start in range(0, len(features), self.config.batch_size):
            batch = tokenizer.pad(
                features[start:start + self.config.batch_size],
                padding=True, return_tensors="pt",
            ).to(self.config.device)
            with torch.inference_mode():
                output = model(
                    **batch,
                    decoder_input_ids=torch.zeros(
                        (batch["input_ids"].shape[0], 1), dtype=torch.long,
                        device=self.config.device,
                    ),
                    use_cache=False, return_dict=True,
                )
                scores.extend(output.logits[:, 0, 250089].clamp(0, 25).float().cpu().tolist())
        return scores


class _MetricXBlockScoring:
    metricx_config: MetricXConfig
    metricx: Any

    def _score_blocks(self, blocks, source_language, target_language, alignment):
        matched = [block for block in blocks if block["state"] == "matched"]
        for block in blocks:
            block["score"] = self.metricx_config.null_score
        if matched:
            _, counts = self.metricx.prepare(matched)
            for block, count in zip(matched, counts, strict=True):
                block["token_counts"] = {"combined_including_eos": count}
            scores = self.metricx.score_many(matched)
            if len(scores) != len(matched) or not all(
                math.isfinite(score) and 0 <= score <= 25 for score in scores
            ):
                raise ValueError("Aligned MetricX returned invalid segment scores.")
            for block, score in zip(matched, scores, strict=True):
                block["score"] = float(score)
        settings = {key: value for key, value in asdict(self.config).items()
                    if not key.startswith("comet_") and key != "max_comet_tokens"}
        settings.update({
            "metricx": asdict(self.metricx_config), "null_score": self.metricx_config.null_score,
            "alignment": alignment, "aggregation": "equal_block_mean",
            "score_direction": "lower_is_better", "score_range": [0, 25],
            "regression_logit_index": 250089,
            "source_language": source_language, "target_language": target_language,
        })
        return AlignedCometResult(
            score=sum(block["score"] for block in blocks) / len(blocks),
            null_alignment_ratio=1 - len(matched) / len(blocks),
            blocks=tuple(blocks), config=settings,
        )


class ReferenceAssignmentMetricXScorer(_MetricXBlockScoring, AlignedCometScorer):
    def __init__(self, config=None, *, alignment_config=None, metricx_scorer=None, **kwargs):
        self.metricx_config = config or MetricXConfig()
        self.metricx = metricx_scorer or TokenCheckedMetricXScorer(self.metricx_config)
        super().__init__(config=alignment_config, **kwargs)


class SentAlignMetricXScorer(_MetricXBlockScoring, SentAlignCometScorer):
    def __init__(self, config=None, *, alignment_config=None, metricx_scorer=None, **kwargs):
        self.metricx_config = config or MetricXConfig()
        self.metricx = metricx_scorer or TokenCheckedMetricXScorer(self.metricx_config)
        super().__init__(config=alignment_config, **kwargs)