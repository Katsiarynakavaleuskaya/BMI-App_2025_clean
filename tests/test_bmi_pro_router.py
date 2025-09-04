"""
Tests for BMI Pro router.
"""

import os
import sys
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

# Create a test client with just the bmi_pro router
from fastapi import FastAPI

from app.routers.bmi_pro import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)


class TestBMIProRouter:
    """Test BMI Pro router."""

    def test_bmi_pro_endpoint_success(self):
        """Test successful BMI Pro analysis via router."""
        data = {
            "height_cm": 175.0,
            "weight_kg": 70.0,
            "sex": "male",
            "age": 30,
            "waist_cm": 85.0,
            "hip_cm": 100.0,
            "bodyfat_percent": 20.0,
            "lang": "en"
        }

        response = client.post("/api/v1/bmi/pro", json=data)
        assert response.status_code == 200

        result = response.json()
        assert "bmi" in result
        assert "whtr" in result
        assert "whr" in result
        assert "ffmi" in result
        assert "risk_level" in result
        assert "notes" in result
        assert result["bmi"] == pytest.approx(22.9, 0.1)
        assert result["whtr"] == pytest.approx(0.486, 0.01)  # Adjusted tolerance

    def test_bmi_pro_endpoint_minimal_data(self):
        """Test BMI Pro analysis with minimal data (no hip or bodyfat) via router."""
        data = {
            "height_cm": 175.0,
            "weight_kg": 70.0,
            "sex": "female",
            "age": 30,
            "waist_cm": 80.0,
            "lang": "en"
        }

        response = client.post("/api/v1/bmi/pro", json=data)
        assert response.status_code == 200

        result = response.json()
        assert "bmi" in result
        assert "whtr" in result
        # WHR and FFMI should be None when not provided
        assert result["whr"] is None
        assert result["ffmi"] is None

    def test_bmi_pro_endpoint_invalid_data(self):
        """Test BMI Pro analysis with invalid data via router."""
        data = {
            "height_cm": 175.0,
            "weight_kg": -70.0,  # Invalid weight
            "sex": "male",
            "age": 30,
            "waist_cm": 85.0,
            "lang": "en"
        }

        response = client.post("/api/v1/bmi/pro", json=data)
        assert response.status_code == 422  # Validation error

    @patch('app.routers.bmi_pro.wht_ratio')
    def test_bmi_pro_endpoint_internal_error(self, mock_wht_ratio):
        """Test BMI Pro endpoint when internal function raises ValueError."""
        mock_wht_ratio.side_effect = ValueError("Invalid input")

        data = {
            "height_cm": 175.0,
            "weight_kg": 70.0,
            "sex": "male",
            "age": 30,
            "waist_cm": 85.0,
            "lang": "en"
        }

        response = client.post("/api/v1/bmi/pro", json=data)
        assert response.status_code == 400  # Bad request due to internal error
