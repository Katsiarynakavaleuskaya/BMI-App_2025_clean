# ruff: noqa: E501
# -*- coding: utf-8 -*-
"""
Добавляем health-check эндпоинты:
- GET /api/v1/health  -> 200 {"status":"ok"}
- GET /health         -> 200 {"status":"ok"}
Без проверки API-ключа. Идемпотентно: старые версии удаляем.
"""
import re
from pathlib import Path

p = Path("app.py")
src = p.read_text(encoding="utf-8")

changed = False

def ensure(line: str):
    """
    Ensure a specific line is present at the start of the module source.
    
    If the given line is not already present anywhere in the in-memory source buffer `src`,
    the function prepends the line plus a newline to `src` and sets the `changed` flag to True.
    
    Parameters:
        line (str): A single source line (without trailing newline) to ensure exists in `src`.
    
    Side effects:
        Modifies the module-level variables `src` and `changed`.
    """
    global src, changed
    if line not in src:
        src = line + "\n" + src
        changed = True

# Импорты и наличие app
ensure("from fastapi import FastAPI")
ensure("from fastapi import HTTPException, Header, Depends")  # уже может быть
ensure("from pydantic import BaseModel")  # уже может быть
if "app = FastAPI(" not in src:
    src += "\n\napp = FastAPI(title='BMI-App_2025')\n"
    changed = True

# Удаляем любые старые определения health
pattern = r"""
(^[ \t]*@app\.get\("/api/v1/health".*?\)\s*\n[ \t]*(?:async[ \t]+)?def[ \t]+[a-zA-Z_][a-zA-Z0-9_]*\(.*?\):\s*\n(?:^[ \t]+.*\n|^\n)*)
|(^[ \t]*@app\.get\("/health".*?\)\s*\n[ \t]*(?:async[ \t]+)?def[ \t]+[a-zA-Z_][a-zA-Z0-9_]*\(.*?\):\s*\n(?:^[ \t]+.*\n|^\n)*)
"""
src2, n = re.subn(pattern, "", src, flags=re.MULTILINE | re.DOTALL | re.VERBOSE)
if n:
    src = src2
    changed = True

handler = r'''
# --- Health endpoints ---
@app.get("/api/v1/health", name="api_v1_health")
def api_v1_health():
    return {"status": "ok"}

@app.get("/health", name="health")
def health():
    return {"status": "ok"}
'''

# Добавляем блок в конец
if "# --- Health endpoints ---" not in src:
    src = src.rstrip() + "\n\n" + handler.strip() + "\n"
    changed = True

if changed:
    p.write_text(src, encoding="utf-8")
    print("app.py: health endpoints added/updated")
else:
    print("no changes")
