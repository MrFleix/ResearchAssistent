# agents/nodes/chat_node.py
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

        if not message:
            raise ValueError("message cannot be empty")

        response_text = (
            await llm_client.generate(message)
            if llm_client
            else f"Echo: {message}"
        )

        # Pydantic validiert
        node_output = ChatNode.Output(
            node=ChatNode.name,
            user_message=message,
            response=response_text,
            metadata={"length": len(response_text)},
        )

        # LangGraph bekommt dict
        output_dict = node_output.model_dump()
        return {
            **state,
            "node_results": state.get("node_results", []) + [output_dict],
            "output": output_dict,
        }