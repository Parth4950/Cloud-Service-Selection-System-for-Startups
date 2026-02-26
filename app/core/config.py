"""
Configuration and environment settings for the application.
Centralizes app config; no logic, placeholder for future values.
Static configuration for provider comparison and service model rules.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env: first from current working directory, then from project root.
# Ensures .env is found whether you run from project root or elsewhere.
load_dotenv()
_project_root = Path(__file__).resolve().parent.parent.parent
_env_path = _project_root / ".env"
if _env_path.exists():
    load_dotenv(_env_path)

# ---------------------------------------------------------------------------
# Provider catalog: feature scores (3–10 scale). Each provider is specialized
# with clear strengths and weaknesses so different inputs yield different winners.
# ---------------------------------------------------------------------------

PROVIDER_CATALOG = {
    "aws": {
        "feature_scores": {
            "scalability": 10,
            "security": 9,
            "ease_of_use": 7,
            "budget": 6,
            "free_tier": 5,
        },
        "strengths": [
            "Broadest service catalog and global footprint",
            "Strong enterprise and compliance offerings",
            "Leading scalability and security",
        ],
    },
    "azure": {
        "feature_scores": {
            "security": 10,
            "scalability": 8,
            "ease_of_use": 6,
            "budget": 5,
            "free_tier": 4,
        },
        "strengths": [
            "Deep integration with Microsoft stack and hybrid cloud",
            "Strong compliance and government offerings",
            "Top-tier security and enterprise focus",
        ],
    },
    "gcp": {
        "feature_scores": {
            "free_tier": 10,
            "budget": 9,
            "ease_of_use": 9,
            "scalability": 7,
            "security": 6,
        },
        "strengths": [
            "Strong data and ML/AI capabilities",
            "Generous free tier and sustained-use discounts",
            "Cost-effective and developer-friendly",
        ],
    },
}

# ---------------------------------------------------------------------------
# Weights for feature dimensions (must sum to 1.0).
# Easily adjustable for tuning recommendations.
# ---------------------------------------------------------------------------

WEIGHT_CONFIG = {
    "budget": 0.25,
    "scalability": 0.20,
    "security": 0.25,
    "ease_of_use": 0.15,
    "free_tier": 0.15,
}

# ---------------------------------------------------------------------------
# Regional advantage modifiers: small boost per provider per region.
# Applied after base scoring. Optional; if no region provided, no modifier.
# ---------------------------------------------------------------------------

REGION_PROVIDER_MODIFIERS = {
    "india": {
        "aws": 0.2,
        "azure": 0.3,
        "gcp": 0.1,
    },
    "us": {
        "aws": 0.3,
        "azure": 0.2,
        "gcp": 0.2,
    },
    "europe": {
        "aws": 0.2,
        "azure": 0.3,
        "gcp": 0.2,
    },
}

# ---------------------------------------------------------------------------
# Mock pricing: base monthly compute + storage (USD). Used for cost estimate.
# ---------------------------------------------------------------------------

MOCK_PRICING = {
    "aws": {
        "base_compute": 120,
        "base_storage": 40,
    },
    "azure": {
        "base_compute": 110,
        "base_storage": 45,
    },
    "gcp": {
        "base_compute": 100,
        "base_storage": 35,
    },
}

# ---------------------------------------------------------------------------
# Optional AI explanation layer. Loaded from .env; never log or expose the key.
# When ENABLE_AI_EXPLANATION is false or GEMINI_API_KEY missing, only deterministic explanation is used.
# ---------------------------------------------------------------------------

def _env_bool(value: str | None) -> bool:
    """Convert env string to boolean safely. true/1/yes (case-insensitive) -> True."""
    if not value:
        return False
    return value.strip().lower() in ("true", "1", "yes")

GEMINI_API_KEY = (os.environ.get("GEMINI_API_KEY") or "").strip() or None
ENABLE_AI_EXPLANATION = _env_bool((os.environ.get("ENABLE_AI_EXPLANATION") or "false").strip())

# Log AI explanation config at import (no key value). Helps confirm .env was loaded.
import logging as _logging
_logging.getLogger(__name__).info(
    "config | ENABLE_AI_EXPLANATION=%s | GEMINI_API_KEY=%s",
    ENABLE_AI_EXPLANATION,
    "set" if GEMINI_API_KEY else "not set",
)

# ---------------------------------------------------------------------------
# Service/model rules: conditions keyed by industry and team_expertise.
# Structured data only; rule evaluation is done elsewhere.
# ---------------------------------------------------------------------------

SERVICE_MODEL_RULES = {
    "industry": {
        "healthcare": {
            "preferred_providers": ["aws", "azure"],
            "required_features": ["security"],
            "constraints": {"compliance": ["hipaa"]},
        },
        "finance": {
            "preferred_providers": ["aws", "azure"],
            "required_features": ["security", "scalability"],
            "constraints": {"compliance": ["pci", "soc2"]},
        },
        "startup": {
            "preferred_providers": ["gcp", "aws"],
            "required_features": ["free_tier", "budget"],
            "constraints": {},
        },
        "enterprise": {
            "preferred_providers": ["aws", "azure", "gcp"],
            "required_features": ["scalability", "security"],
            "constraints": {},
        },
        "default": {
            "preferred_providers": ["aws", "azure", "gcp"],
            "required_features": [],
            "constraints": {},
        },
    },
    "team_expertise": {
        "high": {
            "preferred_providers": ["aws", "gcp", "azure"],
            "weight_overrides": None,
            "min_ease_of_use": 1,
        },
        "medium": {
            "preferred_providers": ["gcp", "aws", "azure"],
            "weight_overrides": {"ease_of_use": 0.25},
            "min_ease_of_use": 5,
        },
        "low": {
            "preferred_providers": ["gcp", "azure", "aws"],
            "weight_overrides": {"ease_of_use": 0.35},
            "min_ease_of_use": 7,
        },
        "default": {
            "preferred_providers": ["aws", "azure", "gcp"],
            "weight_overrides": None,
            "min_ease_of_use": 1,
        },
    },
}
