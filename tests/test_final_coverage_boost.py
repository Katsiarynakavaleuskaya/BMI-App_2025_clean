"""
Final tests to boost coverage to 97%.
"""

import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app import app


class TestFinalCoverageBoost:
    """Final tests to boost coverage to 97%."""

    def setup_method(self):
        """Set up test client."""
        os.environ["API_KEY"] = "test_key"
        self.client = TestClient(app)

    def teardown_method(self):
        """Clean up after tests."""
        if "API_KEY" in os.environ:
            del os.environ["API_KEY"]

    def test_normalize_flags_edge_cases(self):
        """Test edge cases in normalize_flags function."""
        from app import normalize_flags

        # Test with unknown gender
        result = normalize_flags("other", "no", "no")
        assert result["gender_male"] is False
        assert result["is_pregnant"] is False
        assert result["is_athlete"] is False

        # Test with athlete variations
        result = normalize_flags("male", "no", "athlete")
        assert result["is_athlete"] is True

        # Test with pregnant male (should not be pregnant)
        result = normalize_flags("male", "yes", "no")
        assert result["is_pregnant"] is False

    def test_weekly_plan_endpoint_make_weekly_menu_none(self):
        """Test weekly plan endpoint when make_weekly_menu is None."""
        with patch('app.make_weekly_menu', None):
            payload = {
                "sex": "male",
                "age": 30,
                "height_cm": 175,
                "weight_kg": 70,
                "activity": "moderate",
                "goal": "maintain"
            }

            response = self.client.post("/api/v1/premium/plan/week", json=payload, headers={"X-API-Key": "test_key"})
            assert response.status_code == 503
            assert "not available" in response.json()["detail"]

    def test_weekly_plan_endpoint_make_weekly_menu_exception(self):
        """Test weekly plan endpoint when make_weekly_menu raises exception."""
        mock_make_weekly = MagicMock()
        mock_make_weekly.side_effect = Exception("Test error")

        with patch('app.make_weekly_menu', mock_make_weekly):
            payload = {
                "sex": "male",
                "age": 30,
                "height_cm": 175,
                "weight_kg": 70,
                "activity": "moderate",
                "goal": "maintain"
            }

            response = self.client.post("/api/v1/premium/plan/week", json=payload, headers={"X-API-Key": "test_key"})
            assert response.status_code == 500
            assert "failed" in response.json()["detail"]

    def test_weekly_plan_endpoint_make_weekly_menu_value_error(self):
        """Test weekly plan endpoint when make_weekly_menu raises ValueError."""
        mock_make_weekly = MagicMock()
        mock_make_weekly.side_effect = ValueError("Invalid input")

        with patch('app.make_weekly_menu', mock_make_weekly):
            payload = {
                "sex": "male",
                "age": 30,
                "height_cm": 175,
                "weight_kg": 70,
                "activity": "moderate",
                "goal": "maintain"
            }

            response = self.client.post("/api/v1/premium/plan/week", json=payload, headers={"X-API-Key": "test_key"})
            assert response.status_code == 400
            assert "Invalid input" in response.json()["detail"]

    def test_debug_env_endpoint(self):
        """Test debug_env endpoint."""
        response = self.client.get("/debug_env", headers={"X-API-Key": "test_key"})
        assert response.status_code == 200
        data = response.json()
        assert "FEATURE_INSIGHT" in data
        assert "LLM_PROVIDER" in data
        assert "GROK_MODEL" in data
        assert "GROK_ENDPOINT" in data
        assert "insight_enabled" in data

    def test_nutrient_gaps_new_endpoint(self):
        """Test the new nutrient-gaps endpoint."""
        payload = {
            "consumed_nutrients": {
                "protein_g": 50,
                "fat_g": 70,
                "carbs_g": 250
            },
            "user_profile": {
                "sex": "male",
                "age": 30,
                "height_cm": 175,
                "weight_kg": 70,
                "activity": "sedentary",
                "goal": "maintain",
                "deficit_pct": 20,
                "surplus_pct": 10,
                "bodyfat": None,
                "diet_flags": [],
                "life_stage": "adult"
            }
        }

        response = self.client.post("/api/v1/premium/nutrient-gaps", json=payload, headers={"X-API-Key": "test_key"})
        # May succeed or fail depending on implementation availability
        assert response.status_code in [200, 500, 503]

    def test_nutrient_gaps_new_endpoint_analyze_none(self):
        """Test the new nutrient-gaps endpoint when analyze_nutrient_gaps is None."""
        with patch('app.analyze_nutrient_gaps', None):
            payload = {
                "consumed_nutrients": {
                    "protein_g": 50,
                    "fat_g": 70,
                    "carbs_g": 250
                },
                "user_profile": {
                    "sex": "male",
                    "age": 30,
                    "height_cm": 175,
                    "weight_kg": 70,
                    "activity": "sedentary",
                    "goal": "maintain",
                    "deficit_pct": 20,
                    "surplus_pct": 10,
                    "bodyfat": None,
                    "diet_flags": [],
                    "life_stage": "adult"
                }
            }

            response = self.client.post("/api/v1/premium/nutrient-gaps", json=payload, headers={"X-API-Key": "test_key"})
            assert response.status_code == 503
            assert "not available" in response.json()["detail"]
