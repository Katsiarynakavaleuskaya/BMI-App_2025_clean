"""
Tests for Food Merge Pipeline
"""

import asyncio
import os
import tempfile
from unittest.mock import AsyncMock, Mock, patch

import pytest

from core.food_merge_pipeline import FoodMergePipeline


class TestFoodMergePipeline:
    """Test Food Merge Pipeline."""

    def setup_method(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.pipeline = FoodMergePipeline(data_dir=self.test_dir)

    def teardown_method(self):
        """Clean up test environment."""
        # Clean up test files
        for file in os.listdir(self.test_dir):
            os.remove(os.path.join(self.test_dir, file))
        os.rmdir(self.test_dir)

    @pytest.mark.asyncio
    async def test_fetch_usda_data(self):
        """Test fetching data from USDA."""
        # Mock USDA client
        mock_usda_item = Mock()
        mock_usda_item.description = "Chicken Breast"
        mock_usda_item.nutrients_per_100g = {
            "energy_kcal": 165,
            "protein_g": 31.0,
            "fat_g": 3.6,
            "carbohydrate_g": 0.0,
            "fiber_g": 0.0,
            "iron_mg": 0.7,
            "calcium_mg": 15.0,
            "vitamin_d_iu": 28.0,
            "vitamin_b12_ug": 0.3,
            "folate_ug": 6.0,
            "iodine_ug": 7.0,
            "potassium_mg": 256.0,
            "magnesium_mg": 27.0,
        }

        with patch.object(self.pipeline.usda_client, 'search_foods',
                         new=AsyncMock(return_value=[mock_usda_item])):
            result = await self.pipeline.fetch_usda_data("chicken breast")

            assert len(result) == 1
            assert result[0]["name"] == "Chicken Breast"
            assert result[0]["kcal"] == 165
            assert result[0]["protein_g"] == 31.0
            assert result[0]["source"] == "USDA"

    @pytest.mark.asyncio
    async def test_fetch_off_data(self):
        """Test fetching data from OpenFoodFacts."""
        if not self.pipeline.off_client:
            pytest.skip("OpenFoodFacts client not available")

        # Mock OFF client
        mock_off_item = Mock()
        mock_off_item.product_name = "Chicken Breast"
        mock_off_item.nutrients_per_100g = {
            "energy-kcal": 165,
            "protein_g": 31.0,
            "fat_g": 3.6,
            "carbs_g": 0.0,
            "fiber_g": 0.0,
            "iron_mg": 0.7,
            "calcium_mg": 15.0,
            "vitamin_d_iu": 28.0,
            "b12_ug": 0.3,
            "folate_ug": 6.0,
            "iodine_ug": 7.0,
            "potassium_mg": 256.0,
            "magnesium_mg": 27.0,
        }
        mock_off_item.labels = []
        mock_off_item.allergens_tags = []

        with patch.object(self.pipeline.off_client, 'search_products',
                         new=AsyncMock(return_value=[mock_off_item])):
            result = await self.pipeline.fetch_off_data("chicken breast")

            assert len(result) == 1
            assert result[0]["name"] == "Chicken Breast"
            assert result[0]["kcal"] == 165
            assert result[0]["price_per_unit"] == 0.0  # Default value since OFF doesn't provide price
            assert result[0]["source"] == "OpenFoodFacts"

    @pytest.mark.asyncio
    async def test_run_merge_pipeline(self):
        """Test running the full merge pipeline."""
        # Mock USDA client
        mock_usda_item = Mock()
        mock_usda_item.description = "Chicken Breast"
        mock_usda_item.nutrients_per_100g = {
            "energy_kcal": 165,
            "protein_g": 31.0,
            "fat_g": 3.6,
            "carbohydrate_g": 0.0,
            "fiber_g": 0.0,
            "iron_mg": 0.7,
            "calcium_mg": 15.0,
            "vitamin_d_iu": 28.0,
            "vitamin_b12_ug": 0.3,
            "folate_ug": 6.0,
            "iodine_ug": 7.0,
            "potassium_mg": 256.0,
            "magnesium_mg": 27.0,
        }

        # Mock OFF client
        mock_off_item = Mock()
        mock_off_item.product_name = "Chicken Breast"
        mock_off_item.nutrients_per_100g = {
            "energy-kcal": 165,
            "protein_g": 31.0,
            "fat_g": 3.6,
            "carbs_g": 0.0,
            "fiber_g": 0.0,
            "iron_mg": 0.7,
            "calcium_mg": 15.0,
            "vitamin_d_iu": 28.0,
            "b12_ug": 0.3,
            "folate_ug": 6.0,
            "iodine_ug": 7.0,
            "potassium_mg": 256.0,
            "magnesium_mg": 27.0,
        }
        mock_off_item.labels = []
        mock_off_item.allergens_tags = []

        with patch.object(self.pipeline.usda_client, 'search_foods',
                         new=AsyncMock(return_value=[mock_usda_item])):
            with patch.object(self.pipeline.off_client, 'search_products',
                             new=AsyncMock(return_value=[mock_off_item])):
                records = await self.pipeline.run_merge_pipeline(["chicken breast"], "test_output.csv")

                assert len(records) == 1
                assert records[0]["name"] == "chicken_breast"
                assert records[0]["group"] == "protein"
                assert records[0]["kcal"] == 165.0

                # Check that file was created
                filepath = os.path.join(self.test_dir, "test_output.csv")
                assert os.path.exists(filepath)

    @pytest.mark.asyncio
    async def test_extract_flags_from_off(self):
        """Test extracting flags from OpenFoodFacts item."""
        # Create mock OFF item with various label combinations
        mock_off_item = Mock()

        # Test vegetarian flag
        mock_off_item.labels = ['en:vegetarian']
        mock_off_item.allergens_tags = []
        flags = self.pipeline._extract_flags_from_off(mock_off_item)
        assert "VEG" in flags

        # Test vegan flag
        mock_off_item.labels = ['en:vegan']
        flags = self.pipeline._extract_flags_from_off(mock_off_item)
        assert "VEG" in flags

        # Test gluten-free flag
        mock_off_item.labels = ['en:gluten-free']
        flags = self.pipeline._extract_flags_from_off(mock_off_item)
        assert "GF" in flags

        # Test dairy-free flag
        mock_off_item.labels = ['en:no-milk']
        flags = self.pipeline._extract_flags_from_off(mock_off_item)
        assert "DAIRY_FREE" in flags

        # Test no special flags
        mock_off_item.labels = ['en:organic']
        flags = self.pipeline._extract_flags_from_off(mock_off_item)
        assert len(flags) == 0

    def test_merge_nutrient_values(self):
        """Test merging nutrient values with different strategies."""
        # Test median calculation
        values = [10.0, 20.0, 30.0]
        result = self.pipeline._merge_nutrient_values(values, "Fe_mg", ["USDA", "OFF"])
        assert result == 20.0

        # Test with empty values
        result = self.pipeline._merge_nutrient_values([], "Fe_mg", ["USDA", "OFF"])
        assert result == 0.0

        # Test with None values
        values = [10.0, None, 30.0]
        result = self.pipeline._merge_nutrient_values(values, "Fe_mg", ["USDA", "OFF"])
        assert result == 20.0

        # Test with negative values
        values = [10.0, -5.0, 30.0]
        result = self.pipeline._merge_nutrient_values(values, "Fe_mg", ["USDA", "OFF"])
        assert result == 20.0

    def test_classify_food_group(self):
        """Test food group classification."""
        # High protein food (lean)
        record = {
            "name": "Chicken Breast",
            "kcal": 165,
            "protein_g": 31.0,
            "fat_g": 3.6,
            "carbs_g": 0.0,
            "fiber_g": 0.0
        }
        group = self.pipeline._classify_food_group(record)
        assert group == "protein"

        # High fat food
        record = {
            "name": "Olive Oil",
            "kcal": 884,
            "protein_g": 0.0,
            "fat_g": 100.0,
            "carbs_g": 0.0,
            "fiber_g": 0.0
        }
        group = self.pipeline._classify_food_group(record)
        assert group == "fat"

        # Grain (high carb, low fiber)
        record = {
            "name": "White Rice",
            "kcal": 130,
            "protein_g": 2.7,
            "fat_g": 0.3,
            "carbs_g": 28.2,
            "fiber_g": 0.4
        }
        group = self.pipeline._classify_food_group(record)
        assert group == "grain"

        # Legume (contains legume keyword and high fiber)
        record = {
            "name": "Lentils",
            "kcal": 116,
            "protein_g": 9.0,
            "fat_g": 0.4,
            "carbs_g": 20.0,
            "fiber_g": 8.0
        }
        group = self.pipeline._classify_food_group(record)
        assert group == "legume"

        # Vegetable (high fiber, low calories)
        record = {
            "name": "Spinach",
            "kcal": 23,
            "protein_g": 2.9,
            "fat_g": 0.4,
            "carbs_g": 3.6,
            "fiber_g": 2.2
        }
        group = self.pipeline._classify_food_group(record)
        assert group == "veg"

        # Fruit
        record = {
            "name": "Banana",
            "kcal": 89,
            "protein_g": 1.1,
            "fat_g": 0.3,
            "carbs_g": 23.0,
            "fiber_g": 2.6
        }
        group = self.pipeline._classify_food_group(record)
        assert group == "fruit"

        # High protein food with higher fat (e.g., nuts)
        record = {
            "name": "Almonds",
            "kcal": 579,
            "protein_g": 21.2,
            "fat_g": 49.9,
            "carbs_g": 21.6,
            "fiber_g": 12.5
        }
        group = self.pipeline._classify_food_group(record)
        assert group == "protein"

    def test_classify_food_group_edge_cases(self):
        """Test food group classification edge cases."""
        # Test other category
        record = {
            "name": "Unknown Food",
            "kcal": 0,
            "protein_g": 0,
            "fat_g": 0,
            "carbs_g": 0,
            "fiber_g": 0
        }
        group = self.pipeline._classify_food_group(record)
        assert group == "other"

        # Test dairy classification
        record = {
            "name": "Milk",
            "kcal": 61,
            "protein_g": 3.3,
            "fat_g": 3.6,
            "carbs_g": 4.7,
            "fiber_g": 0.0
        }
        group = self.pipeline._classify_food_group(record)
        # Should be protein since it's high in protein (>15% of calories)
        assert group == "protein"

    def test_save_to_csv(self):
        """Test saving records to CSV."""
        records = [
            {
                "name": "Chicken Breast",
                "group": "protein",
                "per_g": 100.0,
                "kcal": 165.0,
                "protein_g": 31.0,
                "fat_g": 3.6,
                "carbs_g": 0.0,
                "fiber_g": 0.0,
                "Fe_mg": 0.7,
                "Ca_mg": 15.0,
                "VitD_IU": 28.0,
                "B12_ug": 0.3,
                "Folate_ug": 6.0,
                "Iodine_ug": 7.0,
                "K_mg": 256.0,
                "Mg_mg": 27.0,
                "flags": ["LOW_FAT"],
                "price_per_unit": 5.99,
                "source": "MERGED(USDA,OpenFoodFacts)",
                "version_date": "2025-01-01T00:00:00"
            }
        ]

        filename = "test_food_db.csv"
        self.pipeline.save_to_csv(records, filename)

        # Check that file was created
        filepath = os.path.join(self.test_dir, filename)
        assert os.path.exists(filepath)

        # Check file contents
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            assert "Chicken Breast" in content
            assert "protein" in content
            assert "165.0" in content
            assert "LOW_FAT" in content

    @pytest.mark.asyncio
    async def test_merge_food_sources(self):
        """Test merging food sources."""
        # Mock USDA client
        mock_usda_item = Mock()
        mock_usda_item.description = "Chicken Breast"
        mock_usda_item.nutrients_per_100g = {
            "energy_kcal": 165,
            "protein_g": 31.0,
            "fat_g": 3.6,
            "carbohydrate_g": 0.0,
            "fiber_g": 0.0,
            "iron_mg": 0.7,
            "calcium_mg": 15.0,
            "vitamin_d_iu": 28.0,
            "vitamin_b12_ug": 0.3,
            "folate_ug": 6.0,
            "iodine_ug": 7.0,
            "potassium_mg": 256.0,
            "magnesium_mg": 27.0,
        }

        # Mock OFF client
        mock_off_item = Mock()
        mock_off_item.product_name = "Chicken Breast"
        mock_off_item.nutrients_per_100g = {
            "energy-kcal": 165,
            "protein_g": 31.0,
            "fat_g": 3.6,
            "carbs_g": 0.0,
            "fiber_g": 0.0,
            "iron_mg": 0.7,
            "calcium_mg": 15.0,
            "vitamin_d_iu": 28.0,
            "b12_ug": 0.3,
            "folate_ug": 6.0,
            "iodine_ug": 7.0,
            "potassium_mg": 256.0,
            "magnesium_mg": 27.0,
        }
        mock_off_item.labels = []
        mock_off_item.allergens_tags = []

        with patch.object(self.pipeline.usda_client, 'search_foods',
                         new=AsyncMock(return_value=[mock_usda_item])):
            with patch.object(self.pipeline.off_client, 'search_products',
                             new=AsyncMock(return_value=[mock_off_item])):
                records = await self.pipeline.merge_food_sources(["chicken breast"])

                assert len(records) == 1
                assert records[0]["name"] == "chicken_breast"
                assert records[0]["group"] == "protein"
                assert records[0]["kcal"] == 165.0

    @pytest.mark.asyncio
    async def test_fetch_usda_data_error_handling(self):
        """Test error handling in USDA data fetching."""
        with patch.object(self.pipeline.usda_client, 'search_foods',
                         new=AsyncMock(side_effect=Exception("API Error"))):
            result = await self.pipeline.fetch_usda_data("chicken breast")
            assert result == []

    @pytest.mark.asyncio
    async def test_fetch_off_data_error_handling(self):
        """Test error handling in OFF data fetching."""
        if not self.pipeline.off_client:
            pytest.skip("OpenFoodFacts client not available")

        with patch.object(self.pipeline.off_client, 'search_products',
                         new=AsyncMock(side_effect=Exception("API Error"))):
            result = await self.pipeline.fetch_off_data("chicken breast")
            assert result == []

    def test_resolve_conflicts(self):
        """Test conflict resolution between records."""
        records = [
            {
                "name": "Chicken Breast",
                "kcal": 165,
                "protein_g": 31.0,
                "fat_g": 3.6,
                "carbs_g": 0.0,
                "fiber_g": 0.0,
                "Fe_mg": 0.7,
                "Ca_mg": 15.0,
                "source": "USDA",
                "flags": ["LOW_FAT"],
                "price_per_unit": 0.0
            },
            {
                "name": "Chicken Breast",
                "kcal": 170,
                "protein_g": 30.0,
                "fat_g": 4.0,
                "carbs_g": 0.0,
                "fiber_g": 0.0,
                "Fe_mg": 0.8,
                "Ca_mg": 16.0,
                "source": "OpenFoodFacts",
                "flags": ["ORGANIC"],
                "price_per_unit": 5.99
            }
        ]

        result = self.pipeline._resolve_conflicts(records)

        # Check that values are merged correctly
        assert result["kcal"] == 167.5  # median of [165, 170]
        assert result["protein_g"] == 30.5  # median of [31.0, 30.0]
        # For micronutrients, USDA values are prioritized
        assert result["Fe_mg"] == 0.7  # USDA value (priority) instead of median 0.75
        assert "LOW_FAT" in result["flags"]
        assert "ORGANIC" in result["flags"]
        assert result["price_per_unit"] == 5.99  # prefer OFF price

    def test_resolve_conflicts_edge_cases(self):
        """Test conflict resolution edge cases."""
        # Test with empty records
        result = self.pipeline._resolve_conflicts([])
        assert result == {}

        # Test with single record
        record = {
            "name": "Chicken Breast",
            "kcal": 165,
            "protein_g": 31.0,
            "fat_g": 3.6,
            "carbs_g": 0.0,
            "fiber_g": 0.0,
            "Fe_mg": 0.7,
            "Ca_mg": 15.0,
            "source": "USDA",
            "flags": ["LOW_FAT"],
            "price_per_unit": 0.0
        }
        result = self.pipeline._resolve_conflicts([record])
        assert result["name"] == "Chicken Breast"
        assert result["kcal"] == 165
        assert result["Fe_mg"] == 0.7
        assert result["flags"] == ["LOW_FAT"]

    def test_save_to_csv_formatting(self):
        """Test CSV saving with proper formatting."""
        records = [
            {
                "name": "Chicken Breast",
                "group": "protein",
                "per_g": 100.0,
                "kcal": 165.0,
                "protein_g": 31.0,
                "fat_g": 3.6,
                "carbs_g": 0.0,
                "fiber_g": 0.0,
                "Fe_mg": 0.7,
                "Ca_mg": 15.0,
                "VitD_IU": 28.0,
                "B12_ug": 0.3,
                "Folate_ug": 6.0,
                "Iodine_ug": 7.0,
                "K_mg": 256.0,
                "Mg_mg": 27.0,
                "flags": ["LOW_FAT", "HIGH_PROTEIN"],
                "price_per_unit": 5.99,
                "source": "MERGED(USDA,OpenFoodFacts)",
                "version_date": "2025-01-01T00:00:00"
            }
        ]

        filename = "test_formatting.csv"
        self.pipeline.save_to_csv(records, filename)

        # Check that file was created
        filepath = os.path.join(self.test_dir, filename)
        assert os.path.exists(filepath)

        # Check file contents
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            assert "Chicken Breast" in content
            assert "LOW_FAT;HIGH_PROTEIN" in content  # Check flags formatting
