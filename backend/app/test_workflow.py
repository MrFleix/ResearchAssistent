# test_workflow.py
import asyncio
from agents.graph import run_chat_workflow
from models.async_local_llm import AsyncLocalLLM


async def main():
    llm = AsyncLocalLLM()
    final_state = await run_chat_workflow("user1", "Hello world", llm_client=llm)

    print("Response:    ", final_state["output"]["response"])
    print("Node results:", final_state["node_results"])


if __name__ == "__main__":
    asyncio.run(main())