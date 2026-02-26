"""
Scoring engine: computes weighted scores for AWS, Azure, and GCP
using static configuration. Pure business logic; no side effects.
"""

from typing import Any, Dict, Mapping, Optional

from app.core.config import (
    MOCK_PRICING,
    PROVIDER_CATALOG,
    REGION_PROVIDER_MODIFIERS,
    WEIGHT_CONFIG,
)

# Qualitative user input -> numeric intensity (1–9 scale).
# Used to weight how much each dimension matters to the user.
QUALITATIVE_SCALE = {
    "low": 3,
    "medium": 6,
    "high": 9,
}

# Feature keys expected in user_input and present in config.
EXPECTED_FEATURES = frozenset(WEIGHT_CONFIG.keys())


def _validate_and_normalize_user_input(user_input: dict) -> Dict[str, float]:
    """
    Validate user_input keys/values and convert qualitative preferences
    to normalized intensity (0–1). Missing features default to 'medium'.
    """
    if not isinstance(user_input, dict):
        raise TypeError("user_input must be a dict")

    normalized: Dict[str, float] = {}
    allowed = set(QUALITATIVE_SCALE)

    for feature in EXPECTED_FEATURES:
        raw = user_input.get(feature, "medium")
        if raw not in allowed:
            raise ValueError(
                f"Invalid value for '{feature}': '{raw}'. "
                f"Expected one of: {sorted(allowed)}"
            )
        # Scale to 0–1 so weighted sum stays in a bounded range.
        normalized[feature] = QUALITATIVE_SCALE[raw] / 9.0

    return normalized


def _select_weights(custom_weights: Optional[Mapping[str, Any]]) -> Dict[str, float]:
    """
    Choose which weights to use for scoring.

    If custom_weights is provided and contains numeric values for all
    EXPECTED_FEATURES, they are normalized to sum to 1. Otherwise the
    static WEIGHT_CONFIG is returned.
    """
    if custom_weights is None:
        return dict(WEIGHT_CONFIG)

    # Extract and coerce values for all expected features.
    raw: Dict[str, float] = {}
    total = 0.0
    for feature in EXPECTED_FEATURES:
        value = custom_weights.get(feature)
        if not isinstance(value, (int, float)):
            return dict(WEIGHT_CONFIG)
        coerced = float(value)
        if coerced < 0:
            return dict(WEIGHT_CONFIG)
        raw[feature] = coerced
        total += coerced

    if total <= 0:
        return dict(WEIGHT_CONFIG)

    normalized: Dict[str, float] = {}
    for feature, value in raw.items():
        normalized[feature] = value / total

    return normalized


def calculate_estimated_cost(
    user_input: Dict[str, Any],
    provider: str,
) -> float:
    """
    Compute estimated monthly cost (USD) for a provider from mock pricing and
    user_input. Deterministic; no external APIs.

    Cost multipliers (additive):
    - high scalability → +30%
    - high security → +20%
    - low team_expertise → +10%
    (medium: half of high; low/other: 0%)

    Args:
        user_input: Dict with scalability, security, team_expertise (low/medium/high).
        provider: Provider id: "aws", "azure", or "gcp".

    Returns:
        Estimated monthly cost, rounded to integer.
    """
    if provider not in MOCK_PRICING:
        return 0.0
    bases = MOCK_PRICING[provider]
    base_total = bases["base_compute"] + bases["base_storage"]

    mult = 1.0
    raw = user_input or {}
    scal = (raw.get("scalability") or "medium").lower()
    sec = (raw.get("security") or "medium").lower()
    expertise = (raw.get("team_expertise") or "medium").lower()

    if scal == "high":
        mult += 0.30
    elif scal == "medium":
        mult += 0.15
    if sec == "high":
        mult += 0.20
    elif sec == "medium":
        mult += 0.10
    if expertise == "low":
        mult += 0.10

    return round(base_total * mult, 0)


def calculate_provider_scores(
    user_input: Dict[str, Any],
    custom_weights: Optional[Mapping[str, Any]] = None,
    region: Optional[str] = None,
) -> Dict[str, float]:
    """
    Compute a weighted score per provider (AWS, Azure, GCP) from
    qualitative user preferences and provider feature scores.

    User preferences are given as low / medium / high per feature.
    They are converted to numeric intensity, then multiplied with
    each provider's feature score and combined using either the
    static WEIGHT_CONFIG or optional custom_weights.
    If region is provided, a small regional advantage modifier is
    added per provider.

    Args:
        user_input: Dict of feature names to qualitative level.
            Expected keys (optional; default 'medium' if missing):
            budget, scalability, security, ease_of_use, free_tier.
            Values must be one of: "low", "medium", "high".
        custom_weights: Optional mapping of feature name to numeric
            weight. If provided and valid, these weights are
            normalized to sum to 1 and used instead of WEIGHT_CONFIG.
        region: Optional deployment region: "india", "us", or "europe".
            If provided, REGION_PROVIDER_MODIFIERS are applied.

    Returns:
        Dict mapping provider id to final numeric score, e.g.:
        {"aws": <float>, "azure": <float>, "gcp": <float>}.

    Raises:
        TypeError: If user_input is not a dict.
        ValueError: If any feature value is not low/medium/high.
    """
    intensity = _validate_and_normalize_user_input(user_input)
    weights = _select_weights(custom_weights)

    result: Dict[str, float] = {}

    for provider_id, provider_data in PROVIDER_CATALOG.items():
        feature_scores = provider_data["feature_scores"]
        score = 0.0
        for feature, weight in weights.items():
            user_intensity = intensity[feature]
            provider_score = feature_scores[feature]
            score += weight * user_intensity * provider_score
        result[provider_id] = round(score, 4)

    if region and region in REGION_PROVIDER_MODIFIERS:
        modifiers = REGION_PROVIDER_MODIFIERS[region]
        for provider_id in result:
            if provider_id in modifiers:
                result[provider_id] = round(result[provider_id] + modifiers[provider_id], 4)

    if (user_input or {}).get("budget") == "high":
        costs = {
            pid: calculate_estimated_cost(user_input, pid)
            for pid in result
        }
        max_cost = max(costs.values()) if costs else 1.0
        if max_cost > 0:
            for provider_id in result:
                penalty = 0.2 * (costs.get(provider_id, 0) / max_cost)
                result[provider_id] = round(result[provider_id] - penalty, 4)

    return result


def compute_confidence(provider_scores: Dict[str, float]) -> Dict[str, Any]:
    """
    Compute decision confidence from provider score dict using absolute difference.

    Uses difference = top_score - second_score and maps to level + display percentage.
    Does not use (top - second) / top so confidence can be meaningful even with
    small relative gaps when scores are similar.

    Args:
        provider_scores: Dict mapping provider id to numeric score, e.g. {"aws": 6.2, "azure": 5.1, "gcp": 5.0}.

    Returns:
        {"confidence_percent": float (0–100), "confidence_level": "High" | "Moderate" | "Low"}.
    """
    if not provider_scores or len(provider_scores) < 2:
        return {"confidence_percent": 0.0, "confidence_level": "Low"}

    ordered = sorted(provider_scores.values(), reverse=True)
    top_score = ordered[0]
    second_score = ordered[1]
    difference = float(top_score - second_score)

    if difference >= 1.5:
        confidence_level = "High"
    elif difference >= 0.8:
        confidence_level = "Moderate"
    else:
        confidence_level = "Low"

    confidence_percent = min((difference / 3.0) * 100.0, 100.0)
    confidence_percent = round(max(0.0, confidence_percent), 1)

    return {
        "confidence_percent": confidence_percent,
        "confidence_level": confidence_level,
    }
