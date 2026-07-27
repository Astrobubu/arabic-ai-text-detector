from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from . import ml_layer
from .core import DetectionResult, analyze_text
from .ml_layer import MLResult

TOOL_VERSION = "0.2.0"

_AI_BUCKETS = {"high_ai_likelihood"}
_HUMAN_BUCKETS = {"low_ai_likelihood"}


@dataclass(frozen=True)
class CombinedReport:
    generated_at: str
    tool_version: str
    input_sha256: str
    language: str
    word_count: int
    heuristic: DetectionResult
    ml: MLResult
    agreement: str
    summary: str
    caveats: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def _agreement_and_summary(heuristic: DetectionResult, ml: MLResult) -> tuple[str, str]:
    if heuristic.verdict == "insufficient_text":
        return (
            "insufficient_text",
            "The sample is too short to run either detection layer reliably.",
        )

    if not ml.available:
        return (
            "ml_layer_unavailable",
            "Only the rule-based heuristic layer ran. "
            f"It reports {heuristic.verdict.replace('_', ' ')} ({heuristic.score}/100). "
            "The local ML classifier layer did not produce a result: " + ml.note,
        )

    h_bucket = (
        "ai" if heuristic.verdict in _AI_BUCKETS
        else "human" if heuristic.verdict in _HUMAN_BUCKETS
        else "uncertain"
    )
    m_bucket = (
        "ai" if ml.verdict in _AI_BUCKETS
        else "human" if ml.verdict in _HUMAN_BUCKETS
        else "uncertain"
    )

    if h_bucket == "ai" and m_bucket == "ai":
        return (
            "both_layers_flag_ai_like",
            f"Both layers flag AI-like writing: heuristics {heuristic.score}/100, "
            f"ML classifier {ml.ai_probability:.0%} AI probability. Convergent signals, still not proof.",
        )
    if h_bucket == "human" and m_bucket == "human":
        return (
            "both_layers_flag_human_like",
            f"Both layers read as human-like: heuristics {heuristic.score}/100, "
            f"ML classifier {ml.ai_probability:.0%} AI probability. Convergent signals, still not proof.",
        )
    if {h_bucket, m_bucket} == {"ai", "human"}:
        return (
            "layers_disagree",
            f"The two layers disagree: heuristics read {heuristic.verdict.replace('_', ' ')} "
            f"({heuristic.score}/100) while the ML classifier reads {ml.verdict.replace('_', ' ')} "
            f"({ml.ai_probability:.0%} AI probability). Treat this sample as genuinely uncertain and "
            "prioritize human review over either automated signal.",
        )
    return (
        "uncertain_or_mixed",
        f"Signals are mixed: heuristics {heuristic.score}/100 ({heuristic.verdict.replace('_', ' ')}), "
        f"ML classifier {ml.ai_probability:.0%} AI probability ({ml.verdict.replace('_', ' ')}). "
        "Neither layer gives a confident read.",
    )


def generate_report(text: str, *, use_ml: bool = True) -> CombinedReport:
    """Run both detection layers and combine them into one explainable report.

    Layer 1 (heuristic, core.analyze_text) always runs and never requires extra
    dependencies. Layer 2 (ml_layer.classify) runs a local, offline ML classifier
    when the optional 'ml' extra is installed; if not, the report still returns
    with ml.available=False rather than failing.
    """
    raw = text or ""
    heuristic = analyze_text(raw)

    if heuristic.verdict == "insufficient_text" or not use_ml:
        ml_result = MLResult(
            available=False, model_id=None, label=None, ai_probability=None, verdict=None,
            note="Skipped (sample too short)." if heuristic.verdict == "insufficient_text" else "Skipped (use_ml=False).",
        )
    else:
        ml_result = ml_layer.classify(raw, heuristic.language)

    agreement, summary = _agreement_and_summary(heuristic, ml_result)

    caveats = list(heuristic.caveats)
    caveats.append(
        "This report combines two independent automated signals (rule-based heuristics and a local "
        "ML classifier). Neither layer, alone or combined, constitutes forensic proof of authorship."
    )
    if not ml_result.available and heuristic.verdict != "insufficient_text":
        caveats.append(
            "The ML classifier layer did not run, so this report reflects heuristics only and carries "
            "correspondingly lower confidence."
        )

    return CombinedReport(
        generated_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        tool_version=TOOL_VERSION,
        input_sha256=hashlib.sha256(raw.encode("utf-8")).hexdigest(),
        language=heuristic.language,
        word_count=heuristic.word_count,
        heuristic=heuristic,
        ml=ml_result,
        agreement=agreement,
        summary=summary,
        caveats=caveats,
    )
