# -*- coding: utf-8 -*-
"""
FastAPI слой над ядром bmi_core.
Эндпоинты:
- GET  /health
- POST /bmi
- POST /plan
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Tuple
from bmi_core import (
    bmi_value, bmi_category, auto_group, interpret_group,
    compute_wht_ratio, build_premium_plan
)

app = FastAPI(title="BMI App API", version="1.0.0")
