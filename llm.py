# -*- coding: utf-8 -*-
"""
RU: Минимальная фабрика LLM-провайдера для тестов: 'stub' | 'grok' | 'ollama'.
EN: Minimal LLM provider factory for tests: 'stub' | 'grok' | 'ollama'.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Protocol


class ProviderBase(Protocol):
    name: str
    async def generate(self, text: str) -> str: ...


# --- Stub (без внешних зависимостей) ---
class StubProvider:
    name = "stub"
    async def generate(self, text: str) -> str:
        dt = datetime.now(timezone.utc).isoformat()
        return f"[stub @ {dt}] Insight: {text}"


# --- Пытаемся подтянуть реальный GrokProvider; иначе даём лёгкую заглушку ---
try:
    from providers.grok import GrokProvider  # type: ignore
except Exception:
    GrokProvider = None  # type: ignore

class GrokLiteProvider:
    name = "grok"
    async def generate(self, text: str) -> str:
        return f"[grok-lite] {text}"


def get_provider():
    """
    RU: Возвращает инстанс провайдера по env LLM_PROVIDER:
        'stub' | 'grok' | 'ollama' | None (по умолчанию None).
    EN: Returns provider instance by env LLM_PROVIDER:
        'stub' | 'grok' | 'ollama' | None (default None).
    """
    val = (os.getenv("LLM_PROVIDER") or "").strip().lower()

    if val in {"", "none", "no"}:
        return None

    if val in {"stub", "test", "fake"}:
        return StubProvider()

    if val == "grok":
        # Если есть реальный провайдер и ключ — вернём его; иначе лёгкий фоллбек
        if GrokProvider:
            api_key = os.getenv("GROK_API_KEY") or os.getenv("XAI_API_KEY")
            model = os.getenv("GROK_MODEL", "grok-4-latest")
            endpoint = os.getenv("GROK_ENDPOINT", "https://api.x.ai/v1")
            try:
                if api_key:
                    return GrokProvider(endpoint=endpoint, api_key=api_key, model=model)  # type: ignore
            except Exception:
                pass
        return GrokLiteProvider()

    if val == "ollama":
        try:
            from providers.ollama import OllamaProvider  # lazy import
        except Exception:
            return None
        endpoint = os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434")
        model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
        try:
            timeout = float(os.getenv("OLLAMA_TIMEOUT", "5"))
        except ValueError:
            timeout = 5.0
        return OllamaProvider(endpoint=endpoint, model=model, timeout_s=timeout)  # type: ignore

    # неизвестное значение
    return None


__all__ = ["get_provider", "ProviderBase", "StubProvider", "GrokLiteProvider"]
