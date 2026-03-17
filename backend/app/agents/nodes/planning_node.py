# backend/app/agents/nodes/planning_node.py
from typing import ClassVar, Dict, Any, List
from pydantic import field_validator
from backend.app.agents.state import BaseNodeOutput

class PlanningNode:
    name: ClassVar[str] = "PlanningNode"

    class Output(BaseNodeOutput):
        steps: List[Dict[str, Any]]

        @field_validator("steps")
        @classmethod
        def non_empty_steps(cls, v):
            if not v:
                raise ValueError("Plan steps cannot be empty")
            return v

    @staticmethod
    async def run(state: dict, llm_client=None) -> dict:
        goal = state.get("goal", "")
        intent = state.get("intent", "")

        # LLM Prompt
        if llm_client:
            import json
            prompt = f"""
Create a minimal plan for this user request.

Goal: {goal}
Intent: {intent}

Return JSON list like:
[{{"action": "respond"}}]
"""
            try:
                steps = json.loads(await llm_client.generate(prompt))
            except:
                steps = [{"action": "respond"}]
        else:
            steps = [{"action": "respond"}]

        # Pydantic Output
        node_output = PlanningNode.Output(
            node=PlanningNode.name,
            steps=steps,
            metadata={"steps_count": len(steps)}
        )

        output_dict = node_output.model_dump()
        return {
            **state,
            "plan": steps,
            "node_results": state.get("node_results", []) + [output_dict],
            "output": output_dict,
        }