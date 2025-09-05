"""
CIQUAL French Food Composition Database Client

RU: Клиент для работы с французской базой данных CIQUAL.
EN: Client for CIQUAL French food composition database.

This module provides access to the CIQUAL food composition database managed by ANSES,
which contains nutritional data for foods commonly consumed in France.

Data Access: CIQUAL database is distributed as Excel or XML files.
For this implementation, we'll work with locally downloaded CSV files.

Documentation: https://ciqual.anses.fr/
Data License: Open access for research and educational purposes.
"""

from __future__ import annotations

import csv
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Flag to indicate if CIQUAL client is available
CIQUAL_AVAILABLE = True


@dataclass
class CIQUALFoodItem:
    """
    RU: Элемент из базы данных CIQUAL с полной питательной информацией.
    EN: CIQUAL food item with complete nutritional information.
    """
    food_code: str
    food_name_fr: str
    food_name_en: str
    food_group: str
    nutrients_per_100g: Dict[str, float]  # Nutrient name -> amount per 100g
    region: str = "FR"  # Region the food data is relevant for (France)
    database_source: str = "CIQUAL"  # Database source
    publication_year: str = "2020"  # CIQUAL version

    def to_menu_engine_format(self) -> Dict[str, Any]:
        """
        RU: Конвертирует в формат для menu_engine.
        EN: Converts to menu_engine format.
        """
        return {
            "name": self.food_name_fr or self.food_name_en,
            "nutrients_per_100g": self.nutrients_per_100g,
            "cost_per_100g": 1.3,  # Default cost - can be overridden
            "tags": self._generate_tags(),
            "availability_regions": [self.region],
            "source": f"CIQUAL {self.database_source}",
            "source_id": self.food_code
        }

    def _generate_tags(self) -> List[str]:
        """Generate diet tags based on food group and name."""
        tags = []
        name_lower = (self.food_name_fr or self.food_name_en).lower()
        group_lower = self.food_group.lower()

        # Vegetarian/Vegan detection based on food group
        animal_groups = ["viande", "poisson", "produits laitiers"]
        if not any(keyword in group_lower for keyword in animal_groups):
            tags.append("VEG")

        # Check if likely vegan (no dairy either)
        dairy_groups = ["produits laitiers", "lait", "fromage"]
        if "VEG" in tags and not any(keyword in group_lower for keyword in dairy_groups):
            tags.append("VEGAN")

        # Gluten-free approximation
        gluten_keywords = ["blé", "pain", "pâtes", "céréales"]
        if not any(keyword in name_lower for keyword in gluten_keywords):
            tags.append("GF")

        return tags


class CIQUALClient:
    """
    RU: Клиент для работы с базой данных CIQUAL.
    EN: Client for CIQUAL database.

    Provides methods to load and search food composition data from the CIQUAL database.
    Since this database is distributed as static files, we'll work with locally stored CSV files.
    """

    def __init__(self, data_file: str = "external/ciqual/ciqual_2020.csv"):
        """
        Initialize CIQUAL client.

        Args:
            data_file: Path to the CIQUAL CSV file
        """
        self.data_file = Path(data_file)
        self.food_items = []

        # Common nutrient mappings (CIQUAL nutrient names to our standard names)
        self.nutrient_mapping = {
            # Macronutrients
            "Protéines": "protein_g",
            "Lipides": "fat_g",
            "Glucides": "carbs_g",
            "Fibres": "fiber_g",
            "Energie, Règlement UE N° 1169/2011 (kcal)": "kcal",

            # Minerals (mg)
            "Calcium": "calcium_mg",
            "Fer": "iron_mg",
            "Magnésium": "magnesium_mg",
            "Zinc": "zinc_mg",
            "Potassium": "potassium_mg",

            # Trace elements (μg)
            "Sélénium": "selenium_ug",
            "Iode": "iodine_ug",

            # Vitamins
            "Vitamine A": "vitamin_a_ug",
            "Vitamine D": "vitamin_d_iu",
            "Vitamine C": "vitamin_c_mg",
            "Folates": "folate_ug",
            "Vitamine B12": "b12_ug",

            # B-vitamins
            "Vitamine B1 (Thiamine)": "thiamin_mg",
            "Vitamine B2 (Riboflavine)": "riboflavin_mg",
            "Vitamine B3 (Niacine)": "niacin_mg",
            "Vitamine B6": "b6_mg",

            # Individual sugars (CIQUAL 2020 specific)
            "Fructose": "fructose_g",
            "Glucose": "glucose_g",
            "Lactose": "lactose_g",
            "Maltose": "maltose_g",
            "Saccharose": "sucrose_g",
        }

        # Load the database
        self._load_database()

    def _load_database(self):
        """Load the CIQUAL database from CSV file."""
        try:
            if not self.data_file.exists():
                logger.warning(f"CIQUAL data file not found: {self.data_file}")
                return

            with open(self.data_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter=';')  # CIQUAL uses semicolon delimiter
                for row in reader:
                    self.food_items.append(row)
            logger.info(f"Loaded {len(self.food_items)} food items from CIQUAL database")
        except Exception as e:
            logger.error(f"Error loading CIQUAL database: {e}")

    def search_foods(self, query: str) -> List[CIQUALFoodItem]:
        """
        RU: Поиск продуктов по названию в базе данных CIQUAL.
        EN: Search foods by name in CIQUAL database.

        Args:
            query: Search query (e.g., "pomme")

        Returns:
            List of CIQUALFoodItem objects
        """
        try:
            results = []
            query_lower = query.lower()

            for food_data in self.food_items:
                food_name_fr = food_data.get("alim_nom_fr", "")
                food_name_en = food_data.get("alim_nom_eng", "")
                food_group = food_data.get("alim_grp_nom_fr", "")

                if (query_lower in food_name_fr.lower() or
                    query_lower in food_name_en.lower() or
                    query_lower in food_group.lower()):
                    food_item = self._parse_food_item(food_data)
                    if food_item:
                        results.append(food_item)

            logger.info(f"Found {len(results)} foods for query: {query}")
            return results

        except Exception as e:
            logger.error(f"Error searching CIQUAL foods for '{query}': {e}")
            return []

    def get_food_by_code(self, food_code: str) -> Optional[CIQUALFoodItem]:
        """
        RU: Получить детальную информацию о продукте по коду.
        EN: Get detailed food information by code.

        Args:
            food_code: Food code in the CIQUAL database

        Returns:
            CIQUALFoodItem or None if not found
        """
        try:
            for food_data in self.food_items:
                if food_data.get("alim_code") == food_code:
                    return self._parse_food_item(food_data)

            return None

        except Exception as e:
            logger.error(f"Error getting CIQUAL food details for code {food_code}: {e}")
            return None

    def _parse_food_item(self, food_data: Dict[str, Any]) -> Optional[CIQUALFoodItem]:
        """Parse a food item from raw database data."""
        try:
            # Extract basic information
            food_code = food_data.get("alim_code", "")
            food_name_fr = food_data.get("alim_nom_fr", "")
            food_name_en = food_data.get("alim_nom_eng", "")
            food_group = food_data.get("alim_grp_nom_fr", "")

            # Parse nutrients
            nutrients_per_100g = {}
            for raw_name, standard_name in self.nutrient_mapping.items():
                # Try different possible column names (CIQUAL has specific naming)
                possible_names = [
                    raw_name,
                    f"{raw_name} (mg/100g)",
                    f"{raw_name} (µg/100g)",
                    f"{raw_name} (g/100g)",
                    f"{raw_name} (kJ/100g)",
                    f"{raw_name} (kcal/100g)",
                    raw_name
                ]

                for name in possible_names:
                    if name in food_data and food_data[name] not in ["", "ND", "NQ"]:
                        try:
                            # Handle different value formats in CIQUAL
                            value_str = food_data[name].replace(',', '.')  # Convert comma to dot
                            value = float(value_str)
                            nutrients_per_100g[standard_name] = value
                            break
                        except ValueError:
                            continue

            # Create food item
            return CIQUALFoodItem(
                food_code=food_code,
                food_name_fr=food_name_fr,
                food_name_en=food_name_en,
                food_group=food_group,
                nutrients_per_100g=nutrients_per_100g
            )

        except Exception as e:
            logger.error(f"Error parsing CIQUAL food item: {e}")
            return None

    def get_all_food_groups(self) -> List[str]:
        """
        RU: Получить все группы продуктов в базе данных.
        EN: Get all food groups in the database.
        """
        try:
            groups = set()
            for food_data in self.food_items:
                group = food_data.get("alim_grp_nom_fr", "")
                if group:
                    groups.add(group)
            return sorted(list(groups))
        except Exception as e:
            logger.error(f"Error getting CIQUAL food groups: {e}")
            return []

    def close(self):
        """Close the client (no-op for file-based client)."""
        pass
