import pytest

from chem_machine_translation.evaluation.metrics import (
    DEFAULT_METRIC_NAMES,
    MqmJudgeResult,
    compute_corpus_overlap_metrics,
    compute_terminology_success_rate,
    compute_translation_metrics,
    parse_metric_names,
    parse_mqm_judge_response,
)


class _FakeCometScorer:
    def __init__(self) -> None:
        self.calls = []

    def score(self, source: str, prediction: str, reference: str) -> float:
        self.calls.append((source, prediction, reference))
        return 0.87


class _FakeMqmJudge:
    def __init__(self) -> None:
        self.calls = []

    def score(self, source: str, prediction: str, reference: str) -> MqmJudgeResult:
        self.calls.append((source, prediction, reference))
        return MqmJudgeResult(
            quality_score=82.0,
            error_score=3.0,
            minor_errors=1,
            major_errors=1,
            critical_errors=0,
        )


def test_parse_metric_names_defaults_to_all_general_metrics() -> None:
    assert parse_metric_names(None) == DEFAULT_METRIC_NAMES
    assert "chrf2++" in DEFAULT_METRIC_NAMES
    assert "chrf" not in DEFAULT_METRIC_NAMES
    assert "terminology_success_rate" in DEFAULT_METRIC_NAMES
    assert "fsp_mqm" not in DEFAULT_METRIC_NAMES


def test_parse_metric_names_rejects_unknown_metric() -> None:
    with pytest.raises(ValueError, match="Unsupported metrics"):
        parse_metric_names(["bleu", "unknown"])


def test_compute_translation_metrics_can_select_overlap_metrics_only() -> None:
    metrics = compute_translation_metrics(
        prediction="solid electrolyte battery",
        reference="solid electrolyte battery",
        metric_names=["sequence_similarity", "bleu", "chrf", "chrf2++"],
    )

    assert set(metrics) == {"sequence_similarity", "bleu", "chrf", "chrf2++"}
    assert metrics["sequence_similarity"] == 100
    assert metrics["bleu"] > 0
    assert metrics["chrf"] > 0
    assert metrics["chrf2++"] > 0


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


def test_compute_terminology_success_rate_matches_manifest_target_terms() -> None:
    terminology = [
        {
            "source_term": "gastrointestinal tract",
            "target_terms": ["tube digestif", "tractus gastro-intestinal"],
            "decision": "keep_both",
        },
        {
            "source_term": "phosphate-binder(s)",
            "target_terms": ["chélateurs du phosphate"],
            "decision": "keep_reference",
        },
    ]

    score = compute_terminology_success_rate(
        prediction="Le tube digestif contient un autre terme.",
        terminology=terminology,
    )

    assert score == 50


def test_compute_terminology_success_rate_uses_wmt_style_applicability_and_counts() -> None:
    terminology = [
        {
            "source_term": "fatty acid",
            "target_terms": ["acide gras"],
            "decision": "keep_reference",
        },
        {
            "source_term": "water soluble polymer",
            "target_terms": ["polymère soluble dans l'eau"],
            "decision": "keep_reference",
        },
        {
            "source_term": "not in source",
            "target_terms": ["absent"],
            "decision": "keep_reference",
        },
    ]

    score = compute_terminology_success_rate(
        prediction="acide gras est répété: acide gras.",
        source="fatty acid and fatty acid in a water soluble polymer",
        reference="acide gras et polymère soluble dans l'eau",
        terminology=terminology,
    )

    assert score == 50


def test_compute_terminology_success_rate_skips_terms_absent_from_reference() -> None:
    terminology = [
        {
            "source_term": "external variant",
            "target_terms": ["variante externe"],
            "decision": "keep_external",
        }
    ]

    assert (
        compute_terminology_success_rate(
            prediction="variante externe",
            source="external variant",
            reference="autre traduction",
            terminology=terminology,
        )
        is None
    )


def test_compute_terminology_success_rate_handles_preserve_and_drop_terms() -> None:
    terminology = [
        {
            "source_term": "C18:0",
            "target_terms": [],
            "decision": "preserve",
        },
        {
            "source_term": "generic term",
            "target_terms": ["terme générique"],
            "decision": "drop",
        },
    ]

    score = compute_terminology_success_rate(
        prediction="La chaîne C18:0 est préservée.",
        terminology=terminology,
    )

    assert score == 100


def test_compute_terminology_success_rate_returns_none_without_terms() -> None:
    assert compute_terminology_success_rate("translation", []) is None
    assert compute_terminology_success_rate("translation", [{"decision": "drop"}]) is None


def test_compute_translation_metrics_can_select_terminology_success_rate() -> None:
    metrics = compute_translation_metrics(
        prediction="Le tube digestif est mentionné.",
        reference="Le tube digestif est mentionné.",
        metric_names=["terminology_success_rate"],
        terminology=[
            {
                "source_term": "gastrointestinal tract",
                "target_terms": ["tube digestif"],
                "decision": "keep_reference",
            }
        ],
    )

    assert metrics == {"terminology_success_rate": 100}


def test_compute_translation_metrics_omits_terminology_score_without_terms() -> None:
    metrics = compute_translation_metrics(
        prediction="translation",
        reference="reference",
        metric_names=["terminology_success_rate"],
        terminology=[],
    )

    assert metrics == {}


def test_compute_corpus_overlap_metrics_uses_corpus_level_sacrebleu() -> None:
    metrics = compute_corpus_overlap_metrics(
        predictions=[
            "solid electrolyte battery contains stable ceramic particles",
            "aqueous solution includes dissolved phosphate binder molecules",
        ],
        references=[
            "solid electrolyte battery contains stable ceramic particles",
            "aqueous solution includes dissolved phosphate binder molecules",
        ],
        metric_names=["bleu", "chrf", "chrf2++"],
    )

    assert set(metrics) == {"bleu", "chrf", "chrf2++"}
    assert metrics["bleu"] > 0
    assert metrics["chrf"] > 0
    assert metrics["chrf2++"] > 0


def test_parse_mqm_judge_response_counts_severity_weighted_errors() -> None:
    result = parse_mqm_judge_response(
        """
        {
          "quality_score": 73,
          "errors": [
            {"severity": "minor", "category": "style", "description": "awkward"},
            {"severity": "major", "category": "terminology", "description": "wrong term"},
            {"severity": "critical", "category": "chemistry", "description": "wrong formula"}
          ]
        }
        """
    )

    assert result == MqmJudgeResult(
        quality_score=73.0,
        error_score=8.0,
        minor_errors=1,
        major_errors=1,
        critical_errors=1,
    )


def test_compute_translation_metrics_can_select_fsp_mqm() -> None:
    judge = _FakeMqmJudge()

    metrics = compute_translation_metrics(
        prediction="Batterie mit Festelektrolyt",
        reference="Festelektrolytbatterie",
        source="solid electrolyte battery",
        metric_names=["fsp_mqm"],
        mqm_judge=judge,
    )

    assert metrics == {
        "fsp_mqm": 82.0,
        "fsp_mqm_error_score": 3.0,
        "fsp_mqm_minor_errors": 1,
        "fsp_mqm_major_errors": 1,
        "fsp_mqm_critical_errors": 0,
    }
    assert judge.calls == [
        (
            "solid electrolyte battery",
            "Batterie mit Festelektrolyt",
            "Festelektrolytbatterie",
        )
    ]


def test_compute_translation_metrics_requires_source_and_judge_for_fsp_mqm() -> None:
    with pytest.raises(ValueError, match="requires source"):
        compute_translation_metrics(
            prediction="translation",
            reference="reference",
            metric_names=["fsp_mqm"],
            mqm_judge=_FakeMqmJudge(),
        )

    with pytest.raises(ValueError, match="requires an MQM judge"):
        compute_translation_metrics(
            prediction="translation",
            reference="reference",
            source="source",
            metric_names=["fsp_mqm"],
        )
