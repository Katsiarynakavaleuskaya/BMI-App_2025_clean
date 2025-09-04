"""Extra tests for core.food_merge to improve coverage."""

from core.food_merge import _classify_food_group, _merge_values, merge_records
from core.food_sources.base import FoodRecord


def test_merge_values_first_strategy_and_filtering():
    vals = [None, -1.0, 0.0, 2.5]
    # "first" strategy picks first non-negative, non-None value
    assert _merge_values(vals, strategy="first") == 0.0


def test_micro_pick_median_fallback_when_no_usda():
    # Two OFF sources, ensure micronutrient comes from median of all
    r1 = FoodRecord(
        name="lentils",
        locale="en",
        per_g=100.0,
        kcal=100,
        protein_g=9,
        fat_g=1,
        carbs_g=18,
        fiber_g=8,
        Fe_mg=6.0,
        Ca_mg=20,
        VitD_IU=0,
        B12_ug=0,
        Folate_ug=180,
        Iodine_ug=3,
        K_mg=300,
        Mg_mg=35,
        flags=["VEG"],
        price=0.0,
        source="OFF",
        version_date="2025-01-01",
    )
    r2 = FoodRecord(
        name="lentils",
        locale="en",
        per_g=100.0,
        kcal=102,
        protein_g=8.8,
        fat_g=1.2,
        carbs_g=17.5,
        fiber_g=7.5,
        Fe_mg=5.0,
        Ca_mg=18,
        VitD_IU=0,
        B12_ug=0,
        Folate_ug=170,
        Iodine_ug=4,
        K_mg=310,
        Mg_mg=33,
        flags=["GF", "VEG"],
        price=0.0,
        source="OFF",
        version_date="2025-01-01",
    )
    merged = merge_records([[r1], [r2]])
    assert len(merged) == 1
    m = merged[0]
    # Iron median of [6.0, 5.0] = 5.5
    assert m["Fe_mg"] == 5.5


def test_classify_paths_fat_veg_dairy_and_default():
    # High fat profile -> "fat"
    rec_fat = {
        "protein_g": 5.0,
        "fat_g": 15.0,
        "carbs_g": 5.0,
        "fiber_g": 1.0,
        "kcal": 200.0,
        "flags": [],
    }
    assert _classify_food_group(rec_fat) == "fat"

    # Vegetable-like (low kcal, good fiber) -> "veg"
    # Ensure carb_pct <= 50 to hit veg path (outside high-carb branch)
    rec_veg = {
        "protein_g": 2.0,
        "fat_g": 0.5,
        "carbs_g": 5.0,
        "fiber_g": 3.0,
        "kcal": 60.0,
        "flags": [],
    }
    assert _classify_food_group(rec_veg) == "veg"

    # Dairy flagged -> "dairy"
    rec_dairy = {
        "protein_g": 1.0,
        "fat_g": 1.5,
        "carbs_g": 6.0,
        "fiber_g": 0.0,
        "kcal": 90.0,
        "flags": ["DAIRY"],
    }
    assert _classify_food_group(rec_dairy) == "dairy"

    # Default path -> "other"
    rec_other = {
        "protein_g": 0.1,
        "fat_g": 0.1,
        "carbs_g": 0.1,
        "fiber_g": 0.0,
        "kcal": 50.0,
        "flags": [],
    }
    assert _classify_food_group(rec_other) == "other"
