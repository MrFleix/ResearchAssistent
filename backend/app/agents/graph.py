# agents/graph.py
from langgraph.graph import StateGraph, END
from backend.app.agents.nodes.chat_node import ChatNode
from backend.app.agents.state import WorkflowState

def build_graph(llm_client=None):
    graph = StateGraph(WorkflowState)

    # llm_client per closure mitgeben
    async def chat(state):
        return await ChatNode.run(state, llm_client)

    graph.add_node("chat", chat)

    # Später erweiterbar:
    # graph.add_node("rag", RAGNode.run)
    # graph.add_edge("chat", "rag")

    graph.set_entry_point("chat")
    graph.add_edge("chat", END)

    return graph.compile()


async def run_chat_workflow(user_id: str, message: str, llm_client=None) -> dict:
    app = build_graph(llm_client)

    initial_state = {
        "user_id": user_id,
        "message": message,
        "node_results": [],
        "output": {},
    }

    final_state = await app.ainvoke(initial_state)
    return final_state