from __future__ import annotations

from difflib import SequenceMatcher
from typing import Protocol

try:
    from sacrebleu.metrics import BLEU, CHRF
except ImportError:  # pragma: no cover - dependency is included for normal uv installs
    BLEU = None
    CHRF = None

GENERAL_METRIC_NAMES = ("sequence_similarity", "bleu", "chrf", "chrf2++", "comet")
DEFAULT_METRIC_NAMES = ("sequence_similarity", "bleu", "chrf2++", "comet")
COMET_DEFAULT_MODEL = "Unbabel/wmt22-comet-da"


class CometScorer(Protocol):
    def score(self, source: str, prediction: str, reference: str) -> float:
        """Return a segment-level COMET score."""


class UnbabelCometScorer:
    """Lazy wrapper around the official unbabel-comet package."""

    def __init__(
        self,
        model_name: str = COMET_DEFAULT_MODEL,
        batch_size: int = 8,
        gpus: int = 0,
    ) -> None:
        self.model_name = model_name
        self.batch_size = batch_size
        self.gpus = gpus
        self._model = None

    def score(self, source: str, prediction: str, reference: str) -> float:
        model = self._load_model()
        result = model.predict(
            [{"src": source, "mt": prediction, "ref": reference}],
            batch_size=self.batch_size,
            gpus=self.gpus,
        )
        return float(result.scores[0])

    def _load_model(self):
        if self._model is None:
            try:
                from comet import download_model, load_from_checkpoint
            except ImportError as exc:  # pragma: no cover - depends on optional install
                raise RuntimeError(
                    "COMET metric requested but unbabel-comet or one of its dependencies "
                    f"could not be imported: {exc}. Install dependencies with `uv sync` "
                    "or select metrics explicitly, "
                    "for example `--metric sequence_similarity --metric bleu --metric chrf2++`."
                ) from exc

            model_path = download_model(self.model_name)
            self._model = load_from_checkpoint(model_path)
        return self._model


def parse_metric_names(metric_names: list[str] | tuple[str, ...] | None) -> tuple[str, ...]:
    if not metric_names:
        return DEFAULT_METRIC_NAMES

    normalized = tuple(metric_name.strip().lower() for metric_name in metric_names)
    unknown = sorted(set(normalized) - set(GENERAL_METRIC_NAMES))
    if unknown:
        allowed = ", ".join(GENERAL_METRIC_NAMES)
        raise ValueError(f"Unsupported metrics {unknown}. Use one or more of: {allowed}")
    return normalized


def compute_translation_metrics(
    prediction: str,
    reference: str,
    source: str | None = None,
    metric_names: list[str] | tuple[str, ...] | None = None,
    comet_scorer: CometScorer | None = None,
) -> dict[str, float]:
    selected_metrics = parse_metric_names(metric_names)
    metrics: dict[str, float] = {}

    if "sequence_similarity" in selected_metrics:
        metrics["sequence_similarity"] = SequenceMatcher(None, prediction, reference).ratio() * 100

    if "bleu" in selected_metrics and BLEU:
        metrics["bleu"] = BLEU(effective_order=True).sentence_score(
            prediction,
            [reference],
        ).score

    if "chrf" in selected_metrics and CHRF:
        metrics["chrf"] = CHRF().sentence_score(prediction, [reference]).score

    if "chrf2++" in selected_metrics and CHRF:
        metrics["chrf2++"] = CHRF(
            char_order=6,
            word_order=2,
        ).sentence_score(prediction, [reference]).score

    if "comet" in selected_metrics:
        if source is None:
            raise ValueError("COMET metric requires source text.")
        scorer = comet_scorer or UnbabelCometScorer()
        metrics["comet"] = scorer.score(
            source=source,
            prediction=prediction,
            reference=reference,
        )

    return metrics
