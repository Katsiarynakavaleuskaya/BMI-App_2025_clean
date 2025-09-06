import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

from app import app

client = TestClient(app)


class _StubProvider:
    """Stub provider for testing."""

    name = "stub"

    def generate(self, text):
        return f"insight::{text[::-1]}"


class _StubProviderException:
    """Stub provider that raises an exception."""

    name = "stub"

    def generate(self, text):
        raise RuntimeError("Generate failed")


def test_insight_with_monkeypatched_provider(monkeypatch):
    # Подменяем фабрику провайдера на заглушку
    monkeypatch.setattr("llm.get_provider", lambda: _StubProvider())

    r = client.post(
        "/api/v1/insight",
        json={"text": "hello"},
        headers={"X-API-Key": "test_key"}
    )
    assert r.status_code == 200
    data = r.json()
    assert data.get("insight", "").startswith("insight::")
    assert "hello"[::-1] in data["insight"]


def test_insight_with_provider_exception(monkeypatch):
    # Подменяем фабрику провайдера на заглушку, которая вызывает исключение
    monkeypatch.setattr("llm.get_provider", lambda: _StubProviderException())

    r = client.post(
        "/api/v1/insight",
        json={"text": "error"},
        headers={"X-API-Key": "test_key"}
    )
    assert r.status_code == 503
    data = r.json()
    assert "unavailable" in data.get("detail", "")


def test_insight_no_provider(monkeypatch):
    # Подменяем фабрику провайдера на None
    monkeypatch.setattr("llm.get_provider", lambda: None)

    r = client.post(
        "/api/v1/insight",
        json={"text": "test"},
        headers={"X-API-Key": "test_key"}
    )
    assert r.status_code == 503
    data = r.json()
    assert "not configured" in data.get("detail", "")


def test_health_smoke():
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    d = r.json()
    assert d.get("status") == "ok"


def test_api_v1_insight_provider_none(monkeypatch):
    # Подменяем фабрику провайдера на None
    monkeypatch.setattr("llm.get_provider", lambda: None)

    r = client.post(
        "/api/v1/insight",
        json={"text": "test"},
        headers={"X-API-Key": "test_key"}
    )
    assert r.status_code == 503
    data = r.json()
    assert "insight provider not configured" in data.get("detail", "")


def test_api_v1_insight_generate_exception(monkeypatch):
    # Подменяем generate, чтобы вызвать исключение
    class StubProvider:
        name = "stub"

        def generate(self, text):
            raise RuntimeError("Generate failed")

    monkeypatch.setattr("llm.get_provider", lambda: StubProvider())

    r = client.post(
        "/api/v1/insight",
        json={"text": "test"},
        headers={"X-API-Key": "test_key"}
    )
    assert r.status_code == 503
    data = r.json()
    assert "insight provider unavailable" in data.get("detail", "")


def test_insight_feature_disabled():
    # Устанавливаем FEATURE_INSIGHT в false
    import os
    original = os.environ.get("FEATURE_INSIGHT")
    os.environ["FEATURE_INSIGHT"] = "false"

    r = client.post("/insight", json={"text": "test"}, headers={"X-API-Key": "test_key"})
    assert r.status_code == 503
    data = r.json()
    assert "disabled" in data.get("detail", "")

    # Restore original value
    if original is not None:
        os.environ["FEATURE_INSIGHT"] = original
    elif "FEATURE_INSIGHT" in os.environ:
        del os.environ["FEATURE_INSIGHT"]


def test_insight_no_llm_provider_env():
    # Устанавливаем LLM_PROVIDER в пустое
    import os
    original = os.environ.get("LLM_PROVIDER")
    os.environ["LLM_PROVIDER"] = ""

    r = client.post("/insight", json={"text": "test"}, headers={"X-API-Key": "test_key"})
    assert r.status_code == 503
    data = r.json()
    assert "No LLM provider configured" in data.get("detail", "")

    # Restore original value
    if original is not None:
        os.environ["LLM_PROVIDER"] = original
    elif "LLM_PROVIDER" in os.environ:
        del os.environ["LLM_PROVIDER"]


def test_insight_provider_none():
    # Устанавливаем LLM_PROVIDER, но get_provider возвращает None
    import os
    original = os.environ.get("LLM_PROVIDER")
    os.environ["LLM_PROVIDER"] = "stub"

    # Monkeypatch get_provider
    import llm
    original_get_provider = llm.get_provider
    llm.get_provider = lambda: None

    r = client.post("/insight", json={"text": "test"}, headers={"X-API-Key": "test_key"})
    assert r.status_code == 503
    data = r.json()
    assert "No LLM provider configured" in data.get("detail", "")

    # Restore original values
    if original is not None:
        os.environ["LLM_PROVIDER"] = original
    elif "LLM_PROVIDER" in os.environ:
        del os.environ["LLM_PROVIDER"]
    llm.get_provider = original_get_provider


def test_insight_generate_exception(monkeypatch):
    # Подменяем generate
    class StubProvider:
        name = "stub"

        def generate(self, text):
            raise RuntimeError("Generate failed")

    monkeypatch.setattr("llm.get_provider", lambda: StubProvider())

    # Set FEATURE_INSIGHT to enable the endpoint
    import os
    original = os.environ.get("FEATURE_INSIGHT")
    original_provider = os.environ.get("LLM_PROVIDER")
    os.environ["FEATURE_INSIGHT"] = "true"
    os.environ["LLM_PROVIDER"] = "stub"

    r = client.post("/insight", json={"text": "test"}, headers={"X-API-Key": "test_key"})
    assert r.status_code == 503
    data = r.json()
    assert "unavailable" in data.get("detail", "")

    # Restore original values
    if original is not None:
        os.environ["FEATURE_INSIGHT"] = original
    elif "FEATURE_INSIGHT" in os.environ:
        del os.environ["FEATURE_INSIGHT"]
    if original_provider is not None:
        os.environ["LLM_PROVIDER"] = original_provider
    elif "LLM_PROVIDER" in os.environ:
        del os.environ["LLM_PROVIDER"]


def test_insight_success(monkeypatch):
    # Подменяем generate to succeed
    class StubProvider:
        name = "stub"

        def generate(self, text):
            return f"insight::{text[::-1]}"

    monkeypatch.setattr("llm.get_provider", lambda: StubProvider())

    # Set FEATURE_INSIGHT to enable the endpoint
    import os
    original = os.environ.get("FEATURE_INSIGHT")
    original_provider = os.environ.get("LLM_PROVIDER")
    os.environ["FEATURE_INSIGHT"] = "true"
    os.environ["LLM_PROVIDER"] = "stub"

    r = client.post("/insight", json={"text": "hello"}, headers={"X-API-Key": "test_key"})
    assert r.status_code == 200
    data = r.json()
    assert data.get("insight", "").startswith("insight::")
    assert "hello"[::-1] in data["insight"]

    # Restore original values
    if original is not None:
        os.environ["FEATURE_INSIGHT"] = original
    elif "FEATURE_INSIGHT" in os.environ:
        del os.environ["FEATURE_INSIGHT"]
    if original_provider is not None:
        os.environ["LLM_PROVIDER"] = original_provider
    elif "LLM_PROVIDER" in os.environ:
        del os.environ["LLM_PROVIDER"]


def test_insight_debug_env():
    # Set debug environment
    import os
    original_debug = os.environ.get("DEBUG")
    os.environ["DEBUG"] = "1"

    # This test just checks that the endpoint exists and doesn't crash
    # We don't check the response content as it may vary
    r = client.get("/")
    assert r.status_code == 200

    # Restore original value
    if original_debug is not None:
        os.environ["DEBUG"] = original_debug
    elif "DEBUG" in os.environ:
        del os.environ["DEBUG"]


def test_insight_metrics():
    r = client.get("/metrics")
    assert r.status_code == 200
    data = r.json()
    assert "uptime_seconds" in data


def test_insight_privacy():
    r = client.get("/privacy")
    assert r.status_code == 200
    data = r.json()
    assert "policy" in data


def test_insight_favicon():
    r = client.get("/favicon.ico")
    assert r.status_code == 204


def test_insight_health():
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data.get("status") == "ok"


def test_api_v1_health():
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    data = r.json()
    assert data.get("status") == "ok"
    assert data.get("version") == "v1"


def test_bmi_endpoint_with_waist_risk_ru():
    req = {
        "weight_kg": 70,
        "height_m": 1.75,
        "age": 30,
        "gender": "male",
        "pregnant": "no",
        "athlete": "no",
        "waist_cm": 95,  # High risk for male
        "lang": "ru"
    }
    r = client.post("/bmi", json=req, headers={"X-API-Key": "test_key"})
    assert r.status_code == 200
    data = r.json()
    assert "note" in data
    assert "риск" in data["note"]  # Risk in Russian


def test_bmi_endpoint_with_waist_risk_en():
    req = {
        "weight_kg": 70,
        "height_m": 1.75,
        "age": 30,
        "gender": "male",
        "pregnant": "no",
        "athlete": "no",
        "waist_cm": 95,  # High risk for male
        "lang": "en"
    }
    r = client.post("/bmi", json=req, headers={"X-API-Key": "test_key"})
    assert r.status_code == 200
    data = r.json()
    assert "note" in data
    assert "risk" in data["note"].lower()


def test_bmi_endpoint_high_waist_risk_ru():
    req = {
        "weight_kg": 70,
        "height_m": 1.75,
        "age": 30,
        "gender": "female",
        "pregnant": "no",
        "athlete": "no",
        "waist_cm": 90,  # High risk for female
        "lang": "ru"
    }
    r = client.post("/bmi", json=req, headers={"X-API-Key": "test_key"})
    assert r.status_code == 200
    data = r.json()
    assert "note" in data
    assert "риск" in data["note"]  # Risk in Russian


def test_bmi_endpoint_high_waist_risk_en():
    req = {
        "weight_kg": 70,
        "height_m": 1.75,
        "age": 30,
        "gender": "female",
        "pregnant": "no",
        "athlete": "no",
        "waist_cm": 90,  # High risk for female
        "lang": "en"
    }
    r = client.post("/bmi", json=req, headers={"X-API-Key": "test_key"})
    assert r.status_code == 200
    data = r.json()
    assert "note" in data
    assert "risk" in data["note"].lower()


def test_bmi_endpoint_athlete_note_ru():
    req = {
        "weight_kg": 70,
        "height_m": 1.75,
        "age": 30,
        "gender": "male",
        "pregnant": "no",
        "athlete": "yes",  # Athlete
        "lang": "ru"
    }
    r = client.post("/bmi", json=req, headers={"X-API-Key": "test_key"})
    assert r.status_code == 200
    data = r.json()
    assert "note" in data
    assert "спортсмен" in data["note"]  # Athlete note in Russian


def test_bmi_endpoint_athlete_note_en():
    req = {
        "weight_kg": 70,
        "height_m": 1.75,
        "age": 30,
        "gender": "male",
        "pregnant": "no",
        "athlete": "yes",  # Athlete
        "lang": "en"
    }
    r = client.post("/bmi", json=req, headers={"X-API-Key": "test_key"})
    assert r.status_code == 200
    data = r.json()
    assert "note" in data
    assert "athlete" in data["note"].lower()


def test_plan_endpoint_ru():
    req = {
        "weight_kg": 70,
        "height_m": 1.75,
        "age": 30,
        "gender": "male",
        "pregnant": "no",
        "athlete": "no",
        "lang": "ru"
    }
    r = client.post("/plan", json=req, headers={"X-API-Key": "test_key"})
    assert r.status_code == 200
    data = r.json()
    assert "summary" in data
    assert "Персональный" in data["summary"]  # Personal in Russian


def test_plan_endpoint_en():
    req = {
        "weight_kg": 70,
        "height_m": 1.75,
        "age": 30,
        "gender": "male",
        "pregnant": "no",
        "athlete": "no",
        "lang": "en"
    }
    r = client.post("/plan", json=req, headers={"X-API-Key": "test_key"})
    assert r.status_code == 200
    data = r.json()
    assert "summary" in data
    assert "Personal" in data["summary"]


def test_api_v1_bmi_success():
    req = {
        "weight_kg": 70,
        "height_cm": 170,
        "group": "general"
    }
    r = client.post("/api/v1/bmi", json=req, headers={"X-API-Key": "test_key"})
    assert r.status_code == 200
    data = r.json()
    assert "bmi" in data
    assert "category" in data
    assert "interpretation" in data


def test_api_v1_bmi_invalid_height():
    req = {
        "weight_kg": 70,
        "height_cm": 0,
        "group": "general"
    }
    r = client.post("/api/v1/bmi", json=req, headers={"X-API-Key": "test_key"})
    assert r.status_code == 422
    data = r.json()
    assert "detail" in data


def test_api_v1_bmi_invalid_weight():
    req = {
        "weight_kg": 0,
        "height_cm": 170,
        "group": "general"
    }
    r = client.post("/api/v1/bmi", json=req, headers={"X-API-Key": "test_key"})
    assert r.status_code == 422
    data = r.json()
    assert "detail" in data


def test_insight_bodyfat_router_none(monkeypatch):
    # Подменяем get_bodyfat_router на None
    monkeypatch.setattr("app.get_bodyfat_router", lambda: None)

    # Перезапускаем app, но поскольку это модульный тест, просто проверяем, что роутер не добавлен
    # This test just verifies the app doesn't crash when bodyfat router is None
    r = client.get("/health")
    assert r.status_code == 200


def test_insight_bodyfat_router_not_none(monkeypatch):
    # Подменяем get_bodyfat_router на mock
    mock_router_func = MagicMock()
    mock_router = MagicMock()
    mock_router_func.return_value = mock_router
    monkeypatch.setattr("app.get_bodyfat_router", mock_router_func)

    # This test just verifies the app doesn't crash when bodyfat router is available
    r = client.get("/health")
    assert r.status_code == 200


def test_insight_llm_import_fail(monkeypatch):
    # Mock the import to fail
    import sys
    original_llm = sys.modules.get('llm')
    if 'llm' in sys.modules:
        del sys.modules['llm']

    # Mock builtins.__import__ to raise for llm
    original_import = __builtins__['__import__']

    def mock_import(name, *args, **kwargs):
        if name == 'llm':
            raise ImportError("Mocked import error")
        return original_import(name, *args, **kwargs)

    __builtins__['__import__'] = mock_import

    # Set FEATURE_INSIGHT to enable the endpoint
    import os
    original = os.environ.get("FEATURE_INSIGHT")
    original_provider = os.environ.get("LLM_PROVIDER")
    os.environ["FEATURE_INSIGHT"] = "true"
    os.environ["LLM_PROVIDER"] = "stub"

    r = client.post("/insight", json={"text": "test"}, headers={"X-API-Key": "test_key"})
    assert r.status_code == 503
    data = r.json()
    assert "not available" in data.get("detail", "")

    # Restore original values
    __builtins__['__import__'] = original_import
    if original_llm is not None:
        sys.modules['llm'] = original_llm
    if original is not None:
        os.environ["FEATURE_INSIGHT"] = original
    elif "FEATURE_INSIGHT" in os.environ:
        del os.environ["FEATURE_INSIGHT"]
    if original_provider is not None:
        os.environ["LLM_PROVIDER"] = original_provider
    elif "LLM_PROVIDER" in os.environ:
        del os.environ["LLM_PROVIDER"]
