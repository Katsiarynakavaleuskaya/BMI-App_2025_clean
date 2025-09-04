"""
Tests for Food Merge Logic

RU: Тесты для логики мерджа данных о продуктах.
EN: Tests for food merge logic.
"""

from typing import Iterable, List
from unittest.mock import Mock

import pytest

from core.food_merge import FoodRecord, _classify_food_group, _merge_values, merge_records


def test_merge_values():
    """Test merging values with different strategies."""
    # Test median strategy
    values = [10.0, 20.0, 30.0]
    result = _merge_values(values, "median")
    assert result == 20.0

    # Test first strategy
    values = [10.0, 20.0, 30.0]
    result = _merge_values(values, "first")
    assert result == 10.0

    # Test with empty values
    result = _merge_values([], "median")
    assert result == 0.0

    # Test with None values
    values = [10.0, None, 30.0]
    result = _merge_values(values, "median")
    assert result == 20.0

    # Test with negative values
    values = [10.0, -5.0, 30.0]
    result = _merge_values(values, "median")
    assert result == 20.0


def test_classify_food_group():
    """Test food group classification."""
    # Test protein classification (high protein, >15% of calories)
    record = {
        "kcal": 165,
        "protein_g": 31.0,
        "fat_g": 3.6,
        "carbs_g": 0.0,
        "fiber_g": 0.0,
        "sugar_g": 0.0,
        "flags": []
    }
    group = _classify_food_group(record)
    assert group == "protein"

    # Test fat classification (>30% of calories from fat)
    record = {
        "kcal": 884,
        "protein_g": 0.0,
        "fat_g": 100.0,
        "carbs_g": 0.0,
        "fiber_g": 0.0,
        "sugar_g": 0.0,
        "flags": []
    }
    group = _classify_food_group(record)
    assert group == "fat"

    # Test grain classification (>50% of calories from carbs, low fiber)
    record = {
        "kcal": 130,
        "protein_g": 2.7,
        "fat_g": 0.3,
        "carbs_g": 28.2,
        "fiber_g": 0.4,
        "sugar_g": 0.0,
        "flags": []
    }
    group = _classify_food_group(record)
    assert group == "grain"

    # Test vegetable classification (moderate carbs, high fiber, low calories)
    # Need to adjust values so protein % is not >15% and carb % is not >50%
    record = {
        "name": "spinach",
        "kcal": 23,
        "protein_g": 0.8,  # Lower protein content to get <15% of calories
        "fat_g": 0.4,
        "carbs_g": 2.5,  # Lower carbs to get <50% of calories
        "fiber_g": 5.2,  # Higher fiber content
        "sugar_g": 0.0,
        "flags": []
    }
    group = _classify_food_group(record)
    assert group == "veg"

    # Test other classification
    record = {
        "kcal": 0,
        "protein_g": 0,
        "fat_g": 0,
        "carbs_g": 0,
        "fiber_g": 0,
        "sugar_g": 0,
        "flags": []
    }
    group = _classify_food_group(record)
    assert group == "other"


def test_merge_records():
    """Test merging records from multiple sources."""
    # Create mock records
    record1 = Mock(spec=FoodRecord)
    record1.name = "chicken_breast"
    record1.kcal = 165
    record1.protein_g = 31.0
    record1.fat_g = 3.6
    record1.carbs_g = 0.0
    record1.fiber_g = 0.0
    record1.Fe_mg = 0.7
    record1.Ca_mg = 15.0
    record1.VitD_IU = 28.0
    record1.B12_ug = 0.3
    record1.Folate_ug = 6.0
    record1.Iodine_ug = 7.0
    record1.K_mg = 256.0
    record1.Mg_mg = 27.0
    record1.flags = ["LOW_FAT"]
    record1.source = "USDA"

    record2 = Mock(spec=FoodRecord)
    record2.name = "chicken_breast"
    record2.kcal = 170
    record2.protein_g = 30.0
    record2.fat_g = 4.0
    record2.carbs_g = 0.0
    record2.fiber_g = 0.0
    record2.Fe_mg = 0.8
    record2.Ca_mg = 16.0
    record2.VitD_IU = 29.0
    record2.B12_ug = 0.4
    record2.Folate_ug = 7.0
    record2.Iodine_ug = 8.0
    record2.K_mg = 260.0
    record2.Mg_mg = 28.0
    record2.flags = ["ORGANIC"]
    record2.source = "OpenFoodFacts"

    # Test merging
    streams: List[Iterable[FoodRecord]] = [[record1, record2]]
    merged = merge_records(streams)

    assert len(merged) == 1
    merged_record = merged[0]
    assert merged_record["name"] == "chicken_breast"
    assert merged_record["kcal"] == 167.5  # median of [165, 170]
    assert merged_record["protein_g"] == 30.5  # median of [31.0, 30.0]
    # For micronutrients, since both records are from different sources,
    # it should use the USDA value (0.7) as priority
    assert merged_record["Fe_mg"] == 0.7  # USDA value (priority) instead of median 0.75
    assert "LOW_FAT" in merged_record["flags"]
    assert "ORGANIC" in merged_record["flags"]
    assert merged_record["group"] == "protein"


def test_merge_records_empty():
    """Test merging with empty streams."""
    streams = []
    merged = merge_records(streams)
    assert merged == []


def test_merge_records_single_source():
    """Test merging with single source."""
    record = Mock(spec=FoodRecord)
    record.name = "chicken_breast"
    record.kcal = 165
    record.protein_g = 31.0
    record.fat_g = 3.6
    record.carbs_g = 0.0
    record.fiber_g = 0.0
    record.Fe_mg = 0.7
    record.Ca_mg = 15.0
    record.VitD_IU = 28.0
    record.B12_ug = 0.3
    record.Folate_ug = 6.0
    record.Iodine_ug = 7.0
    record.K_mg = 256.0
    record.Mg_mg = 27.0
    record.flags = ["LOW_FAT"]
    record.source = "USDA"

    streams: List[Iterable[FoodRecord]] = [[record]]
    merged = merge_records(streams)

    assert len(merged) == 1
    merged_record = merged[0]
    assert merged_record["name"] == "chicken_breast"
    assert merged_record["kcal"] == 165.0
    assert merged_record["protein_g"] == 31.0
    assert merged_record["Fe_mg"] == 0.7
    assert merged_record["flags"] == ["LOW_FAT"]
    assert merged_record["group"] == "protein"


if __name__ == "__main__":
    pytest.main([__file__])
