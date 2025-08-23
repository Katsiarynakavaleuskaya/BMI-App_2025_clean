from fastapi import FastAPI
from pydantic import BaseModel, Field, model_validator
from typing import Literal, Optional, Dict

app = FastAPI(title="BMI-App 2025")

# ---------- Models ----------
class BMIRequest(BaseModel):
    weight_kg: float = Field(..., gt=0)
    height_m: float = Field(..., gt=0)
    age: int = Field(..., ge=0, le=120)
    gender: str
    pregnant: str
    athlete: str
    waist_cm: Optional[float] = Field(None, gt=0)
    lang: Literal["ru", "en"] = "ru"
    premium: Optional[bool] = False

    @model_validator(mode="before")
    @classmethod
    def _normalize_values(cls, values: Dict):
        for k in ["gender", "pregnant", "athlete", "lang"]:
            if k in values and isinstance(values[k], str):
                values[k] = values[k].strip().lower()
        return values


# ---------- Core logic ----------
def calc_bmi(weight_kg: float, height_m: float) -> float:
    return round(weight_kg / (height_m ** 2), 1)


def category_by_bmi(bmi: float, lang: str = "ru") -> str:
    # WHO ranges; EN wording as tests expect
    if bmi < 18.5:
        return "Недостаточная масса" if lang == "ru" else "Underweight"
    if bmi < 25:
        return "Норма" if lang == "ru" else "Healthy weight"   # <- was "Normal"
    if bmi < 30:
        return "Избыточная масса" if lang == "ru" else "Overweight"
    return "Ожирение" if lang == "ru" else "Obesity"


def normalize_flags(gender: str, pregnant: str, athlete: str) -> Dict[str, bool]:
    gender_norm = {
        "male": "male", "муж": "male", "м": "male",
        "female": "female", "жен": "female", "ж": "female",
    }.get(gender, gender)

    preg_true = pregnant in {"да", "беременна", "pregnant", "yes", "y"}
    preg_false = pregnant in {"нет", "no", "not", "n"}
    is_pregnant = preg_true and gender_norm == "female" and not preg_false

    is_athlete = athlete in {"спортсмен", "да", "yes", "y", "athlete", "true"}

    return {"gender_male": gender_norm == "male", "is_pregnant": is_pregnant, "is_athlete": is_athlete}


def waist_risk(waist_cm: Optional[float], gender_male: bool, lang: str = "ru") -> str:
    if waist_cm is None:
        return ""
    warn, high = (94, 102) if gender_male else (80, 88)
    if waist_cm >= high:
        return "Высокий риск по талии" if lang == "ru" else "High waist-related risk"
    if waist_cm >= warn:
        return "Повышенный риск по талии" if lang == "ru" else "Increased waist-related risk"
    return ""


# ---------- Endpoints ----------
@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/bmi")
def bmi_endpoint(req: BMIRequest):
    flags = normalize_flags(req.gender, req.pregnant, req.athlete)
    bmi = calc_bmi(req.weight_kg, req.height_m)

    if flags["is_pregnant"]:
        note = "BMI не применим при беременности" if req.lang == "ru" else "BMI is not valid during pregnancy"
        return {
            "bmi": bmi,
            "category": None,
            "note": note,
            "athlete": flags["is_athlete"],
            "group": "general" if not flags["is_athlete"] else "athlete",
        }

    category = category_by_bmi(bmi, req.lang)
    notes = []
    if flags["is_athlete"]:
        notes.append("У спортсменов BMI может завышать жировую массу" if req.lang == "ru"
                     else "For athletes, BMI may overestimate body fat")
    wr = waist_risk(req.waist_cm, flags["gender_male"], req.lang)
    if wr:
        notes.append(wr)

    return {
        "bmi": bmi,
        "category": category,
        "note": " | ".join(notes) if notes else "",
        "athlete": flags["is_athlete"],
        "group": "athlete" if flags["is_athlete"] else "general",  # <- for tests
    }


@app.post("/plan")
def plan_endpoint(req: BMIRequest):
    flags = normalize_flags(req.gender, req.pregnant, req.athlete)
    bmi = calc_bmi(req.weight_kg, req.height_m)
    category = None if flags["is_pregnant"] else category_by_bmi(bmi, req.lang)

    healthy_bmi = {"min": 18.5, "max": 24.9}  # <- tests only check key presence

    if req.lang == "ru":
        base = {
            "summary": "Персональный план (MVP)",
            "bmi": bmi,
            "category": category,
            "premium": bool(req.premium),
            "next_steps": ["Шаги: 7–10 тыс/день", "Белок: 1.2–1.6 г/кг", "Сон: 7–9 часов"],
            "healthy_bmi": healthy_bmi,
        }
        if req.premium:
            base["premium_reco"] = ["Дефицит 300–500 ккал", "2–3 силовые тренировки/нед"]
    else:
        base = {
            "summary": "Personal plan (MVP)",
            "bmi": bmi,
            "category": category,
            "premium": bool(req.premium),
            "next_steps": ["Steps: 7–10k/day", "Protein: 1.2–1.6 g/kg", "Sleep: 7–9 h"],
            "healthy_bmi": healthy_bmi,
        }
        if req.premium:
            base["premium_reco"] = ["Calorie deficit 300–500 kcal", "2–3 strength sessions/week"]

    return base
