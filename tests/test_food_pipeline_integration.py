"""
Integration tests for Food Merge Pipeline with existing food database system
"""

import asyncio
import os
import tempfile
from unittest.mock import AsyncMock, Mock, patch

import pytest

from core.food_db import parse_food_db
from core.food_merge_pipeline import FoodMergePipeline


class TestFoodPipelineIntegration:
    """Test Food Merge Pipeline integration with existing food database system."""

    def setup_method(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.pipeline = FoodMergePipeline(data_dir=self.test_dir)
        
        # Create a new UnifiedFoodDatabase with test directory to avoid cached data interference
        # instead of setting to None which causes type errors
        from core.food_apis.unified_db import UnifiedFoodDatabase
        self.pipeline.unified_db = UnifiedFoodDatabase(cache_dir=self.test_dir)

    def teardown_method(self):
        """Clean up test environment."""
        # Clean up test files
        for file in os.listdir(self.test_dir):
            os.remove(os.path.join(self.test_dir, file))
        os.rmdir(self.test_dir)

    @pytest.mark.asyncio
    async def test_pipeline_integration_with_food_db_parser(self):
        """Test that pipeline output can be parsed by existing food_db parser."""
        # Create mock data
        mock_usda_item = Mock()
        mock_usda_item.description = "Spinach Raw"
        mock_usda_item.nutrients_per_100g = {
            "energy_kcal": 23,
            "protein_g": 2.9,
            "fat_g": 0.4,
            "carbohydrate_g": 3.6,
            "fiber_g": 2.2,
            "iron_mg": 2.7,
            "calcium_mg": 99.0,
            "vitamin_d_iu": 0.0,
            "vitamin_b12_ug": 0.0,
            "folate_ug": 194.0,
            "iodine_ug": 20.0,
            "potassium_mg": 558.0,
            "magnesium_mg": 79.0,
        }

        with patch.object(self.pipeline.usda_client, 'search_foods',
                         new=AsyncMock(return_value=[mock_usda_item])):
            with patch.object(self.pipeline.off_client, 'search_products',
                             new=AsyncMock(return_value=[])):
                # Run pipeline
                records = await self.pipeline.merge_food_sources(["spinach"])

                # Save to CSV
                filename = "test_integration_db.csv"
                self.pipeline.save_to_csv(records, filename)

                # Check that file was created
                filepath = os.path.join(self.test_dir, filename)
                assert os.path.exists(filepath)

                # Parse with existing food_db parser
                food_db = parse_food_db(filepath)

                # Verify that we have exactly one food item
                assert len(food_db) == 1
                
                # Get the single food item
                food_name, food_item = list(food_db.items())[0]
                
                # Verify the nutrient values
                assert food_item.protein_g == 2.9
                assert food_item.Fe_mg == 2.7
                assert food_item.Ca_mg == 99.0

    @pytest.mark.asyncio
    async def test_pipeline_handles_empty_results(self):
        """Test that pipeline handles empty results gracefully."""
        with patch.object(self.pipeline.usda_client, 'search_foods',
                         new=AsyncMock(return_value=[])):
            with patch.object(self.pipeline.off_client, 'search_products',
                             new=AsyncMock(return_value=[])):
                records = await self.pipeline.merge_food_sources(["nonexistent_food"])
                assert len(records) == 0

    @pytest.mark.asyncio
    async def test_pipeline_with_multiple_queries(self):
        """Test pipeline with multiple food queries."""
        # Create mock data for multiple foods
        mock_chicken = Mock()
        mock_chicken.description = "Chicken Breast"
        mock_chicken.nutrients_per_100g = {
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

        mock_salmon = Mock()
        mock_salmon.description = "Salmon"
        mock_salmon.nutrients_per_100g = {
            "energy_kcal": 208,
            "protein_g": 20.0,
            "fat_g": 13.0,
            "carbohydrate_g": 0.0,
            "fiber_g": 0.0,
            "iron_mg": 0.3,
            "calcium_mg": 9.0,
            "vitamin_d_iu": 526.0,
            "vitamin_b12_ug": 2.8,
            "folate_ug": 25.0,
            "iodine_ug": 30.0,
            "potassium_mg": 490.0,
            "magnesium_mg": 30.0,
        }

        with patch.object(self.pipeline.usda_client, 'search_foods',
                         new=AsyncMock(side_effect=[[mock_chicken], [mock_salmon]])):
            with patch.object(self.pipeline.off_client, 'search_products',
                             new=AsyncMock(return_value=[])):
                records = await self.pipeline.merge_food_sources(["chicken breast", "salmon"])

                # Save to CSV
                filename = "test_multiple_db.csv"
                self.pipeline.save_to_csv(records, filename)

                # Check that file was created with correct number of items
                filepath = os.path.join(self.test_dir, filename)
                assert os.path.exists(filepath)

                # Parse with existing food_db parser
                food_db = parse_food_db(filepath)
                assert len(food_db) == 2
                # Check that both items are present
                food_names = [item.name for item in food_db.values()]
                assert any("chicken" in name.lower() for name in food_names)
                assert any("salmon" in name.lower() for name in food_names)