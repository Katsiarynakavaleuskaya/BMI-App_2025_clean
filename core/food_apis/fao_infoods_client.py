"""
FAO/INFOODS Food Composition Database Client

RU: Клиент для работы с базами данных FAO/INFOODS.
EN: Client for FAO/INFOODS food composition databases.

This module provides access to the FAO/INFOODS global food 
composition databases,
including regional databases like WAFCT and specialized 
databases like uPulses.

Data Access: FAO/INFOODS databases are typically distributed 
as Excel or CSV files.
For this implementation, we'll work with locally downloaded
CSV files.

Documentation: https://www.fao.org/infoods/infoods/tables-and-
databases/faoinfoods-databases/en/
Data License: Varies by database, generally open access for
research and educational purposes.
"""

from __future__ import annotations

import csv
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Flag to indicate if FAO/INFOODS client is available
FAO_INFOODS_AVAILABLE = True


@dataclass
class FAOInfoodsFoodItem:
    """
    RU: Элемент из базы данных FAO/INFOODS с полной питательной информацией.
    EN: FAO/INFOODS food item with complete nutritional information.
    """
    food_id: str
    food_name: str
    food_group: str
    nutrients_per_100g: Dict[str, float]  # Nutrient name -> amount per 100g
    region: str  # Region the food data is relevant for
    database_source: str  # Specific FAO/INFOODS database (e.g., "WAFCT",
    # "uPulses")
    publication_year: Optional[str]

    def to_menu_engine_format(self) -> Dict[str, Any]:
        """
        RU: Конвертирует в формат для menu_engine.
        EN: Converts to menu_engine format.
        """
        return {
            "name": self.food_name,
            "nutrients_per_100g": self.nutrients_per_100g,
            "cost_per_100g": 1.2,  # Default cost - can be overridden
            "tags": self._generate_tags(),
            "availability_regions": [self.region],
            "source": f"FAO/INFOODS {self.database_source}",
            "source_id": self.food_id
        }

    def _generate_tags(self) -> List[str]:
        """Generate diet tags based on food group and name."""
        tags = []
        name_lower = self.food_name.lower()
        group_lower = self.food_group.lower()

        # Vegetarian/Vegan detection based on food group
        animal_groups = ["meat", "poultry", "fish", "seafood"]
        if not any(keyword in group_lower for keyword in animal_groups):
            tags.append("VEG")

        # Check if likely vegan (no dairy either)
        dairy_groups = ["dairy", "milk"]
        if "VEG" in tags and not any(
            keyword in group_lower for keyword in dairy_groups
        ):
            tags.append("VEGAN")

        # Gluten-free approximation
        gluten_keywords = ["wheat", "bread", "pasta", "cereal", "flour"]
        if not any(keyword in name_lower for keyword in gluten_keywords):
            tags.append("GF")

        return tags


class FAOInfoodsClient:
    """
    RU: Клиент для работы с базами данных FAO/INFOODS.
    EN: Client for FAO/INFOODS databases.

    Provides methods to load and search food composition data from 
    FAO/INFOODS databases.
    Since these databases are typically distributed as static files, 
    we'll work with
    locally stored CSV files.
    """

    def __init__(self, data_dir: str = "external/fao_infoods"):
        """
        Initialize FAO/INFOODS client.

        Args:
            data_dir: Directory containing FAO/INFOODS CSV files
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Common nutrient mappings (FAO/INFOODS nutrient names to our
        # standard names)
        self.nutrient_mapping = {
            # Macronutrients
            "Protein": "protein_g",
            "Fat": "fat_g",
            "Carbohydrate": "carbs_g",
            "Fibre": "fiber_g",
            "Energy": "kcal",

            # Minerals (mg)
            "Calcium": "calcium_mg",
            "Iron": "iron_mg",
            "Magnesium": "magnesium_mg",
            "Zinc": "zinc_mg",
            "Potassium": "potassium_mg",

            # Trace elements (μg)
            "Selenium": "selenium_ug",
            "Iodine": "iodine_ug",

            # Vitamins
            "Vitamin A": "vitamin_a_ug",
            "Vitamin D": "vitamin_d_iu",
            "Vitamin C": "vitamin_c_mg",
            "Folate": "folate_ug",
            "Vitamin B12": "b12_ug",

            # B-vitamins
            "Thiamin": "thiamin_mg",
            "Riboflavin": "riboflavin_mg",
            "Niacin": "niacin_mg",
            "Vitamin B6": "b6_mg",
        }

        # Load available databases
        self.databases = {}
        self._load_databases()

    def _load_databases(self):
        """Load all available FAO/INFOODS databases from CSV files."""
        try:
            # Look for CSV files in the data directory
            csv_files = list(self.data_dir.glob("*.csv"))
            for csv_file in csv_files:
                db_name = csv_file.stem
                self.databases[db_name] = \
                    self._load_database_from_csv(csv_file)
            logger.info(f"Loaded {len(self.databases)} FAO/INFOODS databases")
        except Exception as e:
            logger.error(f"Error loading FAO/INFOODS databases: {e}")

    def _load_database_from_csv(self, csv_file: Path) -> List[Dict[str, Any]]:
        """Load a single database from a CSV file."""
        try:
            data = []
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    data.append(row)
            logger.info(f"Loaded {len(data)} food items from {csv_file.name}")
            return data
        except Exception as e:
            logger.error(f"Error loading database from {csv_file}: {e}")
            return []

    def search_foods(
        self,
        query: str,
        database_name: Optional[str] = None
    ) -> List[FAOInfoodsFoodItem]:
        """
        RU: Поиск продуктов по названию в базах данных FAO/INFOODS.
        EN: Search foods by name in FAO/INFOODS databases.

        Args:
            query: Search query (e.g., "millet")
            database_name: Specific database to search in, or None to 
                search all

        Returns:
            List of FAOInfoodsFoodItem objects
        """
        try:
            results = []
            query_lower = query.lower()

            # Determine which databases to search
            databases_to_search = [database_name] if database_name \
                else list(self.databases.keys())

            for db_name in databases_to_search:
                if db_name not in self.databases:
                    continue

                # Search in this database
                for food_data in self.databases[db_name]:
                    food_name = food_data.get(
                        "Food name",
                        food_data.get("Food Name", "")
                    ).lower()
                    food_group = food_data.get(
                        "Food group",
                        food_data.get("Food Group", "")
                    )

                    if query_lower in food_name or \
                            query_lower in food_group.lower():
                        food_item = self._parse_food_item(food_data, db_name)
                        if food_item:
                            results.append(food_item)

            logger.info(f"Found {len(results)} foods for query: {query}")
            return results

        except Exception as e:
            logger.error(f"Error searching FAO/INFOODS foods for \
                '{query}': {e}")
            return []

    def get_food_by_id(
        self,
        food_id: str,
        database_name: str
    ) -> Optional[FAOInfoodsFoodItem]:
        """
        RU: Получить детальную информацию о продукте по ID.
        EN: Get detailed food information by ID.

        Args:
            food_id: Food ID in the database
            database_name: Name of the database to search in

        Returns:
            FAOInfoodsFoodItem or None if not found
        """
        try:
            if database_name not in self.databases:
                return None

            return next(
                (
                    self._parse_food_item(food_data, database_name)
                    for food_data in self.databases[database_name]
                    if food_data.get("Food ID") == food_id
                ),
                None,
            )
        except Exception as e:
            logger.error(f"Error getting FAO/INFOODS food details \
                for ID {food_id}: {e}")
            return None

    def _parse_food_item(self, food_data: Dict[str, Any], database_name: str) -> Optional[FAOInfoodsFoodItem]:  # noqa: E501
        """Parse a food item from raw database data."""
        try:
            # Extract basic information
            food_id = food_data.get("Food ID", "")
            food_name = food_data.get(
                "Food name",
                food_data.get("Food Name", "")
            )
            food_group = food_data.get(
                "Food group",
                food_data.get("Food Group", "")
            )
            region = food_data.get("Region", "Global")
            publication_year = food_data.get("Publication Year")

            # Parse nutrients
            nutrients_per_100g = {}
            for raw_name, standard_name in self.nutrient_mapping.items():
                # Try different possible column names
                possible_names = [
                    raw_name,
                    f"{raw_name} (mg/100g)",
                    f"{raw_name} (μg/100g)",

                    f"{raw_name}_100g"
                ]

                for name in possible_names:
                    if name in food_data and food_data[name] != "":
                        try:
                            value = float(food_data[name])
                            nutrients_per_100g[standard_name] = value
                            break
                        except ValueError:
                            continue

            # Create food item
            return FAOInfoodsFoodItem(
                food_id=food_id,
                food_name=food_name,
                food_group=food_group,
                nutrients_per_100g=nutrients_per_100g,
                region=region,
                database_source=database_name,
                publication_year=publication_year
            )

        except Exception as e:
            logger.error(f"Error parsing FAO/INFOODS food item: {e}")
            return None

    def get_available_databases(self) -> List[str]:
        """
        RU: Получить список доступных баз данных.
        EN: Get list of available databases.
        """
        return list(self.databases.keys())

    def close(self):
        """Close the client (no-op for file-based client)."""
        pass


