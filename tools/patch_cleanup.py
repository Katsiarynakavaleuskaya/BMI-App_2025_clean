# ruff: noqa: E501
# -*- coding: utf-8 -*-
"""
Чистим дубликаты эндпоинтов /insight и /api/v1/insight в app.py,
возвращаем единую проверку X-API-Key для /api/v1/bmi и /api/v1/insight.
"""
import re
from pathlib import Path

p = Path("app.py")
src = p.read_text(encoding="utf-8")

changed = False

def drop_route(func_name: str):
    """
    Удаляет блок вида:
    @app.post("/...") [возможно с зависимостями/параметрами в декораторе в нескольких строках]
    (async )def func_name(...):
        <тело>
    """
    global src, changed
    # Захват декоратора(ов) над нужной функцией и самого тела функции
    pattern = rf"""
(?P<decorators>(?:^[ \t]*@app\.post\(.*\)\s*\n)+)   # один или несколько декораторов @app.post
^[ \t]*(?:async[ \t]+)?def[ \t]+{func_name}\s*\(.*?\):\s*\n   # сигнатура функции
(?:^[ \t]+.*\n|^\n)*                                   # тело (грубо)
"""
    src2, n = re.subn(pattern, "", src, flags=re.MULTILINE | re.DOTALL | re.VERBOSE)
    if n:
        src = src2
        changed = True

# 1) Сносим старые реализации этих функций (если были)
for fn in ("insight", "api_v1_insight"):
    drop_route(fn)

# 2) Импорты для зависимостей/моделей
def ensure(line: str):
    global src, changed
    if line not in src:
        src = line + "\n" + src
        changed = True

ensure("import os")
ensure("import llm")
ensure("from fastapi import FastAPI")
ensure("from fastapi import HTTPException, Header, Depends")
ensure("from pydantic import BaseModel")

# 3) Убедимся, что есть app
if "app = FastAPI(" not in src:
    src += "\n\napp = FastAPI(title='BMI-App_2025')\n"
    changed = True

# 4) Добавим единый хэндлер инсайта (без дублей, с правильным порядком проверок)
handler = r'''
# --- Insight endpoints (single source of truth) ---
class InsightIn(BaseModel):
    text: str

class InsightOut(BaseModel):
    provider: str
    result: str

def _is_true(val: str) -> bool:
    return str(val).lower() in {"1", "true", "yes", "on", "y"}

def get_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> None:
    expected = os.getenv("API_KEY", "test_key")
    if not x_api_key or x_api_key != expected:
        raise HTTPException(status_code=403, detail="Forbidden")

@app.post("/insight", name="insight_post", response_model=InsightOut, dependencies=[Depends(get_api_key)])
def insight(inp: InsightIn):
    # 2) feature flag
    if not _is_true(os.getenv("FEATURE_INSIGHT", "")):
        raise HTTPException(status_code=503, detail="insight feature disabled")
    # 3) provider
    provider = llm.get_provider()
    if provider is None:
        raise HTTPException(status_code=503, detail="No LLM provider configured")
    out = provider.generate(inp.text)
    return {"provider": getattr(provider, "name", "unknown"), "result": out}

@app.post("/api/v1/insight", name="api_v1_insight_post", response_model=InsightOut, dependencies=[Depends(get_api_key)])
def api_v1_insight(inp: InsightIn):
    return insight(inp)
'''

# Чистим нашу предыдущую вставку, если была (чтобы не плодить дубли при повторном запуске)
src = re.sub(r"\n# --- Insight endpoints \(single source of truth\).*?\Z", "", src, flags=re.DOTALL)

# 5) Добавляем свежий блок в конец
src = src.rstrip() + "\n\n" + handler.strip() + "\n"
changed = True

# 6) Включаем Depends(get_api_key) для /api/v1/bmi если вдруг отсутствует
# Ищем существующий декоратор и подставим зависимости, если их нет
def add_depends_for_bmi():
    global src, changed
    pattern = r'(@app\.post\("/api/v1/bmi"(?!.*dependencies=)\s*(?:,.*)?\))'
    def repl(m):
        dec = m.group(1)
        if dec.endswith(")"):
            dec = dec[:-1] + ", dependencies=[Depends(get_api_key)])"
        return dec
    new_src, n = re.subn(pattern, repl, src, flags=re.DOTALL)
    if n:
        src = new_src
        changed = True

add_depends_for_bmi()

if changed:
    p.write_text(src, encoding="utf-8")
    print("app.py cleaned & patched")
else:
    print("no changes")
