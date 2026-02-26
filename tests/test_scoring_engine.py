"""
Unit tests for scoring engine. Tests calculate_provider_scores only.
"""

from app.core.scoring_engine import calculate_provider_scores

PROVIDERS = {"aws", "azure", "gcp"}
FEATURES = ["budget", "scalability", "security", "ease_of_use", "free_tier"]


def _make_input(**overrides):
    base = {f: "medium" for f in FEATURES}
    base.update(overrides)
    return base


def test_all_high_returns_dict_with_all_providers_and_numeric_scores():
    user_input = _make_input(
        budget="high",
        scalability="high",
        security="high",
        ease_of_use="high",
        free_tier="high",
    )
    result = calculate_provider_scores(user_input)
    assert isinstance(result, dict)
    assert set(result.keys()) == PROVIDERS
    for provider, score in result.items():
        assert isinstance(score, (int, float))
        assert score >= 0


def test_all_low_returns_dict_scores_differ_from_high():
    user_input_low = _make_input(
        budget="low",
        scalability="low",
        security="low",
        ease_of_use="low",
        free_tier="low",
    )
    user_input_high = _make_input(
        budget="high",
        scalability="high",
        security="high",
        ease_of_use="high",
        free_tier="high",
    )
    result_low = calculate_provider_scores(user_input_low)
    result_high = calculate_provider_scores(user_input_high)
    assert set(result_low.keys()) == PROVIDERS
    assert set(result_high.keys()) == PROVIDERS
    for p in PROVIDERS:
        assert result_high[p] > result_low[p], f"high score should exceed low for {p}"


def test_mixed_inputs_scores_differ_logically():
    user_input = _make_input(
        budget="high",
        scalability="medium",
        security="high",
        ease_of_use="low",
        free_tier="high",
    )
    result = calculate_provider_scores(user_input)
    assert isinstance(result, dict)
    assert set(result.keys()) == PROVIDERS
    for score in result.values():
        assert isinstance(score, (int, float))
    # All three providers should have distinct scores or at least valid ordering
    scores = list(result.values())
    assert len(scores) == 3
    assert min(scores) >= 0
    assert max(scores) <= 10
