# -*- coding: utf-8 -*-
"""
Patch app.py:
- Ensure API key check (403) happens BEFORE feature flag and provider checks
- Keep both /insight and /api/v1/insight
- 503 messages:
    * feature disabled -> "insight feature disabled"
    * no provider      -> "No LLM provider configured"
- Avoid duplicate operationId by setting unique 'name' in @app.post
"""
import re
from pathlib import Path

APP = Path("app.py")
src = APP.read_text(encoding="utf-8")

changed = False

def ensure_import(line: str):
    global src, changed
    if line not in src:
        src = line + "\n" + src
        changed = True

# Импорты
ensure_import("import os")
if "import llm" not in src:
    if m := re.search(
        r"(^|\n)(?:from\s+\S+\s+import\s+\S+|import\s+\S+)(?:.*\n)+", src
    ):
        src = src[:m.end()] + "import llm\n" + src[m.end():]
    else:
        ensure_import("import llm")

if "from fastapi import FastAPI" not in src:
    ensure_import("from fastapi import FastAPI")
if "from fastapi import HTTPException" not in src:
    ensure_import("from fastapi import HTTPException")
if "from fastapi import Header" not in src:
    ensure_import("from fastapi import Header")
if "from pydantic import BaseModel" not in src:
    ensure_import("from pydantic import BaseModel")

# Убедимся, что есть app = FastAPI(...)
if "app = FastAPI(" not in src:
    src += "\n\napp = FastAPI(title='BMI-App_2025')\n"
    changed = True

# Удалим старые вставки инсайта (если были)
src = re.sub(r"# --- Insight endpoints.*?(?=\n# ---|$)", "", src, flags=re.DOTALL)

handler = r'''
# --- Insight endpoints (idempotent patch) ---

class InsightIn(BaseModel):
    text: str

class InsightOut(BaseModel):
    provider: str
    result: str

def _is_true(val: str) -> bool:
    return str(val).lower() in {"1", "true", "yes", "on", "y"}

def _check_api_key(x_api_key: str | None) -> None:
    expected = os.getenv("API_KEY", "test_key")
    if not x_api_key or x_api_key != expected:
        raise HTTPException(status_code=403, detail="Forbidden")

@app.post("/insight", name="insight_post", response_model=InsightOut)
def insight(
    inp: InsightIn,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
):
    # 1) API key
    _check_api_key(x_api_key)

    # 2) feature flag
    if not _is_true(os.getenv("FEATURE_INSIGHT", "")):
        raise HTTPException(status_code=503, detail="insight feature disabled")

    # 3) provider
    provider = llm.get_provider()
    if provider is None:
        raise HTTPException(status_code=503, detail="No LLM provider configured")

    out = provider.generate(inp.text)
    return {"provider": getattr(provider, "name", "unknown"), "result": out}

@app.post("/api/v1/insight", name="api_v1_insight_post", response_model=InsightOut)
def api_v1_insight(
    inp: InsightIn,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
):
    return insight(inp, x_api_key=x_api_key)
'''

src = src.rstrip() + "\n\n" + handler.strip() + "\n"
changed = True

APP.write_text(src, encoding="utf-8")
print("app.py patched")
