"""
Food Database Parser

RU: Парсер базы данных продуктов из CSV.
EN: Parser for food database from CSV.

This module provides functionality to parse the food database CSV file
and provide nutrient lookup functionality.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from typing import Dict, List, Optional, Set

from .targets import MicroTargets


@dataclass
class FoodItem:
    """
    RU: Элемент базы данных продуктов.
    EN: Food database item.
    """
    name: str
    unit_per: int  # e.g., 100
    unit: str      # e.g., g
    protein_g: float
    fat_g: float
    carbs_g: float
    fiber_g: float
    Fe_mg: float
    Ca_mg: float
    VitD_IU: float
    B12_ug: float
    Folate_ug: float
    Iodine_ug: float
    K_mg: float
    Mg_mg: float
    price_per_unit: float
    flags: Set[str]

    def to_micro_targets(self) -> MicroTargets:
        """
        RU: Преобразует питательные вещества в формат MicroTargets.
        EN: Convert nutrients to MicroTargets format.
        """
        return MicroTargets(
            iron_mg=self.Fe_mg,
            calcium_mg=self.Ca_mg,
            magnesium_mg=self.Mg_mg,
            zinc_mg=0.0,  # Not in CSV, would need to be added
            potassium_mg=self.K_mg,
            iodine_ug=self.Iodine_ug,
            selenium_ug=0.0,  # Not in CSV, would need to be added
            folate_ug=self.Folate_ug,
            b12_ug=self.B12_ug,
            vitamin_d_iu=self.VitD_IU,
            vitamin_a_ug=0.0,  # Not in CSV, would need to be added
            vitamin_c_mg=0.0   # Not in CSV, would need to be added
        )

    def get_nutrient_amount(self, nutrient_name: str, amount_g: float) -> float:
        """
        RU: Получает количество нутриента для заданного количества продукта.
        EN: Get nutrient amount for given product quantity.
        """
        # All nutrients are per 100g in the database
        factor = amount_g / 100.0

        nutrient_mapping = {
            "protein_g": self.protein_g,
            "fat_g": self.fat_g,
            "carbs_g": self.carbs_g,
            "fiber_g": self.fiber_g,
            "iron_mg": self.Fe_mg,
            "calcium_mg": self.Ca_mg,
            "magnesium_mg": self.Mg_mg,
            "potassium_mg": self.K_mg,
            "iodine_ug": self.Iodine_ug,
            "folate_ug": self.Folate_ug,
            "b12_ug": self.B12_ug,
            "vitamin_d_iu": self.VitD_IU,
        }

        return nutrient_mapping.get(nutrient_name, 0.0) * factor


def parse_food_db(csv_path: str = "data/food_db.csv") -> Dict[str, FoodItem]:
    """
    RU: Парсит CSV файл базы данных продуктов.
    EN: Parse food database CSV file.

    Args:
        csv_path: Path to the food database CSV file

    Returns:
        Dictionary mapping food names to FoodItem objects
    """
    food_db = {}

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parse flags
            flags_str = row.get("flags", "")
            flags = set(flags_str.split(";")) if flags_str else set()

            # Create FoodItem
            food_item = FoodItem(
                name=row["name"],
                unit_per=int(row["unit_per"]) if "unit_per" in row else 100,
                unit=row["unit"] if "unit" in row else "g",
                protein_g=float(row["protein_g"]),
                fat_g=float(row["fat_g"]),
                carbs_g=float(row["carbs_g"]),
                fiber_g=float(row["fiber_g"]),
                Fe_mg=float(row["Fe_mg"]),
                Ca_mg=float(row["Ca_mg"]),
                VitD_IU=float(row["VitD_IU"]),
                B12_ug=float(row["B12_ug"]),
                Folate_ug=float(row["Folate_ug"]),
                Iodine_ug=float(row["Iodine_ug"]),
                K_mg=float(row["K_mg"]),
                Mg_mg=float(row["Mg_mg"]),
                price_per_unit=float(row.get("price_per_unit", 0) or 0),
                flags=flags
            )

            # Use name as key (assuming unique names)
            food_db[row["name"]] = food_item

    return food_db


# RU: Стабильное mapping доноров микро. EN: Stable mapping of micro donors.
# RU: Стабильное mapping доноров микро. EN: Stable mapping of micro donors.
DONORS = {
    "Fe_mg":      ["lentils","spinach_raw","tofu","chicken_breast"],
    "Ca_mg":      ["greek_yogurt","tofu","spinach_raw"],
    "VitD_IU":    ["salmon","egg"],
    "B12_ug":     ["salmon","chicken_breast","greek_yogurt"],
    "Folate_ug":  ["spinach_raw","lentils"],
    "Iodine_ug":  ["salmon"],
    "K_mg":       ["banana","spinach_raw","potato"],
    "Mg_mg":      ["oats","spinach_raw","lentils"],
}


def pick_booster_for(micro: str, flags: Set[str], food_db: Dict[str, FoodItem]) -> Optional[str]:
    """
    RU: Выбирает продукт-бустер для конкретного микронутриента.
    EN: Picks a booster food for a specific micronutrient.

    Args:
        micro: Micronutrient name (e.g., "iron_mg", "folate_ug")
        flags: Dietary flags to consider
        food_db: Food database

    Returns:
        Name of the best booster food or None if not found
    """
    # Normalize incoming nutrient key to our donor table keys
    alias_map = {
        "iron_mg": "Fe_mg",
        "calcium_mg": "Ca_mg",
        "vitamin_d_iu": "VitD_IU",
        "b12_ug": "B12_ug",
        "folate_ug": "Folate_ug",
        "iodine_ug": "Iodine_ug",
        "potassium_mg": "K_mg",
        "magnesium_mg": "Mg_mg",
    }
    key = micro
    if key not in DONORS:
        key = alias_map.get(str(micro).lower(), micro)

    # Use the stable donor mapping
    candidates = DONORS.get(key, [])

    # Filter by dietary flags
    filtered_candidates = []
    for candidate in candidates:
        if candidate in food_db:
            food = food_db[candidate]
            # Check if food matches dietary flags
            if not flags or _compatible(food.flags, flags):
                filtered_candidates.append(candidate)

    # Return the first matching candidate
    return filtered_candidates[0] if filtered_candidates else None


def _compatible(food_flags: Set[str], diet_flags: Set[str]) -> bool:
    """
    RU: Проверяет совместимость флагов еды с диетическими флагами.
    EN: Checks compatibility of food flags with dietary flags.
    """
    # VEG запрещает OMNI
    if "VEG" in diet_flags and "OMNI" in food_flags:
        return False
    # PESC запрещает OMNI
    if "PESC" in diet_flags and "OMNI" in food_flags:
        return False
    # GF требует GF-совместимое
    if "GF" in diet_flags and "GF" not in food_flags:
        return False
    return True


def aggregate_shopping(days: List[Dict]) -> Dict[str, float]:
    """
    RU: Агрегирует список покупок за несколько дней.
    EN: Aggregates shopping list across multiple days.

    Args:
        days: List of daily meal plans with ingredients

    Returns:
        Dictionary mapping ingredient names to total amounts needed
    """
    shopping_list = {}

    for day in days:
        if "meals" in day:
            for meal in day["meals"]:
                if "ingredients" in meal:
                    for ingredient_name, amount in meal["ingredients"].items():
                        shopping_list[ingredient_name] = shopping_list.get(ingredient_name, 0) + amount

    return shopping_list
