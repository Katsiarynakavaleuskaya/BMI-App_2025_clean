# RU: Заглушка для Grok 2.5 — без реального вызова модели
# EN: Placeholder for Grok 2.5 — no real model call
import os

class GrokProvider:
    name = "grok"

    def __init__(self):
        self.model = os.getenv("GROK_MODEL", "grok-2.5")
        self.endpoint = os.getenv("GROK_ENDPOINT", "http://localhost:11434")
        # RU: Здесь позже добавим реальный клиент/SDK
        # EN: Later we will add real client/SDK here

    def generate(self, text: str) -> str:
        # RU: Плейсхолдер-ответ (чтобы не тянуть зависимостей)
        # EN: Placeholder response (no external deps)
        return f"[{self.name}:{self.model}] Insight: {text[:120]}"
