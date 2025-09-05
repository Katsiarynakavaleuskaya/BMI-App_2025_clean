"""
Tests for FAO/INFOODS Client

RU: Тесты для клиента FAO/INFOODS.
EN: Tests for FAO/INFOODS client.
"""

import csv
import os
import tempfile
from unittest.mock import patch
from pathlib import Path

import pytest

from core.food_apis.fao_infoods_client import FAOInfoodsClient, FAOInfoodsFoodItem


def test_fao_infoods_client_initialization():
    """Test FAO/INFOODS client initialization with non-existent directory."""
    # Test with non-existent directory
    client = FAOInfoodsClient(data_dir="non_existent_dir")
    assert client.data_dir.name == "non_existent_dir"
    assert len(client.databases) == 0


def test_fao_infoods_client_load_databases():
    """Test FAO/INFOODS client database loading."""
    # Create a temporary directory with test CSV files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test CSV file
        csv_file = os.path.join(temp_dir, "test_db.csv")
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                "Food ID", "Food name", "Food group", "Region", "Protein (g/100g)", 
                "Fat (g/100g)", "Carbohydrate (g/100g)", "Energy (kcal)"
            ])
            writer.writeheader()
            writer.writerow({
                "Food ID": "1001",
                "Food name": "Test Food",
                "Food group": "Grains",
                "Region": "Test Region",
                "Protein (g/100g)": "10.0",
                "Fat (g/100g)": "5.0",
                "Carbohydrate (g/100g)": "70.0",
                "Energy (kcal)": "350",
            })

        # Test the client
        client = FAOInfoodsClient(data_dir=temp_dir)
        assert len(client.databases) == 1
        assert "test_db" in client.databases
        assert len(client.databases["test_db"]) == 1
        
        # Check that the food item was loaded correctly
        food_data = client.databases["test_db"][0]
        assert food_data["Food name"] == "Test Food"
        assert food_data["Protein (g/100g)"] == "10.0"
        assert food_data["Energy (kcal)"] == "350"


def test_fao_infoods_food_item_to_menu_engine_format():
    """Test FAO/INFOODS food item conversion to menu engine format."""
    # Create a FAO/INFOODS food item
    nutrients = {
        "protein_g": 10.0,
        "fat_g": 5.0,
        "carbs_g": 70.0,
        "kcal": 350,
        "calcium_mg": 50,
        "iron_mg": 2.0,
    }
    
    food_item = FAOInfoodsFoodItem(
        food_id="1001",
        food_name="Test Food",
        food_group="Grains",
        nutrients_per_100g=nutrients,
        region="Test Region",
        database_source="TestDB",
        publication_year="2020"
    )
    
    # Convert to menu engine format
    menu_format = food_item.to_menu_engine_format()
    
    # Check that all expected fields are present
    assert menu_format["name"] == "Test Food"
    assert menu_format["nutrients_per_100g"] == nutrients
    assert menu_format["cost_per_100g"] == 1.2
    assert "VEG" in menu_format["tags"]  # Should be vegetarian
    assert "VEGAN" in menu_format["tags"]  # Should be vegan
    assert "GF" in menu_format["tags"]  # Should be gluten-free
    assert menu_format["availability_regions"] == ["Test Region"]
    assert menu_format["source"] == "FAO/INFOODS TestDB"
    assert menu_format["source_id"] == "1001"


def test_fao_infoods_client_search_foods():
    """Test FAO/INFOODS client food search functionality."""
    # Create a temporary directory with test CSV files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test CSV file
        csv_file = os.path.join(temp_dir, "test_db.csv")
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                "Food ID", "Food name", "Food group", "Region", "Protein (g/100g)", 
                "Fat (g/100g)", "Carbohydrate (g/100g)", "Energy (kcal)"
            ])
            writer.writeheader()
            writer.writerow({
                "Food ID": "1001",
                "Food name": "Millet",
                "Food group": "Grains",
                "Region": "West Africa",
                "Protein (g/100g)": "11.0",
                "Fat (g/100g)": "4.3",
                "Carbohydrate (g/100g)": "73.0",
                "Energy (kcal)": "378",
            })
            writer.writerow({
                "Food ID": "1002",
                "Food name": "Cowpea",
                "Food group": "Vegetables",
                "Region": "West Africa",
                "Protein (g/100g)": "23.0",
                "Fat (g/100g)": "1.8",
                "Carbohydrate (g/100g)": "60.0",
                "Energy (kcal)": "340",
            })
        
        # Test the client
        client = FAOInfoodsClient(data_dir=temp_dir)
        
        # Search for "millet"
        results = client.search_foods("millet")
        assert len(results) == 1
        assert results[0].food_name == "Millet"
        assert results[0].food_group == "Grains"
        
        # Search for "cowpea"
        results = client.search_foods("cowpea")
        assert len(results) == 1
        assert results[0].food_name == "Cowpea"
        
        # Search for "grain" (should match millet)
        results = client.search_foods("grain")
        assert len(results) == 1
        
        # Search for non-existent item
        results = client.search_foods("steak")
        assert len(results) == 0


def test_fao_infoods_client_search_foods_nonexistent_database():
    """Test FAO/INFOODS client food search with non-existent database."""
    # Create a temporary directory with test CSV files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test CSV file
        csv_file = os.path.join(temp_dir, "test_db.csv")
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                "Food ID", "Food name", "Food group", "Region", "Protein", 
                "Fat", "Carbohydrate", "Energy"
            ])
            writer.writeheader()
            writer.writerow({
                "Food ID": "1001",
                "Food name": "Millet",
                "Food group": "Grains",
                "Region": "West Africa",
                "Protein": "11.0",
                "Fat": "4.3",
                "Carbohydrate": "73.0",
                "Energy": "378",
            })
        
        # Test the client
        client = FAOInfoodsClient(data_dir=temp_dir)
        
        # Search for "millet" in a non-existent database
        results = client.search_foods("millet", "non_existent_db")
        assert len(results) == 0


def test_fao_infoods_client_get_food_by_id():
    """Test FAO/INFOODS client get food by ID functionality."""
    # Create a temporary directory with test CSV files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test CSV file
        csv_file = os.path.join(temp_dir, "test_db.csv")
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                "Food ID", "Food name", "Food group", "Region", "Protein (g/100g)", 
                "Fat (g/100g)", "Carbohydrate (g/100g)", "Energy (kcal)"
            ])
            writer.writeheader()
            writer.writerow({
                "Food ID": "1001",
                "Food name": "Millet",
                "Food group": "Grains",
                "Region": "West Africa",
                "Protein (g/100g)": "11.0",
                "Fat (g/100g)": "4.3",
                "Carbohydrate (g/100g)": "73.0",
                "Energy (kcal)": "378",
            })
        
        # Test the client
        client = FAOInfoodsClient(data_dir=temp_dir)
        
        # Get food by ID
        food_item = client.get_food_by_id("1001", "test_db")
        assert food_item is not None
        assert food_item.food_id == "1001"
        assert food_item.food_name == "Millet"
        assert food_item.food_group == "Grains"
        
        # Try to get non-existent food
        food_item = client.get_food_by_id("9999", "test_db")
        assert food_item is None
        
        # Try to get food from non-existent database
        food_item = client.get_food_by_id("1001", "non_existent_db")
        assert food_item is None


def test_fao_infoods_client_parse_food_item():
    """Test FAO/INFOODS client food item parsing."""
    client = FAOInfoodsClient()
    
    # Test normal parsing
    food_data = {
        "Food ID": "1001",
        "Food name": "Millet",
        "Food group": "Grains",
        "Region": "West Africa",
        "Protein": "11.0",
        "Fat": "4.3",
        "Carbohydrate": "73.0",
        "Energy": "378",
        "Publication Year": "2019"
    }
    
    food_item = client._parse_food_item(food_data, "test_db")
    assert food_item is not None
    assert food_item.food_id == "1001"
    assert food_item.food_name == "Millet"
    assert food_item.food_group == "Grains"
    assert food_item.region == "West Africa"
    assert food_item.database_source == "test_db"
    assert food_item.publication_year == "2019"
    assert food_item.nutrients_per_100g["protein_g"] == 11.0
    assert food_item.nutrients_per_100g["fat_g"] == 4.3
    assert food_item.nutrients_per_100g["carbs_g"] == 73.0
    assert food_item.nutrients_per_100g["kcal"] == 378


def test_fao_infoods_client_parse_food_item_with_invalid_values():
    """Test FAO/INFOODS client food item parsing with invalid values."""
    client = FAOInfoodsClient()
    
    # Test parsing with invalid values
    food_data = {
        "Food ID": "1001",
        "Food name": "Test Food",
        "Food group": "Grains",
        "Region": "Test Region",
        "Protein": "invalid",  # This will cause ValueError when converting to float
        "Fat": "5.0",         # Valid value
    }
    
    # This should not raise an exception and should continue processing
    food_item = client._parse_food_item(food_data, "test_db")
    assert food_item is not None
    # The invalid nutrient should not be included
    assert "protein_g" not in food_item.nutrients_per_100g
    # The valid nutrient should be included
    assert food_item.nutrients_per_100g["fat_g"] == 5.0


def test_fao_infoods_client_parse_food_item_error_handling():
    """Test FAO/INFOODS client food item parsing error handling."""
    client = FAOInfoodsClient()
    
    # Test with exception during parsing
    with patch('core.food_apis.fao_infoods_client.logger.error') as mock_logger:
        with patch('core.food_apis.fao_infoods_client.FAOInfoodsFoodItem.__init__', side_effect=Exception("Init error")):
            food_data = {"Food ID": "1001"}
            food_item = client._parse_food_item(food_data, "test_db")
            assert food_item is None
            mock_logger.assert_called()


def test_fao_infoods_client_error_handling():
    """Test FAO/INFOODS client error handling."""
    # Test with directory that causes exception during loading
    with patch('core.food_apis.fao_infoods_client.logger.error') as mock_logger:
        with patch('core.food_apis.fao_infoods_client.Path.glob', side_effect=Exception("Glob error")):
            client = FAOInfoodsClient(data_dir="problematic_dir")
            # Should handle the error gracefully
            mock_logger.assert_called()


def test_fao_infoods_client_load_database_from_csv_error():
    """Test FAO/INFOODS client database loading from CSV error handling."""
    client = FAOInfoodsClient()
    
    # Test with file that causes exception during loading
    with patch('core.food_apis.fao_infoods_client.logger.error') as mock_logger:
        with patch('builtins.open', side_effect=Exception("File error")):
            data = client._load_database_from_csv(Path("problematic_file.csv"))
            # Should handle the error gracefully and return empty list
            assert data == []
            mock_logger.assert_called()


def test_fao_infoods_client_search_foods_error():
    """Test FAO/INFOODS client food search error handling."""
    client = FAOInfoodsClient()
    client.databases = {"test_db": [{"Food name": "Test"}]}
    
    # Test with exception during search
    with patch('core.food_apis.fao_infoods_client.logger.error') as mock_logger:
        with patch.object(client, '_parse_food_item', side_effect=Exception("Parse error")):
            results = client.search_foods("test")
            assert results == []  # Should return empty list on error
            mock_logger.assert_called()


def test_fao_infoods_client_get_food_by_id_error():
    """Test FAO/INFOODS client get food by ID error handling."""
    client = FAOInfoodsClient()
    client.databases = {"test_db": [{"Food ID": "1001"}]}
    
    # Test with exception during retrieval
    with patch('core.food_apis.fao_infoods_client.logger.error') as mock_logger:
        with patch.object(client, '_parse_food_item', side_effect=Exception("Parse error")):
            food_item = client.get_food_by_id("1001", "test_db")
            assert food_item is None  # Should return None on error
            mock_logger.assert_called()


def test_fao_infoods_client_get_available_databases():
    """Test FAO/INFOODS client get available databases functionality."""
    client = FAOInfoodsClient()
    client.databases = {"db1": [], "db2": []}
    
    # Get available databases
    databases = client.get_available_databases()
    assert len(databases) == 2
    assert "db1" in databases
    assert "db2" in databases


def test_fao_infoods_client_close():
    """Test FAO/INFOODS client close method."""
    client = FAOInfoodsClient()
    # Should not raise any exception
    client.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])