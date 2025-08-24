import os
from typing import Optional, List

# Базовый протокол
class ProviderBase:
    name: str
    def generate(self, text: str) -> str: ...

def _truthy(v: str) -> bool:
    return str(v or "").strip().lower() in {"1", "true", "yes", "on"}

def _get_grok():
    from providers.grok import GrokProvider
    endpoint = os.getenv("GROK_ENDPOINT", "https://api.x.ai/v1")
    model = os.getenv("GROK_MODEL", "grok-4-latest")
    api_key = os.getenv("XAI_API_KEY", "")
    return GrokProvider(endpoint=endpoint, model=model, api_key=api_key)

def _get_pico():
    from providers.pico import PicoProvider
    base_url = os.getenv("PICO_BASE_URL", "http://localhost:8077/v1")
    api_key = os.getenv("PICO_API_KEY", "")
    return PicoProvider(base_url=base_url, api_key=api_key)

def _get_ollama():
    from providers.ollama import OllamaProvider
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
    api_key = os.getenv("OLLAMA_API_KEY", "")
    return OllamaProvider(base_url=base_url, model=model, api_key=api_key)

def get_provider() -> Optional[ProviderBase]:
    """
    Возвращает основной провайдер из LLM_PROVIDER: pico|ollama|grok|stub
    """
    name = (os.getenv("LLM_PROVIDER", "pico") or "").strip().lower()
    if name == "pico":
        return _get_pico()
    if name == "ollama":
        return _get_ollama()
    if name == "grok":
        return _get_grok()
    if name == "stub":
        from providers.stub import StubProvider
        return StubProvider()
    return None

class FallbackProvider(ProviderBase):
    """
    Простой fallback: перебираем провайдеры по списку.
    Любая ошибка → пробуем следующий.
    """
    def __init__(self, providers: List[ProviderBase]):
        self.providers = providers
        self.name = "fallback(" + ",".join(p.name for p in providers) + ")"

    def generate(self, text: str) -> str:
        last_err = None
        for p in self.providers:
            try:
                return p.generate(text)
            except Exception as e:
                last_err = e
                continue
        raise RuntimeError(f"All providers failed: {last_err}")

def get_provider_with_fallback() -> ProviderBase:
    """
    Собираем цепочку: primary -> grok
    (primary = pico/ollama по LLM_PROVIDER)
    """
    primary = get_provider()
    if not primary:
        # по умолчанию — pico → grok
        return FallbackProvider([_get_pico(), _get_grok()])
    # если primary уже grok — просто его
    if primary.name == "grok":
        return primary
    # иначе primary → grok
    return FallbackProvider([primary, _get_grok()])
