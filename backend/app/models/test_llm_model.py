# test_llm.py
import asyncio
from api_model import LLMClient

async def main():
    llm = LLMClient()
    prompt = "Schreibe mir einen Satz über LangGraph in einem Hackathon-Kontext."
    
    result = await llm.generate(prompt)
    
    print("Text Output:")
    print(result["text"])
    print("\nToken Usage:")
    print(result["usage"])

if __name__ == "__main__":
    asyncio.run(main())