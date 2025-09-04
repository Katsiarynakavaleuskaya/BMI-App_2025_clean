"""Unit tests for core.food_db_new to increase coverage."""

import csv
import os
import tempfile

from core.food_db_new import FoodDB


def _write_food_csv(path: str):
    fields = [
        "name","group","per_g","protein_g","fat_g","carbs_g","fiber_g",
        "Fe_mg","Ca_mg","VitD_IU","B12_ug","Folate_ug","Iodine_ug","K_mg","Mg_mg",
        "flags","price",
    ]
    rows = [
        {
            "name": "spinach",
            "group": "veg",
            "per_g": 100,
            "protein_g": 2.9,
            "fat_g": 0.4,
            "carbs_g": 3.6,
            "fiber_g": 2.2,
            "Fe_mg": 2.7,
            "Ca_mg": 99,
            "VitD_IU": 0,
            "B12_ug": 0,
            "Folate_ug": 194,
            "Iodine_ug": 20,
            "K_mg": 558,
            "Mg_mg": 79,
            "flags": "VEG;GF",
            "price": 1.2,
        },
        {
            "name": "chicken_breast",
            "group": "protein",
            "per_g": 100,
            "protein_g": 31,
            "fat_g": 3.6,
            "carbs_g": 0,
            "fiber_g": 0,
            "Fe_mg": 0.7,
            "Ca_mg": 15,
            "VitD_IU": 0.7,
            "B12_ug": 0.3,
            "Folate_ug": 6,
            "Iodine_ug": 7,
            "K_mg": 256,
            "Mg_mg": 27,
            "flags": "OMNI",
            "price": 2.5,
        },
        {
            "name": "greek_yogurt",
            "group": "dairy",
            "per_g": 100,
            "protein_g": 10,
            "fat_g": 0.4,
            "carbs_g": 3.6,
            "fiber_g": 0,
            "Fe_mg": 0.1,
            "Ca_mg": 110,
            "VitD_IU": 0,
            "B12_ug": 0.4,
            "Folate_ug": 7,
            "Iodine_ug": 5,
            "K_mg": 140,
            "Mg_mg": 11,
            "flags": "DAIRY;GF",
            "price": 1.8,
        },
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def test_fooddb_pick_booster_respects_flags_and_translation():
    fd, path = tempfile.mkstemp(suffix=".csv")
    os.close(fd)
    try:
        _write_food_csv(path)
        db = FoodDB(path)

        # For iron, with VEG diet, should not pick chicken (OMNI), prefer spinach
        pick = db.pick_booster_for("Fe_mg", ["VEG"])
        assert pick == "spinach"

        # Translation for shopping names will use meal_i18n
        name_es = db.get_translated_food_name("spinach", "es")
        assert name_es == "Espinacas"
    finally:
        os.unlink(path)


def test_aggregate_shopping_accumulates_grams_and_prices_and_translates():
    fd, path = tempfile.mkstemp(suffix=".csv")
    os.close(fd)
    try:
        _write_food_csv(path)
        db = FoodDB(path)
        days = [
            {"meals": [{"grams": {"spinach": 150.0, "greek_yogurt": 100.0}}]},
            {"meals": [{"grams": {"spinach": 50.0}}]},
        ]
        out = db.aggregate_shopping(days, lang="es")
        # Expect two items
        names = {x["name"] for x in out}
        assert names == {"spinach", "greek_yogurt"}
        # Spinach grams aggregated to 200, price 1.2 per 100g => 2.4
        spin = next(x for x in out if x["name"] == "spinach")
        assert spin["grams"] == 200
        assert spin["price_est"] == 2.4
        assert spin["name_translated"]
    finally:
        os.unlink(path)

