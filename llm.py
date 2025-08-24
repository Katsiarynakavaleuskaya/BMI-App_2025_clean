# RU: Маршрутизатор LLM провайдеров по ENV-флагу LLM_PROVIDER
# EN: LLM providers router by ENV flag LLM_PROVIDER
import os
from typing import Optional

class ProviderBase:
    name: str = "base"

    def generate(self, text: str) -> str:
        raise NotImplementedError

def get_provider() -> Optional[ProviderBase]:
    name = os.getenv("LLM_PROVIDER", "stub").lower().strip()
    if name in {"", "none", "off"}:
        return None
    if name == "stub":
        from providers.stub import StubProvider
        return StubProvider()
    if name == "grok":
        from providers.grok import GrokProvider
        return GrokProvider()
    return None
