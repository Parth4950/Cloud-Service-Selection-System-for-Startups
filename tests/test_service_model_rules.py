"""
Unit tests for service model rules. Tests determine_service_model only.
"""

from app.core.service_model_rules import determine_service_model


def test_fintech_returns_iaas():
    result = determine_service_model({"industry": "fintech"})
    assert result["service_model"] == "IaaS"
    assert "reason" in result


def test_healthcare_returns_paaS():
    result = determine_service_model({"industry": "healthcare"})
    assert result["service_model"] == "PaaS"
    assert "reason" in result


def test_low_team_expertise_returns_saas():
    result = determine_service_model({"team_expertise": "low"})
    assert result["service_model"] == "SaaS"
    assert "reason" in result


def test_default_case_returns_iaas():
    result = determine_service_model({"industry": "general", "team_expertise": "none"})
    assert result["service_model"] == "IaaS"
    assert "reason" in result
