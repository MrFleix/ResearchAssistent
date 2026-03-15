# app/models/async_local_llm.py
import asyncio
from functools import lru_cache
from backend.app.models.local_model import LocalLLM


@lru_cache(maxsize=1)
def _get_llm(model_name: str) -> LocalLLM:
    return LocalLLM(model_name=model_name)


class AsyncLocalLLM:
    def __init__(self, model_name="Qwen/Qwen3-0.6B"):
        self.llm = _get_llm(model_name)  # cached, lädt nur einmal

    async def generate(self, prompt: str, max_length=128) -> str:
        return await asyncio.to_thread(self.llm.generate, prompt, max_length)