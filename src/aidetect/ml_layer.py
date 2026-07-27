from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from functools import lru_cache
from typing import Optional

# Local, offline text classifiers. Model weights are cached to disk by
# huggingface_hub on first use (one-time download); after that, inference
# never leaves the machine. See docs/LEGAL_USE.md for the offline guarantee.
ARABIC_MODEL_ID = "sabaridsnfuji/arabic-ai-text-detector"
ENGLISH_MODEL_ID = "Hello-SimpleAI/chatgpt-detector-roberta"

# Flat folder names used by scripts/prefetch_models.py and looked up via the
# matching env var below - lets a packaged build point straight at bundled
# model folders without going through the (Windows-unfriendly) HF hub cache.
MODEL_DIR_NAME_BY_MODEL = {
    ARABIC_MODEL_ID: "arabic",
    ENGLISH_MODEL_ID: "english",
}
_LOCAL_DIR_ENV_BY_MODEL = {
    ARABIC_MODEL_ID: "AIDETECT_ARABIC_MODEL_DIR",
    ENGLISH_MODEL_ID: "AIDETECT_ENGLISH_MODEL_DIR",
}

# Exact id2label mappings, normalized to "which label means AI-generated".
# Do not fuzzy-match label strings here - this feeds a legal-context report,
# so the mapping must be explicit and verified against real model output
# (not just the model card's prose, which can be wrong - see below).
_AI_LABEL_BY_MODEL = {
    # This model's config.json has NO id2label mapping, so the pipeline falls
    # back to generic "LABEL_0"/"LABEL_1" - it does NOT return "HUMAN"/"AI"
    # strings despite what the model card's example code implies. Verified by
    # running actual inference; per the author's own documented mapping
    # (labels = {0: "HUMAN", 1: "AI"}), LABEL_1 is AI.
    ARABIC_MODEL_ID: "LABEL_1",
    ENGLISH_MODEL_ID: "ChatGPT",  # id2label: {0: "Human", 1: "ChatGPT"} - confirmed via config.json
}

_MAX_CHARS_BY_MODEL = {
    ARABIC_MODEL_ID: 1500,   # ~512 tokens budget for Arabic subword tokenization
    ENGLISH_MODEL_ID: 2000,
}

# Raw pipeline label -> human-readable label, for display in reports/UI.
_DISPLAY_LABEL_BY_MODEL = {
    ARABIC_MODEL_ID: {"LABEL_0": "HUMAN", "LABEL_1": "AI"},
    ENGLISH_MODEL_ID: {"Human": "Human", "ChatGPT": "AI (ChatGPT-style)"},
}


@dataclass(frozen=True)
class MLResult:
    available: bool
    model_id: Optional[str]
    label: Optional[str]
    ai_probability: Optional[float]
    verdict: Optional[str]
    note: str

    def to_dict(self) -> dict:
        return asdict(self)


class MLLayerUnavailable(RuntimeError):
    """Raised when the optional ML extra (transformers + torch) isn't installed."""


def is_supported_language(language: str) -> bool:
    return language in ("ar", "en", "mixed")


def _model_id_for(language: str) -> str:
    return ARABIC_MODEL_ID if language == "ar" else ENGLISH_MODEL_ID


@lru_cache(maxsize=None)
def _pipeline_for(model_id: str):
    try:
        from transformers import pipeline
    except ImportError as exc:
        raise MLLayerUnavailable(
            "The ML layer needs the optional 'ml' extra (transformers + torch). "
            "Install with: pip install -e \".[ml]\"  (or: pip install transformers torch)"
        ) from exc

    env_var = _LOCAL_DIR_ENV_BY_MODEL.get(model_id)
    local_dir = os.environ.get(env_var) if env_var else None
    source = local_dir if local_dir and os.path.isdir(local_dir) else model_id
    return pipeline("text-classification", model=source, tokenizer=source, top_k=None)


def _score_to_verdict(ai_probability: float) -> str:
    if ai_probability >= 0.70:
        return "high_ai_likelihood"
    if ai_probability >= 0.45:
        return "mixed_or_uncertain"
    return "low_ai_likelihood"


def classify(text: str, language: str) -> MLResult:
    """Run the local ML classifier layer (Layer 2) for the detected language.

    Returns an MLResult with available=False (never raises) when the language
    has no bundled model, the optional deps aren't installed, or inference fails -
    Layer 1 heuristics should still produce a report in every case.
    """
    if not is_supported_language(language):
        return MLResult(
            available=False, model_id=None, label=None, ai_probability=None, verdict=None,
            note=f"No bundled ML classifier for detected language '{language}'.",
        )

    model_id = _model_id_for(language)
    ai_label = _AI_LABEL_BY_MODEL[model_id]

    try:
        clf = _pipeline_for(model_id)
    except MLLayerUnavailable as exc:
        return MLResult(
            available=False, model_id=model_id, label=None, ai_probability=None, verdict=None,
            note=str(exc),
        )

    snippet = (text or "")[: _MAX_CHARS_BY_MODEL.get(model_id, 2000)]

    try:
        outputs = clf(snippet, truncation=True)
    except Exception as exc:  # local model/runtime failure must not crash the report
        return MLResult(
            available=False, model_id=model_id, label=None, ai_probability=None, verdict=None,
            note=f"Local model inference failed: {exc}",
        )

    scores = outputs[0] if outputs and isinstance(outputs[0], list) else outputs
    by_label = {item["label"]: item["score"] for item in scores}

    ai_probability = by_label.get(ai_label)
    if ai_probability is None:
        return MLResult(
            available=False, model_id=model_id, label=None, ai_probability=None, verdict=None,
            note=f"Model returned unexpected labels {list(by_label)}; expected '{ai_label}' among them.",
        )

    top_label = max(by_label, key=by_label.get)
    display_label = _DISPLAY_LABEL_BY_MODEL.get(model_id, {}).get(top_label, top_label)
    verdict = _score_to_verdict(ai_probability)

    return MLResult(
        available=True,
        model_id=model_id,
        label=display_label,
        ai_probability=round(float(ai_probability), 4),
        verdict=verdict,
        note=f"Local classifier ({model_id}) estimates {ai_probability:.0%} probability of AI-generated text.",
    )
