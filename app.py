# -*- coding: utf-8 -*-
"""
FastAPI слой над ядром bmi_core.
Маршруты:
- GET  /health
- POST /bmi
- POST /plan
"""
from typing import Optional, Tuple
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from bmi_core import (
    bmi_value, bmi_category, auto_group, interpret_group,
    compute_wht_ratio, build_premium_plan
)

app = FastAPI(title="BMI App API", version="1.0.0")

# --------- Модели ввода/вывода ----------
class BMIInput(BaseModel):
    weight_kg: float = Field(..., ge=30, le=300)
    height_m: float = Field(..., ge=0.5, le=2.5)
    age: int = Field(..., ge=1, le=120)
    gender: str
    pregnant: Optional[str] = None
    athlete: Optional[str] = None
    waist_cm: Optional[float] = Field(None, ge=10, le=300)
    lang: str = "ru"

class BMIResponse(BaseModel):
    bmi: float
    category: str
    group: str
    group_display: str
    message: str
    wht_ratio: Optional[float] = None
    wht_text: Optional[str] = None

class PlanInput(BMIInput):
    premium: bool = False

class PlanResponse(BMIResponse):
    healthy_bmi: Tuple[float, float]
    healthy_weight: Tuple[float, float]
    action: str
    delta_kg: float
    est_weeks: Optional[Tuple[int, int]] = None
    nutrition_tip: str
    activity_tip: str

# --------- Утилиты ----------
GROUP_DISPLAY = {
    "ru": {
        "general": "общая",
        "athlete": "спортсмен",
        "pregnant": "беременная",
        "elderly": "пожилой",
        "child": "подросток/ребёнок",
        "too_young": "слишком юный",
    },
    "en": {
        "general": "general",
        "athlete": "athlete",
        "pregnant": "pregnant",
        "elderly": "elderly",
        "child": "child/teen",
        "too_young": "too young",
    },
}

def _lang_norm(s: str) -> str:
    return s if s in ("ru", "en") else "ru"

def _wht_text(ratio: Optional[float], lang: str) -> Optional[str]:
    if ratio is None:
        return None
    if ratio < 0.40:
        cat = "ниже нормы" if lang == "ru" else "low"
    elif ratio <= 0.50:
        cat = "норма" if lang == "ru" else "healthy"
    elif ratio <= 0.60:
        cat = "повышенный риск" if lang == "ru" else "increased risk"
    else:
        cat = "высокий риск" if lang == "ru" else "high risk"
    return f"WHtR: {ratio:.2f} ({cat})"

# --------- Маршруты ----------
@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/bmi", response_model=BMIResponse)
def calc_bmi(body: BMIInput):
    try:
        lang = _lang_norm(body.lang)
        bmi = bmi_value(body.weight_kg, body.height_m)
        grp = auto_group(body.age, body.gender, body.pregnant or "нет", body.athlete or "нет", lang)
        cat = bmi_category(bmi, lang)
        msg = interpret_group(bmi, grp, lang)
        wht = compute_wht_ratio(body.waist_cm, body.height_m)
        disp = GROUP_DISPLAY[lang].get(grp, grp)
        return BMIResponse(
            bmi=bmi,
            category=cat,
            group=grp,
            group_display=disp,
            message=msg,
            wht_ratio=wht,
            wht_text=_wht_text(wht, lang),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/plan", response_model=PlanResponse)
def plan(body: PlanInput):
    try:
        lang = _lang_norm(body.lang)
        bmi = bmi_value(body.weight_kg, body.height_m)
        grp = auto_group(body.age, body.gender, body.pregnant or "нет", body.athlete or "нет", lang)
        cat = bmi_category(bmi, lang)
        msg = interpret_group(bmi, grp, lang)
        wht = compute_wht_ratio(body.waist_cm, body.height_m)
        disp = GROUP_DISPLAY[lang].get(grp, grp)

        pl = build_premium_plan(
            body.age, body.weight_kg, body.height_m, bmi, lang, grp, body.premium
        )
        weeks_raw = pl.get("est_weeks")
        weeks_out: Optional[Tuple[int, int]]
        if (
            not weeks_raw
            or not isinstance(weeks_raw, (list, tuple))
            or any(v is None for v in weeks_raw)
        ):
            weeks_out = None
        else:
            weeks_out = (int(weeks_raw[0]), int(weeks_raw[1]))

        return PlanResponse(
            bmi=bmi,
            category=cat,
            group=grp,
            group_display=disp,
            message=msg,
            wht_ratio=wht,
            wht_text=_wht_text(wht, lang),
            healthy_bmi=tuple(pl["healthy_bmi"]),
            healthy_weight=tuple(pl["healthy_weight"]),
            action=pl["action"],
            delta_kg=pl["delta_kg"],
            est_weeks=weeks_out,
            nutrition_tip=pl["nutrition_tip"],
            activity_tip=pl["activity_tip"],
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
# app.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health():
    # RU: Эндпоинт для проверки живости сервера
    # EN: Health check endpoint
    return {"status": "ok"}

