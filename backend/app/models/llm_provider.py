import os
from backend.app.models.async_local_llm import AsyncLocalLLM
from backend.app.models.api_model import LLMClient   # deine API Klasse

class LLMProvider:

    def __init__(self):
        mode = os.getenv("LLM_MODE", "api")

        if mode == "api":
            print("Use API LLM")
            self.llm = LLMClient()
            self.mode = "api"
        else:
            print("Use Local LLM")
            self.llm = AsyncLocalLLM()
            self.mode = "local"

    async def generate(self, prompt: str):

        if self.mode == "api":
            result = await self.llm.generate(prompt)
            return result["text"]

        else:
            return await self.llm.generate(prompt)