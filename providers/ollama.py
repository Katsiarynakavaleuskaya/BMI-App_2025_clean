from openai import OpenAI

class OllamaProvider:
    name = "ollama"

    def __init__(self, base_url: str, model: str, api_key: str = ""):
        self.model = model
        self.client = OpenAI(base_url=base_url, api_key=api_key or "ollama-no-key")

    def generate(self, text: str):
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": text}],
            temperature=0.2,
        )
        return resp.choices[0].message.content.strip()
