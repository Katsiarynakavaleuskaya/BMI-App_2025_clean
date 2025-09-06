"""
Tests for Premium Week router additional coverage.
"""

import os
import sys
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

# Create a test client with just the premium_week router
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
    def test_premium_week_endpoint_missing_profile_data(
        self, mock_build_week, mock_recipe_db, mock_food_db
    ):
        """Test premium week endpoint with missing required data."""
        # Mock the dependencies
        mock_build_week.return_value = {
            "days": [],
            "weekly_coverage": {},
            "shopping_list": []
        }

        # Test data with missing required fields (invalid JSON for targets)
        test_data = {
            "targets": "{invalid json",
            "diet_flags": "",
            "lang": "en"
        }

        response = client.post(
            "/api/v1/premium/plan/week",
            json=test_data,
            headers={"X-API-Key": "test_key"}
        )
        # Should fail with 500 due to JSON parsing error
        assert response.status_code == 500

    @patch('app.routers.premium_week.FoodDB')
    @patch('app.routers.premium_week.RecipeDB')
    @patch('app.routers.premium_week.build_week')
    def test_premium_week_endpoint_targets_derivation_failure(
        self, mock_build_week, mock_recipe_db, mock_food_db
    ):
        """Test premium week endpoint when build_week fails."""
        # Mock build_week to raise an exception
        mock_build_week.side_effect = Exception("Failed to build week")

        # Test data with valid targets
        test_data = {
            "targets": '{"kcal": 2000, "macros": {"protein_g": 100, '
                       '"fat_g": 70, "carbs_g": 250, "fiber_g": 25}}',
            "diet_flags": "",
            "lang": "en"
        }

        response = client.post(
            "/api/v1/premium/plan/week",
            json=test_data,
            headers={"X-API-Key": "test_key"}
        )
        # Should fail with 500 due to build_week failure
        assert response.status_code == 500

    @patch('app.routers.premium_week.FoodDB')
    @patch('app.routers.premium_week.RecipeDB')
    @patch('app.routers.premium_week.build_week')
    @patch('app.routers.premium_week.to_csv_premium_week')
    def test_premium_week_export_csv_success(
        self, mock_to_csv, mock_build_week, mock_recipe_db, mock_food_db
    ):
        """Test premium week CSV export endpoint success."""
        # Mock the dependencies
        mock_build_week.return_value = {
            "days": [],
            "weekly_coverage": {},
            "shopping_list": []
        }
        mock_to_csv.return_value = b"test,csv,data"

        url = (
            "/api/v1/premium/plan/week/export/csv"
            "?targets={}&diet_flags=&lang=en"
        )
        response = client.get(
            url,
            headers={"X-API-Key": "test_key"}
        )
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]
        assert "attachment" in response.headers["content-disposition"]

    @patch('app.routers.premium_week.FoodDB')
    @patch('app.routers.premium_week.RecipeDB')
    @patch('app.routers.premium_week.build_week')
    @patch('app.routers.premium_week.to_csv_premium_week')
    def test_premium_week_export_csv_failure(
        self, mock_to_csv, mock_build_week, mock_recipe_db, mock_food_db
    ):
        """Test premium week CSV export endpoint failure."""
        # Mock build_week to raise an exception
        mock_build_week.side_effect = Exception("Failed to build week")

        url = (
            "/api/v1/premium/plan/week/export/csv"
            "?targets={}&diet_flags=&lang=en"
        )
        response = client.get(
            url,
            headers={"X-API-Key": "test_key"}
        )
        assert response.status_code == 500

    @patch('app.routers.premium_week.FoodDB')
    @patch('app.routers.premium_week.RecipeDB')
    @patch('app.routers.premium_week.build_week')
    @patch('app.routers.premium_week.to_pdf_premium_week')
    def test_premium_week_export_pdf_success(
        self, mock_to_pdf, mock_build_week, mock_recipe_db, mock_food_db
    ):
        """Test premium week PDF export endpoint success."""
        # Mock the dependencies
        mock_build_week.return_value = {
            "days": [],
            "weekly_coverage": {},
            "shopping_list": []
        }
        mock_to_pdf.return_value = b"test,pdf,data"

        url = (
            "/api/v1/premium/plan/week/export/pdf"
            "?targets={}&diet_flags=&lang=en"
        )
        response = client.get(
            url,
            headers={"X-API-Key": "test_key"}
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "attachment" in response.headers["content-disposition"]

    @patch('app.routers.premium_week.FoodDB')
    @patch('app.routers.premium_week.RecipeDB')
    @patch('app.routers.premium_week.build_week')
    @patch('app.routers.premium_week.to_pdf_premium_week')
    def test_premium_week_export_pdf_failure(
        self, mock_to_pdf, mock_build_week, mock_recipe_db, mock_food_db
    ):
        """Test premium week PDF export endpoint failure."""
        # Mock build_week to raise an exception
        mock_build_week.side_effect = Exception("Failed to build week")

        url = (
            "/api/v1/premium/plan/week/export/pdf"
            "?targets={}&diet_flags=&lang=en"
        )
        response = client.get(
            url,
            headers={"X-API-Key": "test_key"}
        )
        assert response.status_code == 500
