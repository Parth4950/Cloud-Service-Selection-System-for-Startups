"""
Route definitions. REST API for cloud provider and service model recommendations.
"""

import logging
from typing import Any, Dict, List

from flask import Blueprint, request, jsonify

from app.core.scoring_engine import calculate_estimated_cost, calculate_provider_scores
from app.core.service_model_rules import determine_service_model
from app.core.explanation_engine import enhance_explanation_with_ai, generate_explanation

logger = logging.getLogger(__name__)
bp = Blueprint("api", __name__, url_prefix="/")


@bp.route("/health", methods=["GET"])
def health():
    """
    Lightweight health check for production monitoring (e.g. AWS Elastic Beanstalk).
    Returns 200 and minimal JSON. No scoring, rules, or heavy operations.
    """
    return jsonify({"status": "ok", "service": "cloud-selection-backend"}), 200


REQUIRED_FIELDS = [
    "budget",
    "scalability",
    "security",
    "ease_of_use",
    "free_tier",
    "team_expertise",
    "industry",
]

QUALITATIVE_VALUES = frozenset({"low", "medium", "high"})
INDUSTRY_VALUES = frozenset({"general", "fintech", "healthcare", "ai"})
REGION_VALUES = frozenset({"india", "us", "europe"})

QUALITATIVE_FIELDS = frozenset({
    "budget", "scalability", "security", "ease_of_use", "free_tier", "team_expertise",
})

WEIGHT_FIELDS = ("budget", "scalability", "security", "ease_of_use", "free_tier")


def _validate_payload(data: Any) -> tuple[Dict[str, Any] | None, str | None]:
    """
    Validate JSON body has all required fields. Returns (user_input, None) if valid,
    or (None, error_message) if invalid.
    """
    if not isinstance(data, dict):
        return None, "Request body must be a JSON object."

    missing = [f for f in REQUIRED_FIELDS if f not in data]
    if missing:
        return None, f"Missing required fields: {', '.join(sorted(missing))}."

    return data, None


def _validate_field_values(data: Dict[str, Any]) -> str | None:
    """
    Validate each required field has an allowed value. Returns None if valid,
    or error message "Invalid value for <field>" if invalid.
    """
    for field in REQUIRED_FIELDS:
        value = data.get(field)
        if not isinstance(value, str):
            return f"Invalid value for {field}"
        normalized = value.strip().lower()
        if field in QUALITATIVE_FIELDS:
            if normalized not in QUALITATIVE_VALUES:
                return f"Invalid value for {field}"
        elif field == "industry":
            if normalized not in INDUSTRY_VALUES:
                return f"Invalid value for {field}"
    return None


def _extract_custom_weights(data: Dict[str, Any]) -> Dict[str, float] | None:
    """
    Extract optional custom weights from request JSON.

    Expected structure:
        \"weights\": {\"budget\": float, \"scalability\": float, ...}

    If the structure is missing or invalid, returns None so that the
    scoring engine can fall back to default weights.
    """
    weights = data.get("weights")
    if not isinstance(weights, dict):
        return None

    extracted: Dict[str, float] = {}
    for field in WEIGHT_FIELDS:
        value = weights.get(field)
        if not isinstance(value, (int, float)):
            return None
        extracted[field] = float(value)

    return extracted


def _extract_region(data: Dict[str, Any]) -> str | None:
    """
    Extract optional deployment region from request JSON.
    Returns normalized region ("india" | "us" | "europe") if valid, else None.
    """
    raw = data.get("region")
    if not isinstance(raw, str):
        return None
    normalized = raw.strip().lower()
    return normalized if normalized in REGION_VALUES else None


@bp.route("/recommend", methods=["GET", "POST"])
def recommend():
    """
    GET: usage hint. POST: cloud provider and service model recommendation.
    """
    if request.method == "GET":
        return jsonify({
            "message": "Use POST with a JSON body to get a recommendation.",
            "required_fields": REQUIRED_FIELDS,
            "example_values": {
                "budget": "low | medium | high",
                "industry": "general | fintech | healthcare | ai",
            },
        }), 200

    logger.info("recommend | called")

    if not request.is_json:
        logger.warning("recommend | invalid input | content-type not json")
        return jsonify({"error": "Content-Type must be application/json."}), 400

    data = request.get_json(silent=True)
    user_input, validation_error = _validate_payload(data)
    if validation_error:
        logger.warning("recommend | invalid input | %s", validation_error)
        return jsonify({"error": validation_error}), 400

    value_error = _validate_field_values(user_input)
    if value_error:
        logger.warning("recommend | invalid input | %s", value_error)
        return jsonify({"error": value_error}), 400

    custom_weights = _extract_custom_weights(data)
    region = _extract_region(data)

    try:
        provider_scores = calculate_provider_scores(user_input, custom_weights, region=region)
    except (TypeError, ValueError) as e:
        logger.warning("recommend | invalid input | %s", str(e))
        return jsonify({"error": str(e)}), 400

    service_model_result = determine_service_model(user_input)

    if not provider_scores:
        logger.error("recommend | error | no provider scores computed")
        return jsonify({"error": "No provider scores computed."}), 500

    selected_provider = max(provider_scores, key=provider_scores.get)
    explanation: List[str] = generate_explanation(
        user_input,
        provider_scores,
        selected_provider,
        service_model_result,
    )
    try:
        explanation_enhanced: str = enhance_explanation_with_ai(explanation)
    except Exception as e:
        logger.warning("recommend | AI explanation failed, using deterministic | %s", e)
        explanation_enhanced = "\n\n".join(explanation) if explanation else "No explanation available."

    estimated_costs: Dict[str, float] = {}
    for pid in ("aws", "azure", "gcp"):
        estimated_costs[pid] = calculate_estimated_cost(user_input, pid)

    logger.info(
        "recommend | success | provider=%s | service_model=%s",
        selected_provider,
        service_model_result.get("service_model", "IaaS"),
    )

    response: Dict[str, Any] = {
        "recommended_provider": selected_provider,
        "recommended_service_model": service_model_result.get(
            "service_model", "IaaS"
        ),
        "final_scores": provider_scores,
        "estimated_costs": estimated_costs,
        "explanation": explanation,
        "explanation_raw": explanation,
        "explanation_enhanced": explanation_enhanced,
    }

    return jsonify(response), 200
