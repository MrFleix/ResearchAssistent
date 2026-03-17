# backend/app/agents/nodes/reasoning_node.py
from typing import ClassVar, Dict, Any, List
from pydantic import field_validator
from backend.app.agents.state import BaseNodeOutput

class ReasoningNode:
    name: ClassVar[str] = "ReasoningNode"

    class Output(BaseNodeOutput):
        goal: str
        intent: str
        complexity: str
        key_points: List[str]

        @field_validator("goal")
        @classmethod
        def non_empty_goal(cls, v):
            if not v.strip():
                raise ValueError("Goal cannot be empty")
            return v

    @staticmethod
    async def run(state: dict, llm_client=None) -> dict:
        message = state.get("message", "").strip()
        if not message:
            raise ValueError("message cannot be empty")

        # LLM Prompt
        if llm_client:
            import json
            prompt = f"""
Analyze the user request and extract:

- goal
- intent (coding, question, smalltalk)
- complexity (low, medium, high)
- key_points (list)

Message: {message}
"""
            try:
                data = await llm_client.generate(prompt)
                data_dict = json.loads(data)
            except:
                data_dict = {
                    "goal": message,
                    "intent": "unknown",
                    "complexity": "low",
                    "key_points": [message],
                }
        else:
            data_dict = {
                "goal": message,
                "intent": "unknown",
                "complexity": "low",
                "key_points": [message],
            }

        # Pydantic Output
        node_output = ReasoningNode.Output(
            node=ReasoningNode.name,
            goal=data_dict["goal"],
            intent=data_dict["intent"],
            complexity=data_dict["complexity"],
            key_points=data_dict["key_points"],
            metadata={"key_points_len": len(data_dict["key_points"])},
        )

        output_dict = node_output.model_dump()
        return {
            **state,
            **data_dict,
            "node_results": state.get("node_results", []) + [output_dict],
            "output": output_dict,
        }