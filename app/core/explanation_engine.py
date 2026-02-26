"""
Explanation engine: generates human-readable explanations for provider
and service model recommendations. Deterministic; no scoring or selection.
Optional AI enhancement when enabled and configured.
"""

import json
import logging
import urllib.error
import urllib.request
from typing import Dict, Any, List, Tuple

from app.core.config import (
    ENABLE_AI_EXPLANATION,
    GEMINI_API_KEY,
    PROVIDER_CATALOG,
    WEIGHT_CONFIG,
)

logger = logging.getLogger(__name__)

# Qualitative preference -> numeric intensity for ranking influence (not for scoring).
_INFLUENCE_SCALE = {"low": 3, "medium": 6, "high": 9}

_FEATURE_NAMES = frozenset(WEIGHT_CONFIG.keys())


def _rank_criteria_by_influence(
    user_input: Dict[str, Any], top_n: int = 3
) -> List[Tuple[str, float]]:
    """
    Rank criteria by influence: weight * user preference intensity.
    Returns top_n (feature_name, influence) pairs, descending. Does not recalculate scores.
    """
    if not isinstance(user_input, dict):
        return []

    influence_list: List[Tuple[str, float]] = []
    for feature in _FEATURE_NAMES:
        weight = WEIGHT_CONFIG.get(feature, 0.0)
        raw = user_input.get(feature, "medium")
        intensity = _INFLUENCE_SCALE.get(raw, 6) if isinstance(raw, str) else 6
        influence_list.append((feature, weight * intensity))

    influence_list.sort(key=lambda x: -x[1])
    return influence_list[:top_n]


def _provider_explanation(
    selected_provider: str,
    provider_scores: Dict[str, float],
    user_input: Dict[str, Any],
) -> List[str]:
    """Build explanation strings for provider selection."""
    lines: List[str] = []

    provider_data = PROVIDER_CATALOG.get(selected_provider) if selected_provider else None
    if not provider_data:
        return ["Provider selection could not be explained (unknown or missing provider)."]

    top_criteria = _rank_criteria_by_influence(user_input or {}, top_n=3)
    criteria_names = [c[0].replace("_", " ") for c in top_criteria if c[1] > 0]

    if criteria_names:
        criteria_text = ", ".join(criteria_names)
        score_val = provider_scores.get(selected_provider) if isinstance(provider_scores, dict) else None
        if score_val is not None:
            lines.append(
                f"{selected_provider.upper()} was selected (score: {score_val}) based on your "
                f"priorities: {criteria_text}."
            )
        else:
            lines.append(
                f"{selected_provider.upper()} was selected based on your priorities: {criteria_text}."
            )
    else:
        lines.append(f"{selected_provider.upper()} was selected as the recommended provider.")

    strengths = provider_data.get("strengths")
    if isinstance(strengths, list) and strengths:
        strength_text = "; ".join(str(s) for s in strengths[:3])
        lines.append(f"Key strengths: {strength_text}.")

    return lines


def generate_explanation(
    user_input: Dict[str, Any],
    provider_scores: Dict[str, float],
    selected_provider: str,
    service_model_result: Dict[str, Any],
) -> List[str]:
    """
    Generate a deterministic, human-readable explanation for the recommended
    provider and service model. Does not recalculate scores or select a provider.

    Args:
        user_input: Original request (e.g. qualitative preferences, industry, team_expertise).
        provider_scores: Precomputed scores per provider, e.g. {"aws": 6.2, "azure": 5.8, "gcp": 6.5}.
        selected_provider: Provider id chosen (e.g. "aws", "azure", "gcp").
        service_model_result: Result from determine_service_model, with "service_model" and "reason".

    Returns:
        List of short explanation strings (provider rationale first, then service model reason).
        Safe fallback strings if inputs are missing or invalid.
    """
    result: List[str] = []

    if not isinstance(provider_scores, dict):
        result.append("Provider recommendation explanation is unavailable.")
    else:
        provider_lines = _provider_explanation(
            selected_provider or "",
            provider_scores,
            user_input if isinstance(user_input, dict) else {},
        )
        result.extend(provider_lines)

    if isinstance(service_model_result, dict) and service_model_result.get("reason"):
        result.append(service_model_result["reason"])
    else:
        result.append("Service model: default recommendation applied.")

    return result


def _format_deterministic_explanation(original_explanation: List[str]) -> str:
    """Format the deterministic explanation list as a single string."""
    if not original_explanation:
        return "No explanation available."
    return "\n\n".join(str(s) for s in original_explanation)


def enhance_explanation_with_ai(original_explanation: List[str]) -> str:
    """
    Optionally enhance explanation using Gemini. When disabled or on failure,
    returns the formatted deterministic explanation. API key is never logged or exposed.

    Args:
        original_explanation: List of strings from generate_explanation().

    Returns:
        Single string: AI-rewritten paragraph if enabled and successful,
        otherwise formatted deterministic explanation.
    """
    formatted = _format_deterministic_explanation(original_explanation)

    if not ENABLE_AI_EXPLANATION or not GEMINI_API_KEY:
        return formatted

    try:
        prompt = (
            "Rewrite this cloud recommendation explanation professionally and concisely. "
            "Keep the same meaning and do not add new facts.\n\n"
            + formatted
        )
        body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "maxOutputTokens": 300,
                "temperature": 0.3,
            },
        }
        api_key = (GEMINI_API_KEY or "").strip() if isinstance(GEMINI_API_KEY, str) else ""
        if not api_key:
            return formatted
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=" + api_key
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        candidates = data.get("candidates") or []
        if candidates and isinstance(candidates[0], dict):
            content = candidates[0].get("content") or {}
            parts = content.get("parts") or []
            if parts and isinstance(parts[0], dict):
                text = parts[0].get("text")
                if text and isinstance(text, str):
                    return text.strip()
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, KeyError, TypeError) as e:
        logger.warning("explanation_engine | Gemini enhancement failed, using deterministic | %s", e)
    except Exception as e:
        logger.warning("explanation_engine | Gemini enhancement error, using deterministic | %s", e)

    return formatted if formatted else "No explanation available."
