from __future__ import annotations

from difflib import SequenceMatcher

try:
    from sacrebleu.metrics import BLEU, CHRF
except ImportError:  # pragma: no cover - dependency is included for normal uv installs
    BLEU = None
    CHRF = None


def compute_translation_metrics(prediction: str, reference: str) -> dict[str, float]:
    metrics = {
        "sequence_similarity": SequenceMatcher(None, prediction, reference).ratio() * 100,
    }

    if BLEU and CHRF:
        metrics["bleu"] = BLEU(effective_order=True).sentence_score(
            prediction,
            [reference],
        ).score
        metrics["chrf"] = CHRF().sentence_score(prediction, [reference]).score

    return metrics
