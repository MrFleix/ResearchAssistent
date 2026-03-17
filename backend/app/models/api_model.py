# api_model.py
from openai import AsyncOpenAI
from typing import AsyncGenerator


class LLMClient:

    def __init__(self):
        self.client = AsyncOpenAI(
            api_key="rc_ef9397ac37bc220c758c81f9a21d4b7389cad75c82f514ed8bd8703fb17cd920",
            base_url="https://api.featherless.ai/v1"
        )
        self.model = "Qwen/Qwen2.5-72B-Instruct"

    async def generate(self, prompt: str) -> dict:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )
        return {
            "text": response.choices[0].message.content,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }
        }

    async def generate_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
        )
        async for chunk in stream:
            if not chunk.choices:
                continue
            token = chunk.choices[0].delta.content
            if token is not None:
                yield token