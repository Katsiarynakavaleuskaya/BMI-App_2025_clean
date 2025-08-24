import os
from typing import Optional
from providers import ProviderBase

def _get_stub() -> ProviderBase:
    from providers.stub import StubProvider
    return StubProvider()

def _get_grok() -> ProviderBase:
    from providers.grok import GrokProvider
    endpoint = os.getenv("GROK_ENDPOINT", "https://api.x.ai/v1")
    model = os.getenv("GROK_MODEL", "grok-4-latest")
    api_key = os.getenv("GROK_API_KEY") or os.getenv("XAI_API_KEY")
    return GrokProvider(endpoint=endpoint, model=model, api_key=api_key)

def _get_ollama() -> ProviderBase:
    from providers.ollama import OllamaProvider
    return OllamaProvider(
        endpoint=os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434"),
        model=os.getenv("OLLAMA_MODEL", "llama3.1:8b"),
        api_key=None,
    )

def _get_pico() -> ProviderBase:
    from providers.pico import PicoProvider
    return PicoProvider(
        endpoint=os.getenv("PICO_ENDPOINT", os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434")),
        model=os.getenv("PICO_MODEL", os.getenv("OLLAMA_MODEL", "llama3.1:8b")),
        api_key=None,
    )

def get_provider() -> Optional[ProviderBase]:
    name = (os.getenv("Llm_PROVIDER") or os.getenv("LLM_PROVIDER") or "stub").strip().lower()
    if name in {"", "none", "off"}:
        return None
    if name == "stub":
        return _get_stub()
    if name == "grok":
        return _get_grok()
    if name == "ollama":
        return _get_ollama()
    if name == "pico":
        return _get_pico()
    return None

def get_provider_with_fallback() -> ProviderBase:
    """
    Пытается выбрать провайдера из LLM_PROVIDER.
    Если не получилось — возвращает stub, чтобы /insight не падал.
    """
    try:
        p = get_provider()
        return p if p is not None else _get_stub()
    except Exception:
        return _get_stub()
