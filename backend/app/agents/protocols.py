# agents/protocols.py
from typing import Protocol


class LLMClient(Protocol):
    async def generate(self, prompt: str) -> str: ...
