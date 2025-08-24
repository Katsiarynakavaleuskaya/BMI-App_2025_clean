from typing import Optional
from openai import OpenAI

class PicoProvider:
    name = "pico"

    def __init__(self, base_url: str, api_key: Optional[str] = ""):
        # Pico совместим с OpenAI API
        self.client = OpenAI(base_url=base_url, api_key=api_key or "pico-no-key")

    def generate(self, text: str, model: str = "gpt-3.5-turbo"):
        # Pico обычно игнорирует имя модели, но аргумент оставим для совместимости
        resp = self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": text}],
            temperature=0.2,
        )
        return resp.choices[0].message.content.strip()
