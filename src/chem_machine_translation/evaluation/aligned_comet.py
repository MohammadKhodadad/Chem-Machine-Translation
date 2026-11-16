from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from typing import Any

from chem_machine_translation.evaluation.metrics import COMET_DEFAULT_MODEL, UnbabelCometScorer


@dataclass(frozen=True)
class AlignedCometConfig:
    embedding_model: str = "BAAI/bge-m3"
    embedding_device: str = "cpu"
    embedding_batch_size: int = 8
    embedding_max_tokens: int = 8192
    embedding_pooling: str = "cls"
    segmenter_models: dict[str, str] = field(default_factory=dict)
    comet_model: str = COMET_DEFAULT_MODEL
    comet_batch_size: int = 8
    comet_gpus: int = 0
    minimum_similarity: float = 0.5
    null_score: float = 0.0
    max_comet_tokens: int = 510
    max_sentences: int = 1000

    def __post_init__(self) -> None:
        if not self.embedding_model.strip() or not self.comet_model.strip():
            raise ValueError("Aligned COMET model names must not be empty.")
        if self.embedding_pooling not in {"cls", "mean"}:
            raise ValueError("Aligned COMET embedding_pooling must be cls or mean.")
        if not math.isfinite(self.minimum_similarity) or not -1 < self.minimum_similarity < 1:
            raise ValueError("Aligned COMET minimum_similarity must be between -1 and 1.")
        if not math.isfinite(self.null_score):
            raise ValueError("Aligned COMET null_score must be finite.")
        for name in (
            "embedding_batch_size",
            "embedding_max_tokens",
            "comet_batch_size",
            "max_comet_tokens",
            "max_sentences",
        ):
            if getattr(self, name) <= 0:
                raise ValueError(f"Aligned COMET {name} must be positive.")
        if self.comet_gpus < 0:
            raise ValueError("Aligned COMET comet_gpus must be nonnegative.")


class SpacySentenceSegmenter:
    def __init__(self, models: dict[str, str]) -> None:
        self.models = dict(models)
        self._pipelines: dict[str, Any] = {}

    def segment(self, text: str, language: str) -> list[str]:
        if not text.strip():
            return []
        if language not in self._pipelines:
            import spacy

            if language in self.models:
                pipeline = spacy.load(self.models[language])
                if not any(pipeline.has_pipe(name) for name in ("parser", "senter", "sentencizer")):
                    pipeline.add_pipe("sentencizer")
            else:
                pipeline = spacy.blank("xx")
                pipeline.add_pipe("sentencizer")
            self._pipelines[language] = pipeline
        pipeline = self._pipelines[language]
        sentences = []
        for paragraph in text.splitlines():
            if paragraph.strip():
                sentences.extend(
                    sentence.text.strip()
                    for sentence in pipeline(paragraph).sents
                    if sentence.text.strip()
                )
        return sentences


class TransformersSentenceEmbedder:
    def __init__(self, config: AlignedCometConfig) -> None:
        self.config = config
        self._model: Any = None
        self._tokenizer: Any = None

    def encode(self, texts: list[str]) -> list[list[float]]:
        import torch
        from transformers import AutoModel, AutoTokenizer

        if self._model is None:
            self._tokenizer = AutoTokenizer.from_pretrained(self.config.embedding_model)
            self._model = AutoModel.from_pretrained(self.config.embedding_model)
            self._model.eval().to(self.config.embedding_device)
        tokenizer_limit = self._tokenizer.model_max_length
        limit = min(self.config.embedding_max_tokens, tokenizer_limit)
        encoded = self._tokenizer(texts, truncation=False, add_special_tokens=True)
        if any(len(tokens) > limit for tokens in encoded["input_ids"]):
            raise ValueError(f"Aligned COMET embedding token budget exceeded ({limit} tokens).")
        vectors = []
        for start in range(0, len(texts), self.config.embedding_batch_size):
            inputs = self._tokenizer(
                texts[start : start + self.config.embedding_batch_size],
                truncation=False,
                padding=True,
                return_tensors="pt",
            ).to(self.config.embedding_device)
            with torch.inference_mode():
                hidden = self._model(**inputs).last_hidden_state
                if self.config.embedding_pooling == "mean":
                    mask = inputs["attention_mask"].unsqueeze(-1)
                    pooled = (hidden * mask).sum(1) / mask.sum(1).clamp_min(1)
                else:
                    pooled = hidden[:, 0]
                vectors.extend(pooled.float().cpu().tolist())
        return vectors


class TokenCheckedCometScorer(UnbabelCometScorer):
    def token_count(self, text: str) -> int:
        tokenizer = self._load_model().encoder.tokenizer
        return len(tokenizer.encode(text, add_special_tokens=True, truncation=False))

    def token_limit(self) -> int:
        return int(self._load_model().encoder.max_positions) - 2

    def score_many(self, blocks: list[dict[str, Any]]) -> list[float]:
        model = self._load_model()
        if not model.requires_references():
            raise ValueError("Aligned COMET requires a reference-based COMET checkpoint.")
        result = model.predict(
            [
                {"src": block["source"], "ref": block["reference"], "mt": block["prediction"]}
                for block in blocks
            ],
            batch_size=self.batch_size,
            gpus=self.gpus,
        )
        return [float(score) for score in result.scores]


@dataclass(frozen=True)
class AlignedCometResult:
    score: float
    null_alignment_ratio: float
    blocks: tuple[dict[str, Any], ...]
    config: dict[str, Any]


def pair_sentences(left: list[Any], right: list[Any], minimum_similarity: float):
    import numpy as np
    from scipy.optimize import linear_sum_assignment

    if not left or not right:
        return {}, set(range(len(left))), set(range(len(right)))
    left_vectors, right_vectors = np.asarray(left, dtype=float), np.asarray(right, dtype=float)
    for vectors in (left_vectors, right_vectors):
        if vectors.ndim != 2 or not np.isfinite(vectors).all():
            raise ValueError("Aligned COMET embeddings must be finite two-dimensional arrays.")
        if np.any(np.linalg.norm(vectors, axis=1) == 0):
            raise ValueError("Aligned COMET embeddings must have nonzero norms.")
    similarities = (left_vectors / np.linalg.norm(left_vectors, axis=1, keepdims=True)) @ (
        right_vectors / np.linalg.norm(right_vectors, axis=1, keepdims=True)
    ).T
    left_count, right_count = similarities.shape
    costs = np.zeros((left_count + right_count, left_count + right_count))
    gap_cost = (1 - minimum_similarity) / 2
    costs[:left_count, :right_count] = np.where(
        similarities > minimum_similarity,
        1 - similarities,
        4.0,
    )
    costs[:left_count, right_count:] = gap_cost
    costs[left_count:, :right_count] = gap_cost
    row_indices, column_indices = linear_sum_assignment(costs)
    pairs = {
        int(row): int(column)
        for row, column in zip(row_indices, column_indices, strict=True)
        if row < left_count and column < right_count
    }
    return (
        pairs,
        set(range(left_count)) - pairs.keys(),
        set(range(right_count)) - set(pairs.values()),
    )


class AlignedCometScorer:
    """Reference-anchored one-to-one sentence assignment followed by COMET."""

    def __init__(
        self,
        config: AlignedCometConfig | None = None,
        *,
        segmenter: Any = None,
        embedder: Any = None,
        comet_scorer: Any = None,
    ) -> None:
        self.config = config or AlignedCometConfig()
        self.segmenter = segmenter or SpacySentenceSegmenter(self.config.segmenter_models)
        self.embedder = embedder or TransformersSentenceEmbedder(self.config)
        self.comet = comet_scorer or TokenCheckedCometScorer(
            self.config.comet_model,
            self.config.comet_batch_size,
            self.config.comet_gpus,
        )

    def score_document(
        self,
        source: str,
        prediction: str,
        reference: str,
        source_language: str = "xx",
        target_language: str = "xx",
    ) -> AlignedCometResult:
        sources = self.segmenter.segment(source, source_language)
        references = self.segmenter.segment(reference, target_language)
        predictions = self.segmenter.segment(prediction, target_language)
        if not sources or not references:
            raise ValueError("Aligned COMET requires nonempty source and reference text.")
        if max(len(sources), len(references), len(predictions)) > self.config.max_sentences:
            raise ValueError("Aligned COMET max_sentences exceeded; split the document explicitly.")
        texts = list(dict.fromkeys(sources + references + predictions))
        embeddings = self.embedder.encode(texts)
        if len(embeddings) != len(texts):
            raise ValueError("Aligned COMET embedder returned the wrong number of vectors.")
        vectors = dict(zip(texts, embeddings, strict=True))
        reference_vectors = [vectors[text] for text in references]
        source_pairs, _, unused_sources = pair_sentences(
            reference_vectors,
            [vectors[text] for text in sources],
            self.config.minimum_similarity,
        )
        target_pairs, _, unused_targets = pair_sentences(
            reference_vectors,
            [vectors[text] for text in predictions],
            self.config.minimum_similarity,
        )
        blocks = []
        for index, reference_text in enumerate(references):
            source_index, target_index = source_pairs.get(index), target_pairs.get(index)
            blocks.append(
                {
                    "source": sources[source_index] if source_index is not None else "",
                    "reference": reference_text,
                    "prediction": predictions[target_index] if target_index is not None else "",
                    "source_index": source_index,
                    "reference_index": index,
                    "prediction_index": target_index,
                    "state": "source_unmatched"
                    if source_index is None
                    else ("omission" if target_index is None else "matched"),
                    "score": self.config.null_score,
                }
            )
        for index in sorted(unused_targets):
            blocks.append(
                {
                    "source": "",
                    "reference": "",
                    "prediction": predictions[index],
                    "source_index": None,
                    "reference_index": None,
                    "prediction_index": index,
                    "state": "addition",
                    "score": self.config.null_score,
                }
            )
        for index in sorted(unused_sources):
            blocks.append(
                {
                    "source": sources[index],
                    "reference": "",
                    "prediction": "",
                    "source_index": index,
                    "reference_index": None,
                    "prediction_index": None,
                    "state": "source_only",
                    "score": self.config.null_score,
                }
            )
        return self._score_blocks(
            blocks, source_language, target_language, "reference_anchored_linear_assignment"
        )

    def _score_blocks(self, blocks, source_language, target_language, alignment):
        matched = [block for block in blocks if block["state"] == "matched"]
        if matched:
            limit = min(self.config.max_comet_tokens, self.comet.token_limit())
            for block in matched:
                counts = {
                    name: self.comet.token_count(block[name])
                    for name in ("source", "reference", "prediction")
                }
                block["token_counts"] = counts
                if max(counts.values()) > limit:
                    raise ValueError(
                        f"Aligned COMET token budget exceeded ({limit} tokens): {counts}. "
                        "Split the long sentences explicitly; inputs were not truncated."
                    )
            if hasattr(self.comet, "score_many"):
                scores = self.comet.score_many(matched)
            else:
                scores = [
                    self.comet.score(block["source"], block["prediction"], block["reference"])
                    for block in matched
                ]
            if len(scores) != len(matched) or not all(math.isfinite(score) for score in scores):
                raise ValueError("Aligned COMET returned invalid segment scores.")
            for block, score in zip(matched, scores, strict=True):
                block["score"] = float(score)
        return AlignedCometResult(
            score=sum(block["score"] for block in blocks) / len(blocks),
            null_alignment_ratio=1 - len(matched) / len(blocks),
            blocks=tuple(blocks),
            config={
                **asdict(self.config),
                "alignment": alignment,
                "aggregation": "equal_block_mean",
                "source_language": source_language,
                "target_language": target_language,
            },
        )


@dataclass(frozen=True)
class SentAlignCometConfig:
    alignment_model: str = "BAAI/bge-m3"
    alignment_pooling: str = "cls"
    alignment_device: str = "cpu"
    alignment_batch_size: int = 8
    alignment_max_tokens: int = 8192
    alignment_cache: str | None = None
    max_concatenations: int = 4
    score_cutoff: float = 0.4
    segmenter_models: dict[str, str] = field(default_factory=dict)
    comet_model: str = COMET_DEFAULT_MODEL
    comet_batch_size: int = 8
    comet_gpus: int = 0
    null_score: float = 0.0
    max_comet_tokens: int = 510
    max_sentences: int = 1000

    def __post_init__(self):
        if not self.alignment_model.strip() or not self.comet_model.strip():
            raise ValueError("SentAlign COMET model names must not be empty.")
        if self.alignment_pooling not in {"cls", "mean", "pooler"}:
            raise ValueError("SentAlign alignment_pooling must be cls, mean, or pooler.")
        if not 1 <= self.max_concatenations <= 15:
            raise ValueError("SentAlign max_concatenations must be between 1 and 15.")
        if not math.isfinite(self.score_cutoff) or not 0 <= self.score_cutoff <= 1:
            raise ValueError("SentAlign score_cutoff must be between 0 and 1.")
        if not math.isfinite(self.null_score):
            raise ValueError("SentAlign null_score must be finite.")
        if self.comet_gpus < 0:
            raise ValueError("SentAlign comet_gpus must be nonnegative.")
        for name in (
            "alignment_batch_size", "alignment_max_tokens", "comet_batch_size",
            "max_comet_tokens", "max_sentences",
        ):
            if getattr(self, name) <= 0:
                raise ValueError(f"SentAlign {name} must be positive.")


class SentAlignCometScorer(AlignedCometScorer):
    """Official SentAlign 2 matching with reference-span closure and checked COMET."""

    def __init__(self, config=None, *, segmenter=None, aligner=None, comet_scorer=None):
        self.config = config or SentAlignCometConfig()
        self.segmenter = segmenter or SpacySentenceSegmenter(self.config.segmenter_models)
        self.aligner = aligner
        self.comet = comet_scorer or TokenCheckedCometScorer(
            self.config.comet_model, self.config.comet_batch_size, self.config.comet_gpus
        )

    def _align(self, left, right):
        if not right:
            links = [((index,), ()) for index in range(len(left))]
            self._alignment_audits.append({"links": links, "skipped_empty_target": True})
            return links
        if self.aligner is None:
            try:
                from sentalign import SentAlign
            except ImportError as exc:
                raise RuntimeError(
                    "sentalign_comet requires the optional sentalign dependency. "
                    "Install the project's sentalign extra."
                ) from exc
            self.aligner = SentAlign(
                encoder=self.config.alignment_model,
                pooling=self.config.alignment_pooling,
                device=self.config.alignment_device,
                batch_size=self.config.alignment_batch_size,
                max_tokens=self.config.alignment_max_tokens,
                embedding_cache=self.config.alignment_cache,
                max_concatenations=self.config.max_concatenations,
                score_cutoff=self.config.score_cutoff,
                compat="none", half=False, num_proc=1,
            )
        alignment = self.aligner.align(left, right)
        links = [(tuple(link.src), tuple(link.trg)) for link in alignment.links]
        self._alignment_audits.append({
            "links": [
                {"src": list(link.src), "trg": list(link.trg),
                 "score": getattr(link, "score", None)} for link in alignment.links
            ],
            "info": getattr(alignment, "info", {}),
            "anchors": getattr(alignment, "anchors", []),
        })
        if any(not ref and not span for ref, span in links):
            raise ValueError("SentAlign returned an empty alignment link.")
        for side, count in ((0, len(left)), (1, len(right))):
            indices = [index for link in links for index in link[side]]
            if sorted(indices) != list(range(count)):
                raise ValueError(
                    "SentAlign must cover each sentence exactly once, including nulls."
                )
            for link in links:
                span = link[side]
                if span and span != tuple(range(span[0], span[-1] + 1)):
                    raise ValueError("SentAlign returned a noncontiguous sentence span.")
        return links

    def score_document(
        self, source, prediction, reference, source_language="xx", target_language="xx"
    ):
        sources = self.segmenter.segment(source, source_language)
        references = self.segmenter.segment(reference, target_language)
        predictions = self.segmenter.segment(prediction, target_language)
        if not sources or not references:
            raise ValueError("SentAlign COMET requires nonempty source and reference text.")
        if max(map(len, (sources, references, predictions))) > self.config.max_sentences:
            raise ValueError("SentAlign COMET max_sentences exceeded.")
        self._alignment_audits = []
        source_links = self._align(references, sources)
        target_links = self._align(references, predictions)
        parents = list(range(len(references)))

        def root(index):
            while parents[index] != index:
                parents[index] = parents[parents[index]]
                index = parents[index]
            return index

        for reference_indices, _ in source_links + target_links:
            for index in reference_indices[1:]:
                parents[root(index)] = root(reference_indices[0])
        groups = {}
        for index in range(len(references)):
            groups.setdefault(root(index), []).append(index)
        blocks = []

        def append_block(source_indices, reference_indices, prediction_indices):
            state = (
                "addition" if not reference_indices and prediction_indices else
                "source_only" if not reference_indices else
                "source_unmatched" if not source_indices else
                "omission" if not prediction_indices else "matched"
            )
            blocks.append({
                "source": " ".join(sources[index] for index in source_indices),
                "reference": " ".join(references[index] for index in reference_indices),
                "prediction": " ".join(predictions[index] for index in prediction_indices),
                "source_indices": list(source_indices),
                "reference_indices": list(reference_indices),
                "prediction_indices": list(prediction_indices),
                "state": state, "score": self.config.null_score,
            })

        for reference_indices in groups.values():
            reference_set = set(reference_indices)
            source_indices = sorted(
                index for ref, span in source_links if reference_set.intersection(ref)
                for index in span
            )
            prediction_indices = sorted(
                index for ref, span in target_links if reference_set.intersection(ref)
                for index in span
            )
            append_block(source_indices, reference_indices, prediction_indices)
            blocks[-1]["source_null_reference_indices"] = [
                index for ref, span in source_links if not span for index in ref
                if index in reference_set
            ]
            blocks[-1]["candidate_null_reference_indices"] = [
                index for ref, span in target_links if not span for index in ref
                if index in reference_set
            ]
        for reference_indices, span in target_links:
            if not reference_indices:
                append_block([], [], span)
        for reference_indices, span in source_links:
            if not reference_indices:
                append_block(span, [], [])
        result = self._score_blocks(
            blocks, source_language, target_language, "sentalign_2_reference_span_closure"
        )
        from importlib.metadata import PackageNotFoundError, version

        try:
            package_version = version("sentalign")
        except PackageNotFoundError:
            package_version = None
        backend_config = getattr(self.aligner, "config", None)

        return AlignedCometResult(
            result.score, result.null_alignment_ratio, result.blocks,
            {**result.config, "sentalign_version": package_version,
             "compat": "none",
             "alignment_inputs_may_truncate": True,
             "source_alignment": self._alignment_audits[0],
             "candidate_alignment": self._alignment_audits[1],
             "backend_config": backend_config.to_dict() if backend_config is not None else None},
        )
