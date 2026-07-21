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
    "comet",
    "terminology_success_rate",
    "fsp_mqm",
)
DEFAULT_METRIC_NAMES = (
    "sequence_similarity",
    "bleu",
    "chrf2++",
    "comet",
    "terminology_success_rate",
)
COMET_DEFAULT_MODEL = "Unbabel/wmt22-comet-da"
MQM_DEFAULT_MODEL = "gpt-4.1-mini"
_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)
_MQM_SEVERITY_WEIGHTS = {"minor": 1, "major": 2, "critical": 5}

MQM_JUDGE_SYSTEM_PROMPT = """You are an MQM-style evaluator for chemistry and patent machine
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


class CometScorer(Protocol):
    def score(self, source: str, prediction: str, reference: str) -> float:
        """Return a segment-level COMET score."""


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


class OpenAIMqmJudge:
    """LLM-as-judge wrapper for optional FSP/MQM-style evaluation."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str = MQM_DEFAULT_MODEL,
        timeout: float = 120.0,
    ) -> None:
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - dependency is included for normal installs
            raise RuntimeError("FSP/MQM requested but the openai package is unavailable.") from exc

        self.client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)
        self.model = model

    def score(self, source: str, prediction: str, reference: str) -> MqmJudgeResult:
        response = self.client.responses.create(
            model=self.model,
            temperature=0.0,
            input=[
                {"role": "system", "content": MQM_JUDGE_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        "Evaluate this translation for chemistry and patent MT quality.\n\n"
                        f"Source:\n{source}\n\n"
                        f"Reference translation:\n{reference}\n\n"
                        f"Candidate translation:\n{prediction}"
                    ),
                },
            ],
        )
        return parse_mqm_judge_response(response.output_text)


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
    terminology: list[dict[str, Any]] | None = None,
    mqm_judge: MqmJudge | None = None,
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

    if "terminology_success_rate" in selected_metrics:
        terminology_score = compute_terminology_success_rate(prediction, terminology or [])
        if terminology_score is not None:
            metrics["terminology_success_rate"] = terminology_score

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
) -> float | None:
    """Return percent of accepted manifest terms found in the prediction."""
    accepted_terms = [
        term
        for term in terminology
        if isinstance(term, dict)
        and str(term.get("decision", "")).strip().lower() != "drop"
        and accepted_target_terms(term)
    ]
    if not accepted_terms:
        return None

    matched_terms = sum(
        1
        for term in accepted_terms
        if any(
            contains_normalized_term(prediction, target_term)
            for target_term in accepted_target_terms(term)
        )
    )
    return 100 * matched_terms / len(accepted_terms)


def accepted_target_terms(term: dict[str, Any]) -> tuple[str, ...]:
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
        return target_terms
    if decision == "preserve":
        source_term = str(term.get("source_term", "")).strip()
        return (source_term,) if source_term else ()
    return ()


def contains_normalized_term(text: str, term: str) -> bool:
    normalized_text = normalize_metric_text(text)
    normalized_term = normalize_metric_text(term)
    if not normalized_term:
        return False

    pattern = re.escape(normalized_term)
    if normalized_term[0].isalnum():
        pattern = rf"(?<!\w){pattern}"
    if normalized_term[-1].isalnum():
        pattern = rf"{pattern}(?!\w)"
    return re.search(pattern, normalized_text) is not None


def normalize_metric_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text).casefold()
    return re.sub(r"\s+", " ", normalized).strip()


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
