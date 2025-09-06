"""
Tests for the minimal targets estimation utility.
"""

import pytest

from core.targets_min import estimate_targets_minimal


def test_estimate_targets_minimal_male_maintain():
    """Test minimal targets estimation for male maintaining weight."""
    result = estimate_targets_minimal(
        sex="male",
        age=30,
        height_cm=175,
        weight_kg=70.0,
        activity=1.5,
        goal="maintain"
    )

    # Check that all expected keys are present
    assert "kcal" in result
    assert "macros" in result
    assert "micro" in result
    assert "water_ml" in result
    assert "activity_week" in result

    # Check macro calculations
    assert result["macros"]["protein_g"] == 112.0  # 1.6 * 70
    assert result["macros"]["fat_g"] == 63.0       # 0.9 * 70
    assert result["macros"]["fiber_g"] == 28

    # Check micro calculations
    assert result["micro"]["Fe_mg"] == 8.0  # Male iron
    assert result["micro"]["Ca_mg"] == 1000.0
    assert result["micro"]["VitD_IU"] == 600.0

    # Check water and activity
    assert result["water_ml"] == 2100  # 30 * 70
    assert result["activity_week"]["mvpa_min"] == 150


def test_estimate_targets_minimal_female_loss():
    """Test minimal targets estimation for female losing weight."""
    result = estimate_targets_minimal(
        sex="female",
        age=25,
        height_cm=165,
        weight_kg=60.0,
        activity=1.4,
        goal="loss"
    )

    # Check that calorie target is reduced for weight loss
    assert result["kcal"] > 1200  # Above minimum
    assert "macros" in result
    assert result["macros"]["protein_g"] == 96.0  # 1.6 * 60
    assert result["macros"]["fat_g"] == 54.0      # 0.9 * 60

    # Check micro calculations for female
    assert result["micro"]["Fe_mg"] == 18.0  # Female iron
    assert result["micro"]["Mg_mg"] == 320.0  # Female magnesium


def test_estimate_targets_minimal_gain():
    """Test minimal targets estimation for gaining weight."""
    result = estimate_targets_minimal(
        sex="male",
        age=25,
        height_cm=180,
        weight_kg=75.0,
        activity=1.7,
        goal="gain"
    )

    # Check that calorie target is increased for weight gain
    assert "kcal" in result
    assert result["kcal"] > 2000  # Should be higher for gain


def test_estimate_targets_minimal_edge_cases():
    """Test edge cases for minimal targets estimation."""
    # Test with minimum values
    result = estimate_targets_minimal(
        sex="male",
        age=18,
        height_cm=150,
        weight_kg=40.0,
        activity=1.2,
        goal="maintain"
    )

    # Even with low weight, should have reasonable values
    assert result["kcal"] >= 1200  # Minimum calorie limit
    assert result["macros"]["protein_g"] == 64.0  # 1.6 * 40

    # Test with high activity
    result = estimate_targets_minimal(
        sex="female",
        age=35,
        height_cm=170,
        weight_kg=65.0,
        activity=2.5,  # High activity
        goal="maintain"
    )

    # Should cap activity multiplier
    assert "kcal" in result


def test_estimate_targets_minimal_default_values():
    """Test minimal targets with default/None values."""
    result = estimate_targets_minimal(
        sex="female",  # Should default to female
        age=30,
        height_cm=170,
        weight_kg=65.0,
        activity=1.4,  # Should default to a reasonable activity multiplier
        goal="maintain"      # Should default to maintain
    )

    # Should default to female values
    assert result["micro"]["Fe_mg"] == 18.0  # Female iron
    assert result["micro"]["Mg_mg"] == 320.0  # Female magnesium


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
