"""Coverage-focused tests for core.meal_i18n."""

from core.meal_i18n import (
    translate_food,
    translate_meal_type,
    translate_recipe,
    translate_tip,
)


def test_translate_food_known_and_unknown_and_lang_fallback():
    # Known key
    assert translate_food("es", "spinach") == "Espinacas"
    # Unknown key returns original
    assert translate_food("es", "not_a_food") == "not_a_food"
    # Unknown language returns original
    assert translate_food("de", "spinach") == "spinach"


def test_translate_recipe_and_meal_type():
    assert translate_recipe("ru", "oatmeal_breakfast") == "Овсянка на завтрак"
    assert translate_recipe("xx", "oatmeal_breakfast") == "oatmeal_breakfast"
    assert translate_meal_type("en", "breakfast") == "Breakfast"
    assert translate_meal_type("xx", "breakfast") == "breakfast"


def test_translate_tip_with_donor_translation_and_missing():
    # Known tip key with donor translation
    msg = translate_tip("es", "low_Fe_mg", donor_food="spinach")
    assert "Espinacas" in msg
    # Unknown tip key returns original key
    assert translate_tip("en", "__missing__", donor_food="spinach") == "__missing__"
    # Unknown language returns key unchanged
    assert translate_tip("xx", "low_Fe_mg", donor_food="spinach") == "low_Fe_mg"

