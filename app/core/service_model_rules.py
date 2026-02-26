"""
Service and model rules: rule-based selection of IaaS / PaaS / SaaS.
Deterministic conditional mapping from user_input; no scoring or provider selection.
"""

from typing import Dict, Any

from app.core.config import SERVICE_MODEL_RULES

# Mapping from industry rule key (from config) to service model.
# Extend when new industries are added to SERVICE_MODEL_RULES["industry"].
INDUSTRY_TO_SERVICE_MODEL: Dict[str, str] = {
    "healthcare": "PaaS",
    "finance": "IaaS",
    "startup": "PaaS",
    "enterprise": "IaaS",
    "default": "IaaS",
}

# Mapping from team_expertise rule key (from config) to service model.
TEAM_EXPERTISE_TO_SERVICE_MODEL: Dict[str, str] = {
    "high": "IaaS",
    "medium": "PaaS",
    "low": "SaaS",
    "default": "PaaS",
}

# Fallback when no industry or team_expertise rule matches.
DEFAULT_SERVICE_MODEL = "IaaS"

VALID_SERVICE_MODELS = frozenset({"IaaS", "PaaS", "SaaS"})


def determine_service_model(user_input: Dict[str, Any]) -> Dict[str, str]:
    """
    Determine service model (IaaS / PaaS / SaaS) from user_input using
    SERVICE_MODEL_RULES. Industry is checked first, then team_expertise;
    if neither matches, returns the default service model.

    Args:
        user_input: Dict with optional "industry" and "team_expertise" keys.
            Values should match rule keys in config (e.g. "healthcare", "high").
            Missing or invalid keys are handled defensively.

    Returns:
        Dict with:
          - "service_model": "IaaS" | "PaaS" | "SaaS"
          - "reason": Human-readable explanation of why this model was chosen.
    """
    if not isinstance(user_input, dict):
        raise TypeError("user_input must be a dict")

    industry_rules = SERVICE_MODEL_RULES.get("industry") or {}
    expertise_rules = SERVICE_MODEL_RULES.get("team_expertise") or {}

    industry = user_input.get("industry")
    if industry is not None and isinstance(industry, str):
        industry_key = industry.strip().lower()
        if industry_key in industry_rules:
            service_model = INDUSTRY_TO_SERVICE_MODEL.get(
                industry_key, DEFAULT_SERVICE_MODEL
            )
            return {
                "service_model": service_model,
                "reason": f"Matched industry rule: {industry_key}. "
                f"Recommended service model: {service_model}.",
            }

    team_expertise = user_input.get("team_expertise")
    if team_expertise is not None and isinstance(team_expertise, str):
        expertise_key = team_expertise.strip().lower()
        if expertise_key in expertise_rules:
            service_model = TEAM_EXPERTISE_TO_SERVICE_MODEL.get(
                expertise_key, DEFAULT_SERVICE_MODEL
            )
            return {
                "service_model": service_model,
                "reason": f"Matched team_expertise rule: {expertise_key}. "
                f"Recommended service model: {service_model}.",
            }

    return {
        "service_model": DEFAULT_SERVICE_MODEL,
        "reason": "No industry or team_expertise rule matched. "
        f"Using default service model: {DEFAULT_SERVICE_MODEL}.",
    }
