from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any, Protocol

try:
    from sacrebleu.metrics import BLEU, CHRF
except ImportError:  # pragma: no cover - dependency is included for normal uv installs
    BLEU = None
    CHRF = None

GENERAL_METRIC_NAMES = (
    "sequence_similarity",
    "bleu",
    "chrf",
    "chrf2++",
    "bertscore",
    "bleurt",
    "term_bertscore_recall",
    "comet",
    "cometkiwi_qe",
    "xcomet_xl",
    "terminology_success_rate",
    "variant_aware_terminology_success_rate",
    "target_term_coverage",
    "variant_aware_target_term_coverage",
    "fsp_mqm",
)
DEFAULT_METRIC_NAMES = tuple(metric for metric in GENERAL_METRIC_NAMES if metric != "bleurt")
TERMINOLOGY_TERM_GROUPS = ("llm", "algorithmic", "verified", "refined")
DEFAULT_TERMINOLOGY_TERM_GROUPS = ("verified",)
COMET_DEFAULT_MODEL = "Unbabel/wmt22-comet-da"
COMETKIWI_DEFAULT_MODEL = "Unbabel/wmt22-cometkiwi-da"
XCOMET_XL_DEFAULT_MODEL = "Unbabel/XCOMET-XL"
BERTSCORE_DEFAULT_MODEL = "xlm-roberta-large"
MQM_DEFAULT_MODEL = "gpt-4.1-mini"
_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)
_MQM_SEVERITY_WEIGHTS = {"minor": 1, "major": 2, "critical": 5}

CHEMISTRY_MQM_JUDGE_SYSTEM_PROMPT = """You are an MQM-style evaluator for chemistry and patent machine
translation.

Evaluate the candidate translation against the source and reference. Focus on meaning preservation,
terminology, chemical formulas, identifiers, units, numbers, omissions, hallucinations, and target
language fluency. Penalize terminology and scientific meaning errors more strongly than harmless
wording differences.

Use these severities:
- minor: local wording or style issue that does not change scientific/legal meaning;
- major: mistranslation, omission, wrong terminology, unit/number issue, or fluency issue that
  changes or obscures meaning;
- critical: dangerous scientific/legal error, severe hallucination, wrong chemical identity,
  corrupted formula/identifier, or contradiction of the source.

Return only valid JSON with this shape:
{
  "quality_score": 0.0,
  "errors": [
    {
      "severity": "minor|major|critical",
      "category": "accuracy|terminology|chemistry|number_unit|omission|addition|fluency|style",
      "description": "short explanation"
    }
  ]
}

`quality_score` must be from 0 to 100, where 100 is a perfect translation. If there are no errors,
return an empty `errors` list.
"""

LEGAL_MQM_JUDGE_SYSTEM_PROMPT = """You are an MQM-style evaluator for legal and regulatory machine
translation.

Evaluate the candidate translation against the source and reference. Focus on preservation of legal
effect, terminology, defined terms, obligations, prohibitions, permissions, conditions, exceptions,
scope, institutional names, citations, dates, numbers, omissions, hallucinations, and target-language
fluency. Penalize errors that change rights, duties, legal scope, or a referenced instrument more
strongly than harmless wording differences.

Use these severities:
- minor: local wording or style issue that does not change legal meaning;
- major: mistranslation, omission, wrong terminology, reference/date/number issue, or fluency issue
    that changes or obscures legal meaning;
- critical: a change to a right, duty, prohibition, permission, condition, exception, legal scope, or
    institutional/legal identity that could materially alter the legal effect.

Return only valid JSON with this shape:
{
    "quality_score": 0.0,
    "errors": [
        {
            "severity": "minor|major|critical",
            "category": "accuracy|terminology|legal_effect|reference|number_date|omission|addition|fluency|style",
            "description": "short explanation"
        }
    ]
}

`quality_score` must be from 0 to 100, where 100 is a perfect translation. If there are no errors,
return an empty `errors` list.
"""


class CometScorer(Protocol):
    def score(self, source: str, prediction: str, reference: str) -> float:
        """Return a segment-level COMET score."""


@dataclass(frozen=True)
class BertScoreResult:
    precision: float
    recall: float
    f1: float


class BertScoreScorer(Protocol):
    def score(self, prediction: str, reference: str) -> BertScoreResult:
        """Return segment-level BERTScore precision, recall, and F1."""


class BleurtScorer(Protocol):
    def score(self, prediction: str, reference: str) -> float:
        """Return a segment-level BLEURT score."""


class CometQeScorer(Protocol):
    def score(self, source: str, prediction: str, reference: str | None = None) -> float:
        """Return a segment-level reference-free COMET QE score."""


@dataclass(frozen=True)
class XCometResult:
    score: float
    error_spans: tuple[dict[str, Any], ...]


class XCometScorer(Protocol):
    def score(self, source: str, prediction: str, reference: str) -> XCometResult:
        """Return an XCOMET score and its target-side error spans."""


@dataclass(frozen=True)
class MqmJudgeResult:
    quality_score: float
    error_score: float
    minor_errors: int = 0
    major_errors: int = 0
    critical_errors: int = 0


class MqmJudge(Protocol):
    def score(self, source: str, prediction: str, reference: str) -> MqmJudgeResult:
        """Return MQM-style quality and error scores."""


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

    def score(self, source: str, prediction: str, reference: str | None = None) -> float:
        model = self._load_model()
        payload = {"src": source, "mt": prediction}
        if reference is not None:
            payload["ref"] = reference
        result = model.predict(
            [payload],
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


class HuggingFaceBertScoreScorer:
    """Lazy wrapper around bert-score with a multilingual encoder default."""

    def __init__(
        self,
        model_name: str = BERTSCORE_DEFAULT_MODEL,
        batch_size: int = 8,
        device: str | None = None,
    ) -> None:
        self.model_name = model_name
        self.batch_size = batch_size
        self.device = device

    def score(self, prediction: str, reference: str) -> BertScoreResult:
        try:
            from bert_score import score as bert_score
        except ImportError as exc:  # pragma: no cover - depends on optional install
            raise RuntimeError(
                "BERTScore metric requested but bert-score could not be imported. "
                "Install dependencies with `uv sync` or select metrics explicitly."
            ) from exc

        options: dict[str, Any] = {
            "cands": [prediction],
            "refs": [reference],
            "model_type": self.model_name,
            "batch_size": self.batch_size,
            "verbose": False,
        }
        if self.device is not None:
            options["device"] = self.device
        precision, recall, f1 = bert_score(**options)
        return BertScoreResult(
            precision=float(precision[0]),
            recall=float(recall[0]),
            f1=float(f1[0]),
        )


class OfficialBleurtScorer:
    """Lazy wrapper around the official BLEURT checkpoint scorer."""

    def __init__(self, checkpoint: str) -> None:
        if not checkpoint:
            raise ValueError(
                "BLEURT metric requires a local checkpoint. Set `bleurt_checkpoint` or pass "
                "`--bleurt-checkpoint`."
            )
        self.checkpoint = checkpoint
        self._scorer = None

    def score(self, prediction: str, reference: str) -> float:
        scores = self._load_scorer().score(
            references=[reference],
            candidates=[prediction],
        )
        return float(scores[0])

    def _load_scorer(self):
        if self._scorer is None:
            try:
                from bleurt import score  # type: ignore[reportMissingImports]
            except ImportError as exc:  # pragma: no cover - depends on optional install
                raise RuntimeError(
                    "BLEURT metric requested but the optional BLEURT package could not be imported. "
                    "Install it with `uv sync --extra bleurt`."
                ) from exc
            self._scorer = score.BleurtScorer(self.checkpoint)
        return self._scorer


class UnbabelXCometScorer(UnbabelCometScorer):
    """XCOMET wrapper that retains target-side MQM-style error spans."""

    def score(self, source: str, prediction: str, reference: str) -> XCometResult:
        model = self._load_model()
        result = model.predict(
            [{"src": source, "mt": prediction, "ref": reference}],
            batch_size=self.batch_size,
            gpus=self.gpus,
        )
        return XCometResult(
            score=float(result.scores[0]),
            error_spans=extract_xcomet_error_spans(result),
        )


def extract_xcomet_error_spans(result: Any) -> tuple[dict[str, Any], ...]:
    metadata = getattr(result, "metadata", None)
    raw_spans = getattr(metadata, "error_spans", ())
    if not isinstance(raw_spans, (list, tuple)):
        return ()
    spans = raw_spans[0] if raw_spans and isinstance(raw_spans[0], (list, tuple)) else raw_spans
    return tuple(dict(span) for span in spans if isinstance(span, dict))


def xcomet_severity_counts(error_spans: tuple[dict[str, Any], ...]) -> dict[str, int]:
    counts = {"minor": 0, "major": 0, "critical": 0}
    for span in error_spans:
        severity = str(span.get("severity", "")).strip().lower()
        if severity in counts:
            counts[severity] += 1
    return counts


class OpenAIMqmJudge:
    """LLM-as-judge wrapper for chemistry or legal MQM-style evaluation."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str = MQM_DEFAULT_MODEL,
        timeout: float = 120.0,
        domain: str = "chemistry",
    ) -> None:
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - dependency is included for normal installs
            raise RuntimeError("FSP/MQM requested but the openai package is unavailable.") from exc

        self.client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)
        self.model = model
        self.domain = normalize_mqm_domain(domain)
        self.system_prompt = mqm_judge_system_prompt(self.domain)

    def score(self, source: str, prediction: str, reference: str) -> MqmJudgeResult:
        response = self.client.responses.create(
            model=self.model,
            temperature=0.0,
            input=[
                {"role": "system", "content": self.system_prompt},
                {
                    "role": "user",
                    "content": (
                        "Evaluate this translation.\n\n"
                        f"Source:\n{source}\n\n"
                        f"Reference translation:\n{reference}\n\n"
                        f"Candidate translation:\n{prediction}"
                    ),
                },
            ],
        )
        return parse_mqm_judge_response(response.output_text)


def normalize_mqm_domain(domain: str | None) -> str:
    normalized = str(domain or "").strip().casefold()
    if normalized in {"legal", "jrc", "eurolex", "acquis", "law", "regulatory"}:
        return "legal"
    return "chemistry"


def mqm_judge_system_prompt(domain: str | None) -> str:
    if normalize_mqm_domain(domain) == "legal":
        return LEGAL_MQM_JUDGE_SYSTEM_PROMPT
    return CHEMISTRY_MQM_JUDGE_SYSTEM_PROMPT


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
    bertscore_scorer: BertScoreScorer | None = None,
    bleurt_scorer: BleurtScorer | None = None,
    comet_scorer: CometScorer | None = None,
    cometkiwi_scorer: CometQeScorer | None = None,
    xcomet_scorer: XCometScorer | None = None,
    terminology: list[dict[str, Any]] | None = None,
    terminology_term_groups: list[str] | tuple[str, ...] | None = DEFAULT_TERMINOLOGY_TERM_GROUPS,
    mqm_judge: MqmJudge | None = None,
    metric_details: dict[str, Any] | None = None,
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

    if "bertscore" in selected_metrics:
        result = (bertscore_scorer or HuggingFaceBertScoreScorer()).score(
            prediction=prediction,
            reference=reference,
        )
        metrics["bertscore"] = result.f1
        metrics["bertscore_precision"] = result.precision
        metrics["bertscore_recall"] = result.recall

    if "bleurt" in selected_metrics:
        if bleurt_scorer is None:
            raise ValueError("BLEURT metric requires a BLEURT scorer with a local checkpoint.")
        metrics["bleurt"] = bleurt_scorer.score(prediction=prediction, reference=reference)

    if "term_bertscore_recall" in selected_metrics:
        reference_terms = reference_target_terms(
            reference=reference,
            terminology=terminology or [],
            term_groups=terminology_term_groups,
        )
        if reference_terms:
            result = (bertscore_scorer or HuggingFaceBertScoreScorer()).score(
                prediction=prediction,
                reference="; ".join(reference_terms),
            )
            metrics["term_bertscore_recall"] = result.recall
            metrics["term_bertscore_reference_term_count"] = float(len(reference_terms))
            if metric_details is not None:
                metric_details["term_bertscore_reference_terms"] = list(reference_terms)

    if "comet" in selected_metrics:
        if source is None:
            raise ValueError("COMET metric requires source text.")
        scorer = comet_scorer or UnbabelCometScorer()
        metrics["comet"] = scorer.score(
            source=source,
            prediction=prediction,
            reference=reference,
        )

    if "cometkiwi_qe" in selected_metrics:
        if source is None:
            raise ValueError("COMETKiwi QE metric requires source text.")
        scorer = cometkiwi_scorer or UnbabelCometScorer(COMETKIWI_DEFAULT_MODEL)
        metrics["cometkiwi_qe"] = scorer.score(source=source, prediction=prediction)

    if "xcomet_xl" in selected_metrics:
        if source is None:
            raise ValueError("XCOMET-XL metric requires source text.")
        scorer = xcomet_scorer or UnbabelXCometScorer(XCOMET_XL_DEFAULT_MODEL)
        result = scorer.score(source=source, prediction=prediction, reference=reference)
        metrics["xcomet_xl"] = result.score
        severity_counts = xcomet_severity_counts(result.error_spans)
        for severity, count in severity_counts.items():
            metrics[f"xcomet_xl_{severity}_error_spans"] = float(count)
        if metric_details is not None:
            metric_details["xcomet_xl_error_spans"] = list(result.error_spans)

    if "terminology_success_rate" in selected_metrics:
        terminology_score = compute_terminology_success_rate(
            prediction=prediction,
            terminology=terminology or [],
            source=source,
            reference=reference,
            term_groups=terminology_term_groups,
        )
        if terminology_score is not None:
            metrics["terminology_success_rate"] = terminology_score

    if "variant_aware_terminology_success_rate" in selected_metrics:
        terminology_score = compute_variant_aware_terminology_success_rate(
            prediction=prediction,
            terminology=terminology or [],
            source=source,
            reference=reference,
            term_groups=terminology_term_groups,
        )
        if terminology_score is not None:
            metrics["variant_aware_terminology_success_rate"] = terminology_score

    if "target_term_coverage" in selected_metrics:
        target_term_coverage = compute_target_term_coverage(
            prediction=prediction,
            reference=reference,
            terminology=terminology or [],
            term_groups=terminology_term_groups,
        )
        if target_term_coverage is not None:
            metrics["target_term_coverage"] = target_term_coverage

    if "variant_aware_target_term_coverage" in selected_metrics:
        target_term_coverage = compute_variant_aware_target_term_coverage(
            prediction=prediction,
            reference=reference,
            terminology=terminology or [],
            term_groups=terminology_term_groups,
        )
        if target_term_coverage is not None:
            metrics["variant_aware_target_term_coverage"] = target_term_coverage

    if "fsp_mqm" in selected_metrics:
        if source is None:
            raise ValueError("FSP/MQM metric requires source text.")
        if mqm_judge is None:
            raise ValueError("FSP/MQM metric requires an MQM judge.")
        mqm_result = mqm_judge.score(
            source=source,
            prediction=prediction,
            reference=reference,
        )
        metrics["fsp_mqm"] = mqm_result.quality_score
        metrics["fsp_mqm_error_score"] = mqm_result.error_score
        metrics["fsp_mqm_minor_errors"] = mqm_result.minor_errors
        metrics["fsp_mqm_major_errors"] = mqm_result.major_errors
        metrics["fsp_mqm_critical_errors"] = mqm_result.critical_errors

    return metrics


def compute_terminology_success_rate(
    prediction: str,
    terminology: list[dict[str, Any]],
    source: str | None = None,
    reference: str | None = None,
    term_groups: list[str] | tuple[str, ...] | None = DEFAULT_TERMINOLOGY_TERM_GROUPS,
) -> float | None:
    """Return WMT-style percent of applicable manifest terms found in the prediction."""
    applicable_scores = []
    for term in terminology:
        if not isinstance(term, dict):
            continue
        if str(term.get("decision", "")).strip().lower() == "drop":
            continue
        if not terminology_term_group_matches(term, term_groups):
            continue
        canonical_target_terms = accepted_target_terms(term)
        if not canonical_target_terms:
            continue

        source_count = applicable_source_count(term, source)
        if source_count == 0:
            continue
        if reference is not None and not any(
            count_normalized_occurrences(reference, target_term) > 0
            for target_term in canonical_target_terms
        ):
            continue

        output_count = sum(
            count_normalized_occurrences(prediction, target_term)
            for target_term in canonical_target_terms
        )
        applicable_scores.append(min(output_count / source_count, 1.0))

    if not applicable_scores:
        return None

    return 100 * sum(applicable_scores) / len(applicable_scores)


def compute_variant_aware_terminology_success_rate(
    prediction: str,
    terminology: list[dict[str, Any]],
    source: str | None = None,
    reference: str | None = None,
    term_groups: list[str] | tuple[str, ...] | None = DEFAULT_TERMINOLOGY_TERM_GROUPS,
) -> float | None:
    """Return WMT-style terminology success using canonical or external candidate variants."""
    applicable_scores = []
    for term in terminology:
        if not isinstance(term, dict):
            continue
        if str(term.get("decision", "")).strip().lower() == "drop":
            continue
        if not terminology_term_group_matches(term, term_groups):
            continue
        canonical_target_terms = accepted_target_terms(term)
        if not canonical_target_terms:
            continue

        source_count = applicable_source_count(term, source)
        if source_count == 0:
            continue
        if reference is not None and not any(
            count_normalized_occurrences(reference, target_term) > 0
            for target_term in canonical_target_terms
        ):
            continue

        output_count = sum(
            count_normalized_occurrences(prediction, target_term)
            for target_term in accepted_target_terms(term, include_external_candidates=True)
        )
        applicable_scores.append(min(output_count / source_count, 1.0))

    if not applicable_scores:
        return None
    return 100 * sum(applicable_scores) / len(applicable_scores)


def compute_target_term_coverage(
    prediction: str,
    reference: str,
    terminology: list[dict[str, Any]],
    term_groups: list[str] | tuple[str, ...] | None = DEFAULT_TERMINOLOGY_TERM_GROUPS,
) -> float | None:
    """Return percent of reference target-term occurrences covered by the prediction."""
    applicable_scores = []
    for term in terminology:
        if not isinstance(term, dict):
            continue
        if str(term.get("decision", "")).strip().lower() == "drop":
            continue
        if not terminology_term_group_matches(term, term_groups):
            continue
        target_terms = accepted_target_terms(term)
        if not target_terms:
            continue

        reference_count = sum(
            count_normalized_occurrences(reference, target_term)
            for target_term in target_terms
        )
        if reference_count == 0:
            continue

        prediction_count = sum(
            count_normalized_occurrences(prediction, target_term)
            for target_term in target_terms
        )
        applicable_scores.append(min(prediction_count / reference_count, 1.0))

    if not applicable_scores:
        return None

    return 100 * sum(applicable_scores) / len(applicable_scores)


def reference_target_terms(
    *,
    reference: str,
    terminology: list[dict[str, Any]],
    term_groups: list[str] | tuple[str, ...] | None = DEFAULT_TERMINOLOGY_TERM_GROUPS,
) -> tuple[str, ...]:
    """Return selected canonical target terms that occur in the reference translation."""
    terms: list[str] = []
    seen = set()
    for term in terminology:
        if not isinstance(term, dict):
            continue
        if str(term.get("decision", "")).strip().lower() == "drop":
            continue
        if not terminology_term_group_matches(term, term_groups):
            continue
        for target_term in accepted_target_terms(term):
            normalized = normalize_metric_text(target_term)
            if (
                normalized
                and normalized not in seen
                and count_normalized_occurrences(reference, target_term) > 0
            ):
                terms.append(target_term)
                seen.add(normalized)
    return tuple(terms)


def compute_variant_aware_target_term_coverage(
    prediction: str,
    reference: str,
    terminology: list[dict[str, Any]],
    term_groups: list[str] | tuple[str, ...] | None = DEFAULT_TERMINOLOGY_TERM_GROUPS,
) -> float | None:
    """Return coverage when a canonical target term or its external candidate variant occurs."""
    applicable_scores = []
    for term in terminology:
        if not isinstance(term, dict):
            continue
        if str(term.get("decision", "")).strip().lower() == "drop":
            continue
        if not terminology_term_group_matches(term, term_groups):
            continue
        canonical_target_terms = accepted_target_terms(term)
        if not canonical_target_terms:
            continue

        reference_count = sum(
            count_normalized_occurrences(reference, target_term)
            for target_term in canonical_target_terms
        )
        if reference_count == 0:
            continue

        prediction_count = sum(
            count_normalized_occurrences(prediction, target_term)
            for target_term in accepted_target_terms(term, include_external_candidates=True)
        )
        applicable_scores.append(min(prediction_count / reference_count, 1.0))

    if not applicable_scores:
        return None
    return 100 * sum(applicable_scores) / len(applicable_scores)


def select_terminology_terms(
    terminology: list[dict[str, Any]],
    *,
    term_groups: list[str] | tuple[str, ...] | None,
    require_verified: bool = False,
) -> list[dict[str, Any]]:
    """Select distinct target-side terms for a named evaluation slice."""
    selected: dict[tuple[str, ...], dict[str, Any]] = {}
    for term in terminology:
        if not isinstance(term, dict):
            continue
        if str(term.get("decision", "")).strip().lower() == "drop":
            continue
        if not terminology_term_group_matches(term, term_groups):
            continue
        if require_verified and not term.get("verified_by"):
            continue
        target_terms = accepted_target_terms(term)
        key = tuple(normalize_metric_text(target_term) for target_term in target_terms)
        if not key:
            continue
        existing = selected.get(key)
        if existing is None:
            selected[key] = dict(term)
            continue
        merge_external_candidates(existing, term)
        if terminology_selection_priority(term) > terminology_selection_priority(existing):
            replacement = dict(term)
            merge_external_candidates(replacement, existing)
            selected[key] = replacement
    return list(selected.values())


def merge_external_candidates(target: dict[str, Any], source: dict[str, Any]) -> None:
    target_candidates = target.get("external_candidates") or target.get("candidates") or {}
    source_candidates = source.get("external_candidates") or source.get("candidates") or {}
    if not isinstance(target_candidates, dict) or not isinstance(source_candidates, dict):
        return
    merged = {
        str(name): list(values)
        for name, values in target_candidates.items()
        if isinstance(values, list)
    }
    for name, values in source_candidates.items():
        if not isinstance(values, list):
            continue
        merged[str(name)] = list(
            unique_normalized_terms(
                tuple(str(value) for value in merged.get(str(name), []) + values)
            )
        )
    if merged:
        target["external_candidates"] = merged


def terminology_selection_priority(term: dict[str, Any]) -> int:
    group = terminology_term_group(term)
    return {"refined": 3, "verified": 2, "llm": 1, "algorithmic": 0}.get(group, 0)


def applicable_source_count(term: dict[str, Any], source: str | None) -> int:
    if source is None:
        return 1
    source_term = str(term.get("source_term", "")).strip()
    if not source_term:
        return 0
    return count_normalized_occurrences(source, source_term)


def accepted_target_terms(
    term: dict[str, Any],
    *,
    include_external_candidates: bool = False,
) -> tuple[str, ...]:
    raw_target_terms = term.get("target_terms", [])
    if not isinstance(raw_target_terms, list):
        raw_target_terms = []
    target_terms = tuple(
        str(target_term).strip()
        for target_term in raw_target_terms
        if str(target_term).strip()
    )
    decision = str(term.get("decision", "")).strip().lower()
    if target_terms:
        accepted_terms = target_terms
    elif decision == "preserve":
        source_term = str(term.get("source_term", "")).strip()
        accepted_terms = (source_term,) if source_term else ()
    else:
        accepted_terms = ()

    if include_external_candidates:
        external_candidates = term.get("external_candidates") or term.get("candidates") or {}
        if isinstance(external_candidates, dict):
            accepted_terms += tuple(
                str(candidate).strip()
                for candidates in external_candidates.values()
                if isinstance(candidates, list)
                for candidate in candidates
                if str(candidate).strip()
            )
    return unique_normalized_terms(accepted_terms)


def unique_normalized_terms(terms: tuple[str, ...]) -> tuple[str, ...]:
    unique = []
    seen = set()
    for term in terms:
        key = normalize_metric_text(term)
        if key and key not in seen:
            seen.add(key)
            unique.append(term)
    return tuple(unique)


def terminology_term_group_matches(
    term: dict[str, Any],
    term_groups: list[str] | tuple[str, ...] | None,
) -> bool:
    if term_groups is None:
        term_groups = DEFAULT_TERMINOLOGY_TERM_GROUPS
    allowed_groups = {group.strip().lower() for group in term_groups if group.strip()}
    if not allowed_groups:
        return True
    return terminology_term_group(term) in allowed_groups


def terminology_term_group(term: dict[str, Any]) -> str:
    explicit_group = str(term.get("term_group", "")).strip().lower()
    if explicit_group:
        return explicit_group
    external_candidates = term.get("external_candidates") or term.get("candidates") or {}
    if isinstance(external_candidates, dict) and external_candidates:
        return "verified"
    source = str(term.get("source", "")).strip().lower()
    if source == "llm_target" or source.startswith("llm_target+"):
        return "llm"
    if source:
        return "algorithmic"
    return "verified"


def contains_normalized_term(text: str, term: str) -> bool:
    return count_normalized_occurrences(text, term) > 0


def count_normalized_occurrences(text: str, term: str) -> int:
    normalized_text = normalize_metric_text(text)
    normalized_term = normalize_metric_text(term)
    if not normalized_term:
        return 0
    return normalized_text.count(normalized_term)


def normalize_metric_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text).casefold()
    return re.sub(r"\s+", " ", normalized).strip()


def compute_corpus_overlap_metrics(
    predictions: list[str],
    references: list[str],
    metric_names: list[str] | tuple[str, ...],
) -> dict[str, float]:
    """Compute WMT-style corpus BLEU/chrF metrics for report summaries."""
    metrics = {}
    if "bleu" in metric_names and BLEU:
        metrics["bleu"] = BLEU(max_ngram_order=4, tokenize="13a").corpus_score(
            predictions,
            [references],
        ).score
    if "chrf" in metric_names and CHRF:
        metrics["chrf"] = CHRF().corpus_score(predictions, [references]).score
    if "chrf2++" in metric_names and CHRF:
        metrics["chrf2++"] = CHRF(char_order=6, word_order=2).corpus_score(
            predictions,
            [references],
        ).score
    return metrics


def parse_mqm_judge_response(text: str) -> MqmJudgeResult:
    match = _JSON_OBJECT_RE.search(text)
    try:
        payload = json.loads(match.group(0) if match else text)
    except json.JSONDecodeError:
        return MqmJudgeResult(quality_score=0.0, error_score=100.0, critical_errors=1)

    raw_errors = payload.get("errors", [])
    if not isinstance(raw_errors, list):
        raw_errors = []

    severity_counts = {"minor": 0, "major": 0, "critical": 0}
    for raw_error in raw_errors:
        if not isinstance(raw_error, dict):
            continue
        severity = str(raw_error.get("severity", "")).strip().lower()
        if severity in severity_counts:
            severity_counts[severity] += 1

    error_score = sum(
        severity_counts[severity] * weight
        for severity, weight in _MQM_SEVERITY_WEIGHTS.items()
    )
    return MqmJudgeResult(
        quality_score=parse_score(payload.get("quality_score")),
        error_score=float(error_score),
        minor_errors=severity_counts["minor"],
        major_errors=severity_counts["major"],
        critical_errors=severity_counts["critical"],
    )


def parse_score(value: object) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(score, 100.0))
