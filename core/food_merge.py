"""
Food Data Merge Logic

RU: Логика мерджа данных о продуктах.
EN: Food data merge logic.

This module implements a unified pipeline to merge USDA, CIQUAL, FAO/INFOODS, and OpenFoodFacts data
with conflict resolution strategies and priority-based merging.

Priority for micronutrients: USDA > CIQUAL > INFOODS > OFF (where values are available)
Macro nutrients: median of all available values
Price/flags: from OFF or manual sources
"""

from __future__ import annotations

import os
from collections import defaultdict
from datetime import date
from statistics import median
from typing import Dict, Iterable, List

from .food_sources.base import FoodRecord

# Micro nutrients list
MICROS = ["Fe_mg", "Ca_mg", "VitD_IU", "B12_ug", "Folate_ug", "Iodine_ug", "K_mg", "Mg_mg"]

# Default source priority for micronutrients (highest → lowest)
# Exported for tests and documentation.
PRIORITY = ["USDA", "CIQUAL", "INFOODS", "OFF"]

def _priority():
    # Start from default priority, allow override via ENV
    base_str = os.getenv("FOOD_MICRO_PRIORITY_BASE", ",".join(PRIORITY))
    base = base_str.split(",")
    # расширения по флагам
    if os.getenv("FOOD_ENABLE_CIQUAL") == "1":
        base.insert(1, "CIQUAL")           # после USDA
    if os.getenv("FOOD_ENABLE_INFOODS") == "1":
        base.append("INFOODS")             # ниже CIQUAL/USDA
    # убираем дубли, сохраняя порядок
    seen, out = set(), []
    for s in base:
        s = s.strip()
        if s and s not in seen:
            seen.add(s); out.append(s)
    return out

def micro_pick(rows: List[FoodRecord], key: str) -> float:
    """
    Pick micronutrient value using source priority. Falls back to median across
    all sources if none in the priority list provide a value.
    """
    prio = _priority()
    for src in prio:
        vals = [getattr(r, key, None) for r in rows
                if getattr(r, key, None) is not None and getattr(r, "source", None) == src]
        vals = [v for v in vals if isinstance(v, (int, float)) and v >= 0]
        if vals:
            return float(median(vals))
    vals = [getattr(r, key, None) for r in rows if getattr(r, key, None) is not None]
    vals = [v for v in vals if isinstance(v, (int, float)) and v >= 0]
    return float(median(vals or [0.0]))

def _merge_values(values: List[float], strategy: str = "median") -> float:
    """
    RU: Объединить значения по стратегии.
    EN: Merge values by strategy.

    Args:
        values: List of values to merge
        strategy: Merge strategy ("median" or "first")

    Returns:
        Merged value
    """
    vals = [v for v in values if v is not None and v >= 0]
    if not vals:
        return 0.0
    if strategy == "median":
        return float(median(vals))
    return float(vals[0])

def merge_records(streams: List[Iterable[FoodRecord]]) -> List[Dict]:
    """
    RU: Объединить записи из нескольких источников.
    EN: Merge records from multiple sources.

    Args:
        streams: List of iterables with FoodRecord objects

    Returns:
        List of merged food records as dictionaries
    """
    # Group records by canonical name
    bucket: Dict[str, List[FoodRecord]] = defaultdict(list)
    for stream in streams:
        for rec in stream:
            bucket[rec.name].append(rec)

    merged: List[Dict] = []
    today = date.today().isoformat()

    for name, rows in bucket.items():
        # Merge macronutrients using median
        def macro_pick(key: str) -> float:
            vals = [getattr(r, key, 0.0) for r in rows if getattr(r, key, None) is not None]
            vals = [v for v in vals if v >= 0]
            return float(median(vals or [0.0]))

        kcal = macro_pick("kcal")
        protein = macro_pick("protein_g")
        fat = macro_pick("fat_g")
        carbs = macro_pick("carbs_g")
        fiber = macro_pick("fiber_g")

        # Priority for micronutrients: dynamic based on ENV flags

        # Collect all flags
        all_flags = set()
        for r in rows:
            if r.flags:
                all_flags.update(r.flags)

        # Determine primary source for logging
        sources = sorted({r.source for r in rows})

        out = {
            "name": name,
            "group": "other",  # Will be determined by classification logic
            "per_g": 100.0,
            "kcal": round(kcal, 1),
            "protein_g": round(protein, 2),
            "fat_g": round(fat, 2),
            "carbs_g": round(carbs, 2),
            "fiber_g": round(fiber, 2),
            **{k: round(micro_pick(rows, k), 3) for k in MICROS},
            "flags": list(sorted(all_flags)),
            "price": 0.0,  # Can be populated from OFF later
            "source": "MERGED(" + ",".join(sources) + ")",
            "version_date": today,
        }
        merged.append(out)

    # Classify food groups based on macronutrient profile
    for record in merged:
        record["group"] = _classify_food_group(record)

    return merged

def _classify_food_group(record: Dict) -> str:
    """
    RU: Классифицировать продукт по группе на основе профиля макронутриентов.
    EN: Classify food by group based on macronutrient profile.

    Args:
        record: Food record dictionary

    Returns:
        Food group classification
    """
    protein_pct = (record["protein_g"] * 4 / max(1, record["kcal"])) * 100 if record["kcal"] > 0 else 0
    fat_pct = (record["fat_g"] * 9 / max(1, record["kcal"])) * 100 if record["kcal"] > 0 else 0
    carb_pct = (record["carbs_g"] * 4 / max(1, record["kcal"])) * 100 if record["kcal"] > 0 else 0

    # High protein foods (>15% of calories from protein)
    if protein_pct > 15:
        if record["fat_g"] > 5:  # High fat protein (e.g., nuts, seeds)
            return "protein"
        else:  # Lean protein (e.g., chicken, fish)
            return "protein"

    # High fat foods (>30% of calories from fat)
    if fat_pct > 30:
        return "fat"

    # High carb foods (>50% of calories from carbs)
    if carb_pct > 50:
        if record["fiber_g"] > 3:  # High fiber carbs (e.g., whole grains, legumes)
            if "legume" in record["name"] or any(legume in record["name"] for legume in ["lentil", "bean", "chickpea"]):
                return "legume"
            return "grain"
        elif record["sugar_g"] > 10 if "sugar_g" in record else False:  # High sugar carbs
            return "fruit"
        else:  # Starchy carbs
            return "grain"

    # Vegetables (moderate carbs, high fiber, low calories)
    if record["fiber_g"] > 2 and record["kcal"] < 100:
        return "veg"

    # Fruits (moderate carbs, natural sugars)
    if record["sugar_g"] > 5 if "sugar_g" in record else False:
        return "fruit"

    # Dairy (if has dairy flags)
    if any("DAIRY" in flag for flag in record["flags"]):
        return "dairy"

    # Default classification
    return "other"
