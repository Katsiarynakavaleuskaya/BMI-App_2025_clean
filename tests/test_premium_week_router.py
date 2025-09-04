"""
Tests for Premium Week router additional coverage.
"""

import os
import sys
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

# Create a test client with just the premium_week router
from fastapi import FastAPI

from app.routers.premium_week import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)


class TestPremiumWeekRouter:
    """Test Premium Week router additional coverage."""

    def setup_method(self):
        """Set up test client."""
        os.environ["API_KEY"] = "test_key"

    def teardown_method(self):
        """Clean up test environment."""
        if "API_KEY" in os.environ:
            del os.environ["API_KEY"]

    @patch('app.routers.premium_week.FoodDB')
    @patch('app.routers.premium_week.RecipeDB')
    @patch('app.routers.premium_week.build_week')
    @patch('app.routers.premium_week.build_nutrition_targets')
    def test_premium_week_endpoint_missing_profile_data(self, mock_build_targets, mock_build_week, mock_recipe_db, mock_food_db):
        """Test premium week endpoint with missing user profile data."""
        # Mock the dependencies
        mock_build_week.return_value = {
            "days": [],
            "weekly_coverage": {},
            "shopping_list": []
        }

        # Test data with missing required fields
        test_data = {
            "sex": "male",
            "age": 30,
            # Missing height_cm, weight_kg
            "activity": "moderate",
            "goal": "maintain",
            "diet_flags": [],
            "lang": "en"
        }

        response = client.post("/api/v1/premium/plan/week", json=test_data, headers={"X-API-Key": "test_key"})
        # Should fail with 400 due to missing required data
        assert response.status_code == 400

    @patch('app.routers.premium_week.FoodDB')
    @patch('app.routers.premium_week.RecipeDB')
    @patch('app.routers.premium_week.build_week')
    @patch('app.routers.premium_week.build_nutrition_targets')
    @patch('app.routers.premium_week.estimate_targets_minimal')
    def test_premium_week_endpoint_targets_derivation_failure(self, mock_estimate_targets, mock_build_targets, mock_build_week, mock_recipe_db, mock_food_db):
        """Test premium week endpoint when targets derivation fails."""
        # Mock the dependencies
        mock_estimate_targets.return_value = None
        mock_build_week.return_value = {
            "days": [],
            "weekly_coverage": {},
            "shopping_list": []
        }

        # Test data with complete profile
        test_data = {
            "sex": "male",
            "age": 30,
            "height_cm": 180,
            "weight_kg": 75,
            "activity": "moderate",
            "goal": "maintain",
            "diet_flags": [],
            "lang": "en"
        }

        response = client.post("/api/v1/premium/plan/week", json=test_data, headers={"X-API-Key": "test_key"})
        # Should fail with 400 due to targets derivation failure
        assert response.status_code == 400
