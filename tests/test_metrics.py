import pytest

from chem_machine_translation.evaluation.metrics import (
    DEFAULT_METRIC_NAMES,
    compute_translation_metrics,
    parse_metric_names,
)


class _FakeCometScorer:
    def __init__(self) -> None:
        self.calls = []

    def score(self, source: str, prediction: str, reference: str) -> float:
        self.calls.append((source, prediction, reference))
        return 0.87


def test_parse_metric_names_defaults_to_all_general_metrics() -> None:
    assert parse_metric_names(None) == DEFAULT_METRIC_NAMES


def test_parse_metric_names_rejects_unknown_metric() -> None:
    with pytest.raises(ValueError, match="Unsupported metrics"):
        parse_metric_names(["bleu", "unknown"])


def test_compute_translation_metrics_can_select_overlap_metrics_only() -> None:
    metrics = compute_translation_metrics(
        prediction="solid electrolyte battery",
        reference="solid electrolyte battery",
        metric_names=["sequence_similarity", "bleu", "chrf"],
    )

    assert set(metrics) == {"sequence_similarity", "bleu", "chrf"}
    assert metrics["sequence_similarity"] == 100
    assert metrics["bleu"] > 0
    assert metrics["chrf"] > 0


def test_compute_translation_metrics_adds_comet_with_source_text() -> None:
    scorer = _FakeCometScorer()

    metrics = compute_translation_metrics(
        prediction="Batterie mit Festelektrolyt",
        reference="Festelektrolytbatterie",
        source="solid electrolyte battery",
        metric_names=["comet"],
        comet_scorer=scorer,
    )

    assert metrics == {"comet": 0.87}
    assert scorer.calls == [
        (
            "solid electrolyte battery",
            "Batterie mit Festelektrolyt",
            "Festelektrolytbatterie",
        )
    ]


def test_compute_translation_metrics_requires_source_for_comet() -> None:
    with pytest.raises(ValueError, match="requires source"):
        compute_translation_metrics(
            prediction="translation",
            reference="reference",
            metric_names=["comet"],
            comet_scorer=_FakeCometScorer(),
        )
