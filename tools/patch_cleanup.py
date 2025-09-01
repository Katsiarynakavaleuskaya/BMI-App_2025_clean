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
    Remove any @app.post-decorated route definition (decorators, function signature, and body) for the given function name from the module source.
    
    Scans the global `src` string for one or more @app.post(...) decorators immediately followed by a function definition named `func_name` (optionally `async`) and deletes that entire block. If a block is removed, updates the globals `src` (modified source) and `changed` (set to True).
    
    Parameters:
        func_name (str): Name of the route handler function to remove.
    
    Side effects:
        Modifies the module-level variables `src` and `changed`. Does not return a value.
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
    """
    Ensure a specific line is present at the start of the source buffer, prepending it if missing.
    
    If `line` is not already contained in the module-level `src` string, this function prepends `line` (plus a newline) to `src` and sets the module-level `changed` flag to True. This function has no return value and mutates the globals `src` and `changed`.
    """
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
    """
    Ensure the /api/v1/bmi POST route includes the dependency that enforces X-API-Key validation.
    
    Searches the module source (global `src`) for an @app.post("/api/v1/bmi"...) decorator that does not already include a `dependencies=` argument and appends `, dependencies=[Depends(get_api_key)]` before the decorator's closing parenthesis. If any replacements are made the updated source is written back to the global `src` and the global `changed` flag is set True.
    
    Side effects:
    - Mutates global variables `src` and `changed`.
    
    Notes:
    - Only alters the decorator text; it will not modify function bodies or create duplicate dependency entries if `dependencies=` is already present.
    """
    global src, changed
    pattern = r'(@app\.post\("/api/v1/bmi"(?!.*dependencies=)\s*(?:,.*)?\))'
    def repl(m):
        """
        Replacement callback for re.sub that appends a `dependencies=[Depends(get_api_key)]` argument to a matched decorator string.
        
        Parameters:
            m (re.Match): Regex match whose group(1) is the decorator text (e.g., '@app.post("/api/v1/bmi", ...)').
        
        Returns:
            str: The possibly-modified decorator string with `, dependencies=[Depends(get_api_key)])` inserted before the trailing `)`.
        """
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
