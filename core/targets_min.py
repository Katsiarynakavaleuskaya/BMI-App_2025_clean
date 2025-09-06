"""
Minimal Targets Estimation Utility

RU: Очень простой расчёт на время разработки.
EN: Minimal targets for development.
"""

from typing import Dict


def estimate_targets_minimal(sex: str, age: int, height_cm: int, weight_kg: float,
                             activity: float, goal: str) -> Dict:
    """
    RU: Очень простой расчёт на время разработки.
    EN: Minimal targets for dev.

    Args:
        sex: User's sex ("male" or "female")
        age: User's age in years
        height_cm: User's height in centimeters
        weight_kg: User's weight in kilograms
        activity: Activity level multiplier
        goal: User's goal ("loss", "gain", or "maintain")

    Returns:
        Dictionary with estimated nutrition targets
    """
    # BMR Mifflin-St Jeor
    s = 5 if (sex or "").lower().startswith("m") else -161
    bmr = 10*weight_kg + 6.25*height_cm - 5*age + s
    tdee = max(1200, int(bmr * max(1.1, min(activity or 1.4, 2.5))))
    if (goal or "maintain") == "loss":
        kcal = max(1200, int(tdee - 400))
    elif goal == "gain":
        kcal = int(tdee + 300)
    else:
        kcal = int(tdee)

    # протеин 1.6 г/кг, жир 0.9 г/кг, угли — остаток
    protein = round(1.6 * weight_kg, 1)
    fat = round(0.9 * weight_kg, 1)
    carbs = round((kcal - (protein*4 + fat*9)) / 4, 1)
    fiber = 28

    micro = {
        "Fe_mg": 18.0 if (sex or "f").lower().startswith("f") else 8.0,
        "Ca_mg": 1000.0,
        "VitD_IU": 600.0,
        "B12_ug": 2.4,
        "Folate_ug": 400.0,
        "Iodine_ug": 150.0,
        "K_mg": 3500.0,
        "Mg_mg": 320.0 if (sex or "f").lower().startswith("f") else 420.0,
    }

    return {
        "kcal": kcal,
        "macros": {"protein_g": protein, "fat_g": fat, "carbs_g": carbs, "fiber_g": fiber},
        "micro": micro,
        "water_ml": int(30 * weight_kg),
        "activity_week": {"mvpa_min": 150}
    }
