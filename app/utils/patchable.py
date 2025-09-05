# RU: единый безопасный резолвер "подменяемых" функций.
# EN: unified safe resolver for patchable functions.
from __future__ import annotations
import sys
from typing import Any, Callable

def resolve_patchable(name: str, fallback: Callable[..., Any]) -> Callable[..., Any]:
    mod = sys.modules.get("app")
    if mod and hasattr(mod, name):
        return getattr(mod, name)
    return fallback