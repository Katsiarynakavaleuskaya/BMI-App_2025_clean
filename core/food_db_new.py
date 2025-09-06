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
from typing import Dict, List, Optional

from .meal_i18n import Language, translate_food

MICRO_KEYS = ["Fe_mg","Ca_mg","VitD_IU","B12_ug","Folate_ug","Iodine_ug","K_mg","Mg_mg"]

@dataclass
class FoodItem:
    name: str
    group: str
    per_g: float
    protein_g: float
    fat_g: float
    carbs_g: float
    fiber_g: float
    micros: Dict[str, float]
    flags: List[str]
    price: float

class FoodDB:
    """RU: Хранилище продуктов (100 г). EN: Simple 100g-based food database."""
    def __init__(self, path: str = "data/food_db_new.csv") -> None:
        self.items: Dict[str, FoodItem] = {}
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                micros = {k: float(row.get(k, 0) or 0) for k in MICRO_KEYS}
                flags = [x.strip() for x in (row.get("flags","") or "").split(";") if x.strip()]
                self.items[row["name"]] = FoodItem(
                    name=row["name"],
                    group=row["group"],
                    per_g=float(row["per_g"]),
                    protein_g=float(row["protein_g"]),
                    fat_g=float(row["fat_g"]),
                    carbs_g=float(row["carbs_g"]),
                    fiber_g=float(row["fiber_g"]),
                    micros=micros,
                    flags=flags,
                    price=float(row.get("price", 0) or 0),
                )

    def get_food(self, name: str) -> FoodItem:
        return self.items[name]

    def get_translated_food_name(self, name: str, lang: Language) -> str:
        """Get translated food name for the specified language."""
        return translate_food(lang, name)

    def pick_booster_for(self, micro: str, diet_flags: List[str]) -> Optional[str]:
        """RU: Выбрать продукт-донор для микро с учетом флагов диеты.
           EN: Pick a donor food for given micro respecting diet flags.
        """
        # Updated donor table to match DoD requirements
        donors = {
            "Fe_mg": ["lentils", "spinach_raw", "tofu", "chicken_breast"],
            "Ca_mg": ["greek_yogurt", "tofu", "spinach_raw"],
            "VitD_IU": ["salmon", "egg"],
            "B12_ug": ["salmon", "chicken_breast", "greek_yogurt"],
            "Folate_ug": ["spinach_raw", "lentils"],
            "Iodine_ug": ["salmon"],
            "K_mg": ["banana", "spinach_raw", "potato"],
            "Mg_mg": ["oats", "spinach_raw", "lentils"],
        }
        # Ensure calcium booster favors yogurt if compatible
        if micro == "Ca_mg" and "greek_yogurt" in self.items:
            item = self.items.get("greek_yogurt")
            if item and self._compatible(item.flags, diet_flags):
                return "greek_yogurt"
        cand_list = donors.get(micro, [])
        # Prefer spinach for iron when VEG is set
        if micro == "Fe_mg" and "VEG" in (diet_flags or []):
            # ensure spinach_raw prioritized if present
            if "spinach_raw" in cand_list:
                cand_list = ["spinach_raw"] + [c for c in cand_list if c != "spinach_raw"]
        for candidate in cand_list:
            # Allow fallback from spinach_raw -> spinach if DB uses different naming
            cand_key = candidate
            if candidate == "spinach_raw" and "spinach_raw" not in self.items and "spinach" in self.items:
                cand_key = "spinach"
            item = self.items.get(cand_key)
            if not item:
                continue
            if self._compatible(item.flags, diet_flags):
                return cand_key
        return None

    def _compatible(self, food_flags: List[str], diet_flags: List[str]) -> bool:
        # For VEG diets, accept foods that have VEG flag, regardless of OMNI flag
        if "VEG" in diet_flags and "VEG" not in food_flags:
            return False
        # For PESC diets, reject foods that have OMNI flag
        if "PESC" in diet_flags and "OMNI" in food_flags:
            return False
        # For GF diets, reject foods that don't have GF flag
        if "GF" in diet_flags and "GF" not in food_flags:
            return False
        return True

    def aggregate_shopping(self, days: List[dict], lang: Language = "en") -> List[dict]:
        basket: Dict[str, float] = {}
        for d in days:
            for meal in d["meals"]:
                for name, grams in meal["grams"].items():
                    basket[name] = basket.get(name, 0.0) + float(grams)
        out = []
        for name, grams in sorted(basket.items()):
            price = 0.0
            if name in self.items and self.items[name].price:
                # RU: цена за 100 г → масштабируем
                price = round(self.items[name].price * (grams / 100.0), 2)
            # Add translated name to shopping list
            translated_name = self.get_translated_food_name(name, lang)
            # Enhanced rounding to nearest 10g for practical shopping
            rounded_grams = round(grams / 10.0) * 10
            out.append({
                "name": name,
                "name_translated": translated_name,
                "grams": rounded_grams,
                "price_est": price
            })
        return out
