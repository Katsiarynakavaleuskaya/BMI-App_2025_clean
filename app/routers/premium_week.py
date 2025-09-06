"""
Premium Week Plan Router

RU: Роутер для генерации недельного плана питания.
EN: Router for generating weekly meal plans.
"""


from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel

# Import the security dependency
from app.deps.security import get_api_key
from core.exports_premium import to_csv_premium_week, to_pdf_premium_week
from core.food_db_new import FoodDB
from core.i18n import Language
from core.recipe_db_new import RecipeDB

# Re-exports for test compatibility
from core.recommendations import build_nutrition_targets as _bnt
from core.targets_min import estimate_targets_minimal as _est_min
from core.weekly_plan_new import build_week

# Make available for patch.object(app.routers.premium_week, ...)
build_nutrition_targets = _bnt
estimate_targets_minimal_new = _est_min

router = APIRouter(prefix="/api/v1/premium/plan", tags=["premium"])

class WeekPlanRequest(BaseModel):
    targets: str
    diet_flags: str = ""
    lang: str = "en"

@router.post("/week")
async def generate_weekly_plan(req: WeekPlanRequest):
    """Generate a weekly meal plan based on nutritional targets."""
    try:
        import json
        targets_dict = json.loads(req.targets)
        diet_flags_list = req.diet_flags.split(",") if req.diet_flags else []

        # Load databases
        fooddb = FoodDB("data/food_db_new.csv")
        recipedb = RecipeDB("data/recipes_new.csv", fooddb)

        # Build week
        week = build_week(targets_dict, diet_flags_list, req.lang, fooddb, recipedb)

        return week
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate weekly plan: {str(e)}")

@router.get("/week/export/csv",
    summary="Export Weekly Plan to CSV",
    description="Export the generated weekly meal plan to CSV format. Accepts targets as JSON string and diet flags as comma-separated values.",
    responses={
        200: {
            "description": "CSV file download",
            "content": {
                "text/csv": {
                    "example": "Premium Weekly Meal Plan\n\nWeekly Nutrient Coverage\nNutrient,Coverage (%)\nFe_mg,85.0\nCa_mg,92.0\n..."
                }
            }
        }
    },
    dependencies=[Depends(get_api_key)])
async def export_week_plan_csv(
    targets: str,  # JSON string of targets
    diet_flags: str = "",  # comma-separated diet flags
    lang: Language = "en"
):
    """Export weekly plan to CSV format."""
    try:
        import json
        targets_dict = json.loads(targets)
        diet_flags_list = diet_flags.split(",") if diet_flags else []

        # Load databases
        fooddb = FoodDB("data/food_db_new.csv")
        recipedb = RecipeDB("data/recipes_new.csv", fooddb)

        # Build week
        week = build_week(targets_dict, diet_flags_list, lang, fooddb, recipedb)

        # Export to CSV
        csv_data = to_csv_premium_week(week)

        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=weekly_meal_plan.csv"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CSV export failed: {str(e)}")

@router.get("/week/export/pdf",
    summary="Export Weekly Plan to PDF",
    description="Export the generated weekly meal plan to PDF format. Accepts targets as JSON string and diet flags as comma-separated values.",
    responses={
        200: {
            "description": "PDF file download",
            "content": {
                "application/pdf": {
                    "example": "PDF binary data"
                }
            }
        }
    },
    dependencies=[Depends(get_api_key)])
async def export_week_plan_pdf(
    targets: str,  # JSON string of targets
    diet_flags: str = "",  # comma-separated diet flags
    lang: Language = "en"
):
    """Export weekly plan to PDF format."""
    try:
        import json
        targets_dict = json.loads(targets)
        diet_flags_list = diet_flags.split(",") if diet_flags else []

        # Load databases
        fooddb = FoodDB("data/food_db_new.csv")
        recipedb = RecipeDB("data/recipes_new.csv", fooddb)

        # Build week
        week = build_week(targets_dict, diet_flags_list, lang, fooddb, recipedb)

        # Export to PDF
        pdf_data = to_pdf_premium_week(week)

        return Response(
            content=pdf_data,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=weekly_meal_plan.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF export failed: {str(e)}")
