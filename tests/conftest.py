import pathlib
import sys

# Корень репозитория = родитель папки tests
ROOT = pathlib.Path(__file__).resolve().parent.parent
p = str(ROOT)
if p not in sys.path:
    sys.path.insert(0, p)


import os
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True, scope="session")
def _neutral_llm_env():
    for k in ("LLM_PROVIDER","GROK_ENDPOINT","GROK_MODEL","OPENAI_API_KEY","XAI_API_KEY"):
        os.environ.pop(k, None)


@pytest.fixture(autouse=True, scope="function")
def _set_api_key():
    original_api_key = os.environ.get("API_KEY")
    os.environ["API_KEY"] = "test_key"
    yield
    if original_api_key is not None:
        os.environ["API_KEY"] = original_api_key
    else:
        os.environ.pop("API_KEY", None)


@pytest.fixture(autouse=True, scope="function")
def _reset_scheduler():
    """Reset the global scheduler instance between tests."""
    import core.food_apis.scheduler
    core.food_apis.scheduler._scheduler_instance = None
    yield


@pytest.fixture
def client():
    """Create a test client for each test."""
    from fastapi.testclient import TestClient

    from app import app
    return TestClient(app)


# RU: Общие фикстуры для FoodDB/RecipeDB/targets. EN: Common fixtures.
import os

import pytest

from core.food_db_new import FoodDB
from core.recipe_db_new import RecipeDB


@pytest.fixture(scope="session")
def fooddb() -> FoodDB:
    path = os.getenv("FOOD_DB_PATH", "data/food_db_new.csv")
    return FoodDB(path)

@pytest.fixture(scope="session")
def recipedb(fooddb: FoodDB) -> RecipeDB:
    return RecipeDB("data/recipes_new.csv", fooddb)

@pytest.fixture
def targets_2200() -> dict:
    # RU: Минимальный стабильный таргет под тесты. EN: Stable target for tests.
    return {
        "kcal": 2200,
        "macros": {"protein_g": 130, "fat_g": 70, "carbs_g": 230, "fiber_g": 28},
        "micro": {
            "Fe_mg": 18.0, "Ca_mg": 1000.0, "VitD_IU": 600.0, "B12_ug": 2.4,
            "Folate_ug": 400.0, "Iodine_ug": 150.0, "K_mg": 3500.0, "Mg_mg": 320.0
        },
        "water_ml": 2000,
        "activity_week": {"mvpa_min": 150}
    }
