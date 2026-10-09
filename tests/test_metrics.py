from types import SimpleNamespace

import pytest

from chem_machine_translation.evaluation.metrics import (
    BertScoreResult,
    DEFAULT_METRIC_NAMES,
    DEFAULT_TERMINOLOGY_TERM_GROUPS,
    GENERAL_METRIC_NAMES,
    TERMINOLOGY_TERM_GROUPS,
    MqmJudgeResult,
    UnbabelCometScorer,
    UnbabelXCometScorer,
    XCometResult,
    compute_corpus_overlap_metrics,
    compute_target_term_coverage,
    compute_terminology_success_rate,
    compute_translation_metrics,
    compute_variant_aware_target_term_coverage,
    compute_variant_aware_terminology_success_rate,
    mqm_judge_system_prompt,
    normalize_mqm_domain,
    parse_metric_names,
    parse_mqm_judge_response,
    select_terminology_terms,
    terminology_term_group,
)


class _FakeCometScorer:
    def __init__(self) -> None:
        self.calls = []

    def score(self, source: str, prediction: str, reference: str) -> float:
        self.calls.append((source, prediction, reference))
        return 0.87


class _FakeBertScoreScorer:
    def __init__(self) -> None:
        self.calls = []

    def score(self, prediction: str, reference: str) -> BertScoreResult:
        self.calls.append((prediction, reference))
        return BertScoreResult(precision=0.91, recall=0.83, f1=0.87)


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


class _FakeCometKiwiScorer:
    def __init__(self) -> None:
        self.calls = []

    def score(self, source: str, prediction: str, reference: str | None = None) -> float:
        self.calls.append((source, prediction, reference))
        return 0.76


class _FakeXCometScorer:
    def __init__(self) -> None:
        self.calls = []

    def score(self, source: str, prediction: str, reference: str) -> XCometResult:
        self.calls.append((source, prediction, reference))
        return XCometResult(
            score=0.81,
            error_spans=(
                {"text": "wrong term", "start": 2, "end": 12, "severity": "major"},
                {"text": "unit", "start": 20, "end": 24, "severity": "minor"},
            ),
        )


class _FakeCometModel:
    def __init__(self, result: object) -> None:
        self.result = result
        self.calls = []

    def predict(self, payload: list[dict[str, str]], **kwargs: object) -> object:
        self.calls.append((payload, kwargs))
        return self.result


def test_parse_metric_names_defaults_to_all_general_metrics() -> None:
    assert DEFAULT_METRIC_NAMES == GENERAL_METRIC_NAMES
    assert parse_metric_names(None) == GENERAL_METRIC_NAMES
    assert "chrf2++" in DEFAULT_METRIC_NAMES
    assert "chrf" in DEFAULT_METRIC_NAMES
    assert "target_term_coverage" in DEFAULT_METRIC_NAMES
    assert "terminology_success_rate" in DEFAULT_METRIC_NAMES
    assert "fsp_mqm" in DEFAULT_METRIC_NAMES
    assert DEFAULT_TERMINOLOGY_TERM_GROUPS == ("verified",)
    assert set(TERMINOLOGY_TERM_GROUPS) == {"llm", "algorithmic", "verified", "refined"}


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


def test_compute_translation_metrics_adds_bertscore_components() -> None:
    scorer = _FakeBertScoreScorer()

    metrics = compute_translation_metrics(
        prediction="Batterie mit Festelektrolyt",
        reference="Festelektrolytbatterie",
        metric_names=["bertscore"],
        bertscore_scorer=scorer,
    )

    assert metrics == {
        "bertscore": 0.87,
        "bertscore_precision": 0.91,
        "bertscore_recall": 0.83,
    }
    assert scorer.calls == [("Batterie mit Festelektrolyt", "Festelektrolytbatterie")]


def test_compute_translation_metrics_adds_term_bertscore_recall() -> None:
    scorer = _FakeBertScoreScorer()
    metric_details = {}

    metrics = compute_translation_metrics(
        prediction="Le tube digestif est traité avec un chélateur.",
        reference="Le tube digestif reçoit des chélateurs du phosphate.",
        terminology=[
            {
                "target_terms": ["tube digestif"],
                "term_group": "refined",
                "decision": "keep_reference",
            },
            {
                "target_terms": ["chélateurs du phosphate"],
                "term_group": "refined",
                "decision": "keep_reference",
            },
            {
                "target_terms": ["term absent"],
                "term_group": "refined",
                "decision": "keep_reference",
            },
        ],
        terminology_term_groups=("refined",),
        metric_names=["term_bertscore_recall"],
        bertscore_scorer=scorer,
        metric_details=metric_details,
    )

    assert metrics == {
        "term_bertscore_recall": 0.83,
        "term_bertscore_reference_term_count": 2.0,
    }
    assert scorer.calls == [
        (
            "Le tube digestif est traité avec un chélateur.",
            "tube digestif; chélateurs du phosphate",
        )
    ]
    assert metric_details == {
        "term_bertscore_reference_terms": [
            "tube digestif",
            "chélateurs du phosphate",
        ]
    }


def test_compute_translation_metrics_skips_term_bertscore_without_reference_terms() -> None:
    scorer = _FakeBertScoreScorer()

    metrics = compute_translation_metrics(
        prediction="candidate",
        reference="reference",
        terminology=[
            {
                "target_terms": ["term absent"],
                "term_group": "refined",
                "decision": "keep_reference",
            }
        ],
        terminology_term_groups=("refined",),
        metric_names=["term_bertscore_recall"],
        bertscore_scorer=scorer,
    )

    assert metrics == {}
    assert scorer.calls == []


def test_compute_translation_metrics_requires_source_for_comet() -> None:
    with pytest.raises(ValueError, match="requires source"):
        compute_translation_metrics(
            prediction="translation",
            reference="reference",
            metric_names=["comet"],
            comet_scorer=_FakeCometScorer(),
        )


def test_compute_translation_metrics_adds_reference_free_cometkiwi_qe() -> None:
    scorer = _FakeCometKiwiScorer()

    metrics = compute_translation_metrics(
        prediction="Batterie mit Festelektrolyt",
        reference="Festelektrolytbatterie",
        source="solid electrolyte battery",
        metric_names=["cometkiwi_qe"],
        cometkiwi_scorer=scorer,
    )

    assert metrics == {"cometkiwi_qe": 0.76}
    assert scorer.calls == [("solid electrolyte battery", "Batterie mit Festelektrolyt", None)]


def test_compute_translation_metrics_keeps_xcomet_error_spans() -> None:
    scorer = _FakeXCometScorer()
    metric_details = {}

    metrics = compute_translation_metrics(
        prediction="Batterie mit falschem Begriff und Einheit",
        reference="Festelektrolytbatterie",
        source="solid electrolyte battery",
        metric_names=["xcomet_xl"],
        xcomet_scorer=scorer,
        metric_details=metric_details,
    )

    assert metrics == {
        "xcomet_xl": 0.81,
        "xcomet_xl_minor_error_spans": 1.0,
        "xcomet_xl_major_error_spans": 1.0,
        "xcomet_xl_critical_error_spans": 0.0,
    }
    assert scorer.calls == [
        (
            "solid electrolyte battery",
            "Batterie mit falschem Begriff und Einheit",
            "Festelektrolytbatterie",
        )
    ]
    assert metric_details["xcomet_xl_error_spans"] == [
        {"text": "wrong term", "start": 2, "end": 12, "severity": "major"},
        {"text": "unit", "start": 20, "end": 24, "severity": "minor"},
    ]


def test_unbabel_comet_scorers_use_expected_payloads_and_preserve_spans() -> None:
    kiwi_model = _FakeCometModel(SimpleNamespace(scores=[0.73]))
    kiwi_scorer = UnbabelCometScorer(model_name="fake-kiwi", batch_size=3, gpus=0)
    kiwi_scorer._model = kiwi_model

    assert kiwi_scorer.score("source", "translation") == 0.73
    assert kiwi_model.calls == [([{"src": "source", "mt": "translation"}], {"batch_size": 3, "gpus": 0})]

    xcomet_model = _FakeCometModel(
        SimpleNamespace(
            scores=[0.84],
            metadata=SimpleNamespace(
                error_spans=[[{"text": "error", "start": 0, "end": 5, "severity": "critical"}]]
            ),
        )
    )
    xcomet_scorer = UnbabelXCometScorer(model_name="fake-xcomet", batch_size=2, gpus=1)
    xcomet_scorer._model = xcomet_model

    assert xcomet_scorer.score("source", "translation", "reference") == XCometResult(
        score=0.84,
        error_spans=(
            {"text": "error", "start": 0, "end": 5, "severity": "critical"},
        ),
    )
    assert xcomet_model.calls == [
        (
            [{"src": "source", "mt": "translation", "ref": "reference"}],
            {"batch_size": 2, "gpus": 1},
        )
    ]


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


def test_select_terminology_terms_filters_verification_and_deduplicates() -> None:
    terminology = [
        {
            "term_group": "algorithmic",
            "target_terms": ["common term"],
            "decision": "keep_reference",
            "verified_by": [],
        },
        {
            "term_group": "verified",
            "target_terms": ["verified term"],
            "decision": "keep_reference",
            "verified_by": ["local_iate"],
        },
        {
            "term_group": "refined",
            "target_terms": ["verified term"],
            "decision": "keep_refined",
            "verified_by": ["local_iate"],
        },
        {
            "term_group": "refined",
            "target_terms": ["unverified refined term"],
            "decision": "keep_refined",
            "verified_by": [],
        },
    ]

    all_terms = select_terminology_terms(
        terminology,
        term_groups=("algorithmic", "verified", "refined"),
    )
    verified_terms = select_terminology_terms(
        terminology,
        term_groups=("verified",),
        require_verified=True,
    )
    verified_refined_terms = select_terminology_terms(
        terminology,
        term_groups=("refined",),
        require_verified=True,
    )

    assert [term["target_terms"][0] for term in all_terms] == [
        "common term",
        "verified term",
        "unverified refined term",
    ]
    assert all_terms[1]["term_group"] == "refined"
    assert [term["target_terms"][0] for term in verified_terms] == ["verified term"]
    assert [term["target_terms"][0] for term in verified_refined_terms] == ["verified term"]


def test_variant_aware_terminology_success_rate_accepts_external_candidate_variants() -> None:
    terminology = [
        {
            "source_term": "European Economic Community",
            "target_terms": ["Communauté économique européenne"],
            "external_candidates": {"local_iate": ["CEE", "Communauté économique européenne"]},
            "decision": "keep_reference",
        }
    ]

    assert compute_terminology_success_rate(
        prediction="La CEE agit.",
        terminology=terminology,
    ) == 0
    assert compute_variant_aware_terminology_success_rate(
        prediction="La CEE agit.",
        terminology=terminology,
    ) == 100


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


def test_compute_target_term_coverage_counts_reference_target_terms() -> None:
    terminology = [
        {
            "source_term": "",
            "target_terms": ["acide gras"],
            "decision": "keep_reference",
        },
        {
            "source_term": "",
            "target_terms": ["polymère soluble dans l'eau"],
            "decision": "keep_reference",
        },
        {
            "source_term": "",
            "target_terms": ["terme absent"],
            "decision": "keep_reference",
        },
    ]

    score = compute_target_term_coverage(
        prediction="acide gras est répété: acide gras.",
        reference="acide gras et polymère soluble dans l'eau",
        terminology=terminology,
    )

    assert score == 50


def test_variant_aware_target_term_coverage_accepts_external_candidate_variants() -> None:
    terminology = [
        {
            "target_terms": ["European Economic Community"],
            "candidates": {
                "local_iate": ["EEC", "European Economic Community"],
                "wikidata": ["European Common Market", "ECM"],
            },
            "term_group": "verified",
            "decision": "keep_reference",
        }
    ]

    assert compute_target_term_coverage(
        prediction="The EEC acts.",
        reference="The European Economic Community acts.",
        terminology=terminology,
    ) == 0
    assert compute_variant_aware_target_term_coverage(
        prediction="The EEC acts.",
        reference="The European Economic Community acts.",
        terminology=terminology,
    ) == 100


def test_target_term_coverage_defaults_to_verified_terms() -> None:
    terminology = [
        {
            "target_terms": ["acide gras"],
            "term_group": "verified",
            "decision": "keep_reference",
        },
        {
            "target_terms": ["polymère"],
            "term_group": "llm",
            "decision": "keep_reference",
        },
        {
            "target_terms": ["25 °C"],
            "term_group": "algorithmic",
            "decision": "keep_reference",
        },
    ]

    score = compute_target_term_coverage(
        prediction="acide gras",
        reference="acide gras polymère 25 °C",
        terminology=terminology,
    )

    assert score == 100


def test_target_term_coverage_can_select_multiple_term_groups() -> None:
    terminology = [
        {
            "target_terms": ["acide gras"],
            "term_group": "verified",
            "decision": "keep_reference",
        },
        {
            "target_terms": ["polymère"],
            "term_group": "llm",
            "decision": "keep_reference",
        },
        {
            "target_terms": ["25 °C"],
            "term_group": "algorithmic",
            "decision": "keep_reference",
        },
    ]

    score = compute_target_term_coverage(
        prediction="acide gras polymère",
        reference="acide gras polymère 25 °C",
        terminology=terminology,
        term_groups=("verified", "llm"),
    )

    assert score == 100


def test_compute_translation_metrics_passes_terminology_term_groups() -> None:
    metrics = compute_translation_metrics(
        prediction="polymère",
        reference="acide gras polymère",
        metric_names=["target_term_coverage"],
        terminology=[
            {
                "target_terms": ["acide gras"],
                "term_group": "verified",
                "decision": "keep_reference",
            },
            {
                "target_terms": ["polymère"],
                "term_group": "llm",
                "decision": "keep_reference",
            },
        ],
        terminology_term_groups=("llm",),
    )

    assert metrics == {"target_term_coverage": 100}


def test_terminology_term_group_infers_legacy_terms() -> None:
    assert terminology_term_group({"external_candidates": {"iate": ["glycérides"]}}) == "verified"
    assert terminology_term_group({"source": "llm_target"}) == "llm"
    assert terminology_term_group({"source": "regex"}) == "algorithmic"
    assert terminology_term_group({"target_terms": ["legacy"]}) == "verified"


def test_compute_target_term_coverage_uses_reference_occurrence_counts() -> None:
    terminology = [
        {
            "target_terms": ["acide gras"],
            "decision": "keep_reference",
        }
    ]

    score = compute_target_term_coverage(
        prediction="acide gras.",
        reference="acide gras et acide gras.",
        terminology=terminology,
    )

    assert score == 50


def test_compute_target_term_coverage_ignores_drop_terms_and_absent_reference_terms() -> None:
    terminology = [
        {
            "target_terms": ["terme générique"],
            "decision": "drop",
        },
        {
            "target_terms": ["absent de la référence"],
            "decision": "keep_reference",
        },
    ]

    assert (
        compute_target_term_coverage(
            prediction="terme générique",
            reference="référence sans terme",
            terminology=terminology,
        )
        is None
    )


def test_compute_translation_metrics_can_select_target_term_coverage() -> None:
    metrics = compute_translation_metrics(
        prediction="Le tube digestif est mentionné.",
        reference="Le tube digestif est mentionné.",
        metric_names=["target_term_coverage"],
        terminology=[
            {
                "source_term": "",
                "target_terms": ["tube digestif"],
                "decision": "keep_reference",
            }
        ],
    )

    assert metrics == {"target_term_coverage": 100}


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


def test_mqm_judge_prompts_select_the_legal_domain() -> None:
    assert normalize_mqm_domain("jrc") == "legal"
    assert normalize_mqm_domain("eurolex") == "legal"
    assert normalize_mqm_domain("chemistry") == "chemistry"
    assert "legal effect" in mqm_judge_system_prompt("legal")
    assert "chemical formulas" in mqm_judge_system_prompt("chemistry")


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
