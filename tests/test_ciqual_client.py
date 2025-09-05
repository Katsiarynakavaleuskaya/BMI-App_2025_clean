"""
Tests for CIQUAL Client

RU: Тесты для клиента CIQUAL.
EN: Tests for CIQUAL client.
"""

import csv
import os
import tempfile
from unittest.mock import patch

import pytest

from core.food_apis.ciqual_client import CIQUALClient, CIQUALFoodItem


def test_ciqual_client_initialization():
    """Test CIQUAL client initialization with non-existent file."""
    # Test with non-existent file
    client = CIQUALClient(data_file="non_existent_file.csv")
    assert client.data_file.name == "non_existent_file.csv"
    assert len(client.food_items) == 0


def test_ciqual_client_load_database():
    """Test CIQUAL client database loading."""
    # Create a temporary CSV file with test data (semicolon separated)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            "alim_code", "alim_nom_fr", "alim_nom_eng", "alim_grp_nom_fr",
            "Protéines", "Lipides", "Glucides", "Fibres", "Energie, Règlement UE N° 1169/2011 (kcal)",
            "Calcium", "Fer", "Magnésium", "Zinc", "Potassium", "Sélénium", "Iode",
            "Vitamine A", "Vitamine D", "Vitamine C", "Folates", "Vitamine B12"
        ], delimiter=';')
        writer.writeheader()
        writer.writerow({
            "alim_code": "1001",
            "alim_nom_fr": "Pomme, crue",
            "alim_nom_eng": "Apple, raw",
            "alim_grp_nom_fr": "Fruits",
            "Protéines": "0.5",
            "Lipides": "0.3",
            "Glucides": "13.8",
            "Fibres": "2.4",
            "Energie, Règlement UE N° 1169/2011 (kcal)": "52",
            "Calcium": "6",
            "Fer": "0.12",
            "Magnésium": "5",
            "Zinc": "0.04",
            "Potassium": "107",
            "Sélénium": "0.5",
            "Iode": "1",
            "Vitamine A": "5",
            "Vitamine D": "0",
            "Vitamine C": "4.6",
            "Folates": "3",
            "Vitamine B12": "0",
        })
        temp_path = f.name

    try:
        # Test the client
        client = CIQUALClient(data_file=temp_path)
        assert len(client.food_items) == 1
        
        # Check that the food item was loaded correctly
        food_data = client.food_items[0]
        assert food_data["alim_nom_fr"] == "Pomme, crue"
        assert food_data["alim_nom_eng"] == "Apple, raw"
        assert food_data["Protéines"] == "0.5"
        assert food_data["Energie, Règlement UE N° 1169/2011 (kcal)"] == "52"
    finally:
        # Clean up
        os.unlink(temp_path)


def test_ciqual_food_item_to_menu_engine_format():
    """Test CIQUAL food item conversion to menu engine format."""
    # Create a CIQUAL food item
    nutrients = {
        "protein_g": 0.5,
        "fat_g": 0.3,
        "carbs_g": 13.8,
        "fiber_g": 2.4,
        "kcal": 52,
        "calcium_mg": 6,
        "iron_mg": 0.12,
    }
    
    food_item = CIQUALFoodItem(
        food_code="1001",
        food_name_fr="Pomme, crue",
        food_name_en="Apple, raw",
        food_group="Fruits",
        nutrients_per_100g=nutrients
    )
    
    # Convert to menu engine format
    menu_format = food_item.to_menu_engine_format()
    
    # Check that all expected fields are present
    assert menu_format["name"] == "Pomme, crue"
    assert menu_format["nutrients_per_100g"] == nutrients
    assert menu_format["cost_per_100g"] == 1.3
    assert "VEG" in menu_format["tags"]  # Should be vegetarian
    assert "VEGAN" in menu_format["tags"]  # Should be vegan
    assert "GF" in menu_format["tags"]  # Should be gluten-free
    assert menu_format["availability_regions"] == ["FR"]
    assert menu_format["source"] == "CIQUAL CIQUAL"
    assert menu_format["source_id"] == "1001"


def test_ciqual_client_search_foods():
    """Test CIQUAL client food search functionality."""
    # Create a temporary CSV file with test data
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            "alim_code", "alim_nom_fr", "alim_nom_eng", "alim_grp_nom_fr",
            "Protéines", "Lipides", "Glucides", "Fibres", "Energie, Règlement UE N° 1169/2011 (kcal)"
        ], delimiter=';')
        writer.writeheader()
        writer.writerow({
            "alim_code": "1001",
            "alim_nom_fr": "Pomme, crue",
            "alim_nom_eng": "Apple, raw",
            "alim_grp_nom_fr": "Fruits",
            "Protéines": "0.5",
            "Lipides": "0.3",
            "Glucides": "13.8",
            "Fibres": "2.4",
            "Energie, Règlement UE N° 1169/2011 (kcal)": "52",
        })
        writer.writerow({
            "alim_code": "2001",
            "alim_nom_fr": "Banane, crue",
            "alim_nom_eng": "Banana, raw",
            "alim_grp_nom_fr": "Fruits",
            "Protéines": "1.1",
            "Lipides": "0.3",
            "Glucides": "23.0",
            "Fibres": "2.6",
            "Energie, Règlement UE N° 1169/2011 (kcal)": "89",
        })
        temp_path = f.name

    try:
        # Test the client
        client = CIQUALClient(data_file=temp_path)
        
        # Search for "pomme"
        results = client.search_foods("pomme")
        assert len(results) == 1
        assert results[0].food_name_fr == "Pomme, crue"
        assert results[0].food_name_en == "Apple, raw"
        
        # Search for "banane"
        results = client.search_foods("banane")
        assert len(results) == 1
        assert results[0].food_name_fr == "Banane, crue"
        
        # Search for "fruit" (should match both)
        results = client.search_foods("fruit")
        assert len(results) == 2
        
        # Search for non-existent item
        results = client.search_foods("steak")
        assert len(results) == 0
    finally:
        # Clean up
        os.unlink(temp_path)


def test_ciqual_client_get_food_by_code():
    """Test CIQUAL client get food by code functionality."""
    # Create a temporary CSV file with test data
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            "alim_code", "alim_nom_fr", "alim_nom_eng", "alim_grp_nom_fr",
            "Protéines", "Lipides", "Glucides", "Fibres", "Energie, Règlement UE N° 1169/2011 (kcal)"
        ], delimiter=';')
        writer.writeheader()
        writer.writerow({
            "alim_code": "1001",
            "alim_nom_fr": "Pomme, crue",
            "alim_nom_eng": "Apple, raw",
            "alim_grp_nom_fr": "Fruits",
            "Protéines": "0.5",
            "Lipides": "0.3",
            "Glucides": "13.8",
            "Fibres": "2.4",
            "Energie, Règlement UE N° 1169/2011 (kcal)": "52",
        })
        temp_path = f.name

    try:
        # Test the client
        client = CIQUALClient(data_file=temp_path)
        
        # Get food by code
        food_item = client.get_food_by_code("1001")
        assert food_item is not None
        assert food_item.food_code == "1001"
        assert food_item.food_name_fr == "Pomme, crue"
        assert food_item.food_name_en == "Apple, raw"
        
        # Try to get non-existent food
        food_item = client.get_food_by_code("9999")
        assert food_item is None
    finally:
        # Clean up
        os.unlink(temp_path)


def test_ciqual_client_parse_food_item():
    """Test CIQUAL client food item parsing."""
    client = CIQUALClient()
    
    # Test normal parsing
    food_data = {
        "alim_code": "1001",
        "alim_nom_fr": "Pomme, crue",
        "alim_nom_eng": "Apple, raw",
        "alim_grp_nom_fr": "Fruits",
        "Protéines": "0.5",
        "Lipides": "0.3",
        "Glucides": "13.8",
        "Fibres": "2.4",
        "Energie, Règlement UE N° 1169/2011 (kcal)": "52",
        "Calcium": "6",
        "Fer": "0.12",
    }
    
    food_item = client._parse_food_item(food_data)
    assert food_item is not None
    assert food_item.food_code == "1001"
    assert food_item.food_name_fr == "Pomme, crue"
    assert food_item.food_name_en == "Apple, raw"
    assert food_item.food_group == "Fruits"
    assert food_item.nutrients_per_100g["protein_g"] == 0.5
    assert food_item.nutrients_per_100g["fat_g"] == 0.3
    assert food_item.nutrients_per_100g["carbs_g"] == 13.8
    assert food_item.nutrients_per_100g["fiber_g"] == 2.4
    assert food_item.nutrients_per_100g["kcal"] == 52
    assert food_item.nutrients_per_100g["calcium_mg"] == 6
    assert food_item.nutrients_per_100g["iron_mg"] == 0.12


def test_ciqual_client_parse_food_item_with_comma_values():
    """Test CIQUAL client food item parsing with comma-separated values."""
    client = CIQUALClient()
    
    # Test parsing with comma values (CIQUAL format)
    food_data = {
        "alim_code": "1001",
        "alim_nom_fr": "Pomme, crue",
        "alim_nom_eng": "Apple, raw",
        "alim_grp_nom_fr": "Fruits",
        "Protéines": "0,5",  # Comma instead of dot
        "Lipides": "0,3",
    }
    
    food_item = client._parse_food_item(food_data)
    assert food_item is not None
    assert food_item.nutrients_per_100g["protein_g"] == 0.5
    assert food_item.nutrients_per_100g["fat_g"] == 0.3


def test_ciqual_client_parse_food_item_with_invalid_values():
    """Test CIQUAL client food item parsing with invalid values."""
    client = CIQUALClient()
    
    # Test parsing with invalid values
    food_data = {
        "alim_code": "1001",
        "alim_nom_fr": "Pomme, crue",
        "alim_nom_eng": "Apple, raw",
        "alim_grp_nom_fr": "Fruits",
        "Protéines": "ND",  # Not determined
        "Lipides": "NQ",   # Not quantified
        "Glucides": "",    # Empty
        "Fibres": "2.4",   # Valid value
    }
    
    food_item = client._parse_food_item(food_data)
    assert food_item is not None
    assert "protein_g" not in food_item.nutrients_per_100g  # Should not be included
    assert "fat_g" not in food_item.nutrients_per_100g      # Should not be included
    assert "carbs_g" not in food_item.nutrients_per_100g    # Should not be included
    assert food_item.nutrients_per_100g["fiber_g"] == 2.4   # Should be included


def test_ciqual_client_parse_food_item_value_error():
    """Test CIQUAL client food item parsing with ValueError in nutrient parsing."""
    client = CIQUALClient()
    
    # Test parsing with invalid numeric values that cause ValueError
    food_data = {
        "alim_code": "1001",
        "alim_nom_fr": "Pomme, crue",
        "alim_nom_eng": "Apple, raw",
        "alim_grp_nom_fr": "Fruits",
        "Protéines": "invalid",  # This will cause ValueError when converting to float
    }
    
    # This should not raise an exception and should continue processing
    food_item = client._parse_food_item(food_data)
    assert food_item is not None
    # The invalid nutrient should not be included
    assert "protein_g" not in food_item.nutrients_per_100g


def test_ciqual_client_parse_food_item_error_handling():
    """Test CIQUAL client food item parsing error handling."""
    client = CIQUALClient()
    
    # Test with exception during parsing
    with patch('core.food_apis.ciqual_client.CIQUALFoodItem.__init__', side_effect=Exception("Init error")):
        food_data = {"alim_code": "1001"}
        food_item = client._parse_food_item(food_data)
        assert food_item is None


def test_ciqual_client_error_handling():
    """Test CIQUAL client error handling."""
    # Test with file that causes exception during loading
    with patch('core.food_apis.ciqual_client.open', side_effect=Exception("File error")):
        client = CIQUALClient(data_file="problematic_file.csv")
        # Should handle the error gracefully
        assert len(client.food_items) == 0
    
    # Test search with exception
    with patch('core.food_apis.ciqual_client.CIQUALClient._parse_food_item', side_effect=Exception("Parse error")):
        client = CIQUALClient()
        # Should handle the error gracefully and return empty list
        results = client.search_foods("test")
        assert results == []


def test_ciqual_client_get_all_food_groups():
    """Test CIQUAL client get all food groups functionality."""
    # Create a temporary CSV file with test data
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            "alim_code", "alim_nom_fr", "alim_grp_nom_fr"
        ], delimiter=';')
        writer.writeheader()
        writer.writerow({
            "alim_code": "1001",
            "alim_nom_fr": "Pomme, crue",
            "alim_grp_nom_fr": "Fruits",
        })
        writer.writerow({
            "alim_code": "2001",
            "alim_nom_fr": "Carotte, crue",
            "alim_grp_nom_fr": "Légumes",
        })
        writer.writerow({
            "alim_code": "3001",
            "alim_nom_fr": "Pomme, crue",  # Duplicate group
            "alim_grp_nom_fr": "Fruits",
        })
        temp_path = f.name

    try:
        # Test the client
        client = CIQUALClient(data_file=temp_path)
        
        # Get all food groups
        groups = client.get_all_food_groups()
        assert len(groups) == 2
        assert "Fruits" in groups
        assert "Légumes" in groups
        assert groups == ["Fruits", "Légumes"]  # Should be sorted
    finally:
        # Clean up
        os.unlink(temp_path)


def test_ciqual_client_load_database_error():
    """Test CIQUAL client database loading error handling."""
    # Test with file that causes exception during loading
    with patch('core.food_apis.ciqual_client.open', side_effect=Exception("File error")):
        client = CIQUALClient(data_file="problematic_file.csv")
        # Should handle the error gracefully
        assert len(client.food_items) == 0


def test_ciqual_client_search_foods_error():
    """Test CIQUAL client food search error handling."""
    client = CIQUALClient()
    client.food_items = [{"alim_nom_fr": "Test"}]
    
    # Test with exception during search
    with patch('core.food_apis.ciqual_client.CIQUALClient._parse_food_item', side_effect=Exception("Parse error")):
        results = client.search_foods("test")
        assert results == []  # Should return empty list on error


def test_ciqual_client_get_food_by_code_error():
    """Test CIQUAL client get food by code error handling."""
    client = CIQUALClient()
    client.food_items = [{"alim_code": "1001"}]
    
    # Test with exception during retrieval
    with patch('core.food_apis.ciqual_client.CIQUALClient._parse_food_item', side_effect=Exception("Parse error")):
        food_item = client.get_food_by_code("1001")
        assert food_item is None  # Should return None on error


def test_ciqual_client_parse_food_item_alternate_names():
    """Test CIQUAL client food item parsing with alternate nutrient names."""
    client = CIQUALClient()
    
    # Test parsing with alternate nutrient names
    food_data = {
        "alim_code": "1001",
        "alim_nom_fr": "Pomme, crue",
        "alim_nom_eng": "Apple, raw",
        "alim_grp_nom_fr": "Fruits",
        "Protéines (g/100g)": "0.5",  # Alternate name format
        "Lipides (mg/100g)": "300",   # Different unit format
    }
    
    food_item = client._parse_food_item(food_data)
    assert food_item is not None
    assert food_item.nutrients_per_100g["protein_g"] == 0.5
    assert food_item.nutrients_per_100g["fat_g"] == 300


def test_ciqual_client_close():
    """Test CIQUAL client close method."""
    client = CIQUALClient()
    # Should not raise any exception
    client.close()  # This covers line 284


def test_ciqual_client_load_database_file_not_found():
    """Test CIQUAL client database loading when file doesn't exist."""
    with patch('core.food_apis.ciqual_client.logger.warning') as mock_logger:
        client = CIQUALClient(data_file="non_existent_file.csv")
        # Should log a warning
        mock_logger.assert_called()
        # This covers lines 160-161


def test_ciqual_client_load_database_file_error():
    """Test CIQUAL client database loading with file error."""
    # Create a temporary file and then make it unreadable
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
        f.write("test")
        temp_path = f.name

    try:
        # Make the file unreadable
        os.chmod(temp_path, 0o000)
        
        with patch('core.food_apis.ciqual_client.logger.error') as mock_logger:
            client = CIQUALClient(data_file=temp_path)
            # Should log an error
            mock_logger.assert_called()
    finally:
        # Restore permissions and clean up
        os.chmod(temp_path, 0o644)
        os.unlink(temp_path)


def test_ciqual_client_search_foods_exception():
    """Test CIQUAL client search foods with general exception."""
    client = CIQUALClient()
    client.food_items = [{"alim_nom_fr": "Test"}]
    
    # Test with general exception during search
    with patch('core.food_apis.ciqual_client.logger.error') as mock_logger:
        with patch.object(client, '_parse_food_item', side_effect=Exception("General error")):
            results = client.search_foods("test")
            # Should return empty list on error
            assert results == []
            # Should log the error
            mock_logger.assert_called()


def test_ciqual_client_get_food_by_code_exception():
    """Test CIQUAL client get food by code with general exception."""
    client = CIQUALClient()
    client.food_items = [{"alim_code": "1001"}]
    
    # Test with general exception during retrieval
    with patch('core.food_apis.ciqual_client.logger.error') as mock_logger:
        with patch.object(client, '_parse_food_item', side_effect=Exception("General error")):
            food_item = client.get_food_by_code("1001")
            # Should return None on error
            assert food_item is None
            # Should log the error
            mock_logger.assert_called()


def test_ciqual_client_parse_food_item_general_exception():
    """Test CIQUAL client food item parsing with general exception."""
    client = CIQUALClient()
    
    # Test with general exception during parsing
    with patch('core.food_apis.ciqual_client.logger.error') as mock_logger:
        with patch('core.food_apis.ciqual_client.CIQUALFoodItem.__init__', side_effect=Exception("General error")):
            food_data = {"alim_code": "1001"}
            food_item = client._parse_food_item(food_data)
            assert food_item is None
            mock_logger.assert_called()


def test_ciqual_client_get_all_food_groups_exception():
    """Test CIQUAL client get all food groups with general exception."""
    client = CIQUALClient()
    client.food_items = [{"alim_grp_nom_fr": "Test"}]
    
    # Test with general exception during retrieval
    with patch('core.food_apis.ciqual_client.logger.error') as mock_logger:
        with patch('core.food_apis.ciqual_client.sorted', side_effect=Exception("General error")):
            groups = client.get_all_food_groups()
            # Should return empty list on error
            assert groups == []
            # Should log the error
            mock_logger.assert_called()


def test_ciqual_client_search_foods_general_exception():
    """Test CIQUAL client search foods with general exception."""
    client = CIQUALClient()
    client.food_items = [{"alim_nom_fr": "Test"}]
    
    # Test with general exception during search
    with patch('core.food_apis.ciqual_client.logger.error') as mock_logger:
        with patch.object(client, '_parse_food_item', side_effect=Exception("General error")):
            results = client.search_foods("test")
            # Should return empty list on error
            assert results == []
            # Should log the error
            mock_logger.assert_called()


def test_ciqual_client_get_all_food_groups_exception():
    """Test CIQUAL client get all food groups with general exception."""
    client = CIQUALClient()
    client.food_items = [{"alim_grp_nom_fr": "Test"}]
    
    # Test with general exception during retrieval
    with patch('core.food_apis.ciqual_client.logger.error') as mock_logger:
        with patch('core.food_apis.ciqual_client.sorted', side_effect=Exception("General error")):
            groups = client.get_all_food_groups()
            # Should return empty list on error
            assert groups == []
            # Should log the error
            mock_logger.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])