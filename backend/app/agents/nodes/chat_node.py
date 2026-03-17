# backend/app/agents/nodes/chat_node.py
from typing import ClassVar, Dict, Any
from pydantic import field_validator
from backend.app.agents.state import BaseNodeOutput

class ChatNode:
    name: ClassVar[str] = "ChatNode"

    class Output(BaseNodeOutput):
        user_message: str
        response: str

        @field_validator("response")
        @classmethod
        def non_empty_response(cls, v):
            if not v.strip():
                raise ValueError("Response cannot be empty")
            return v

    @staticmethod
    async def run(state: dict, llm_client=None) -> dict:
        message = state.get("message", "").strip()
        goal = state.get("goal", "")
        intent = state.get("intent", "")
        key_points = state.get("key_points", [])

        if not message:
            raise ValueError("message cannot be empty")

        prompt = f"""
You are a helpful assistant.

Goal:
{goal}

Intent:
{intent}

Key points:
{key_points}

User:
{message}
"""
        # LLM oder Fallback
        response_text = (
            await llm_client.generate(prompt)
            if llm_client
            else f"Echo: {message}"
        )

        node_output = ChatNode.Output(
            node=ChatNode.name,
            user_message=message,
            response=response_text,
            metadata={"length": len(response_text)},
        )

        output_dict = node_output.model_dump()
        return {
            **state,
            "node_results": state.get("node_results", []) + [output_dict],
            "output": output_dict,
        }

    @staticmethod
    async def run_stream(state: dict, llm_client=None):
        """Streaming Variante für Live-Typing"""
        message = state.get("message", "").strip()
        goal = state.get("goal", "")
        intent = state.get("intent", "")
        key_points = state.get("key_points", [])

        prompt = f"""
You are a helpful assistant.

Goal:
{goal}

Intent:
{intent}

Key points:
{key_points}

User:
{message}
"""
        if not llm_client:
            yield f"Echo: {message}"
            return

        async for token in llm_client.generate_stream(prompt):
            yield token