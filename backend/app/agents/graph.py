import json
from langgraph.graph import StateGraph, END
from backend.app.agents.nodes.chat_node      import ChatNode
from backend.app.agents.nodes.reasoning_node import ReasoningNode
from backend.app.agents.nodes.planning_node  import PlanningNode
from backend.app.agents.state                import WorkflowState


def event(type: str, **data) -> str:
    """Einen typisierten JSON-Line Event erstellen."""
    return json.dumps({"type": type, **data}) + "\n"


def build_graph(llm_client=None, use_reasoning: bool = False):
    graph = StateGraph(WorkflowState)

    async def planning(state):
        return await PlanningNode.run(state, llm_client)

    async def chat(state):
        return await ChatNode.run(state, llm_client)

    graph.add_node("planning", planning)
    graph.add_node("chat",     chat)

    if use_reasoning:
        async def reasoning(state):
            return await ReasoningNode.run(state, llm_client)
        graph.add_node("reasoning", reasoning)
        graph.set_entry_point("reasoning")
        graph.add_edge("reasoning", "planning")
    else:
        graph.set_entry_point("planning")

    graph.add_edge("planning", "chat")
    graph.add_edge("chat",     END)
    return graph.compile()


async def run_chat_workflow(
    user_id:                 str,
    message:                 str,
    llm_client=None,
    use_reasoning:           bool = False,
    reasoning_budget_tokens: int  = 8000,
) -> dict:
    app = build_graph(llm_client, use_reasoning=use_reasoning)

    initial_state = {
        "user_id":                 user_id,
        "message":                 message,
        "thinking_summary":        "",
        "reasoning_budget_tokens": reasoning_budget_tokens,
        "node_results":            [],
        "output":                  {},
    }

    return await app.ainvoke(initial_state)


async def run_chat_workflow_stream(
    user_id:                 str,
    message:                 str,
    llm_client=None,
    use_reasoning:           bool = False,
    reasoning_budget_tokens: int  = 8000,
):
    state = {
        "user_id":                 user_id,
        "message":                 message,
        "thinking_summary":        "",
        "reasoning_budget_tokens": reasoning_budget_tokens,
        "node_results":            [],
        "output":                  {},
    }

    if use_reasoning:
        state = await ReasoningNode.run(state, llm_client)
        yield event("reasoning",
            goal       = state.get("goal", ""),
            intent     = state.get("intent", ""),
            complexity = state.get("complexity", ""),
            key_points = state.get("key_points", []),
        )

    state = await PlanningNode.run(state, llm_client)
    yield event("planning",
        steps = state.get("plan", []),
    )

    async for token in ChatNode.run_stream(state, llm_client):
        yield event("token",
            value = token,
        )