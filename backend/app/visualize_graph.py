# backend/visualize_graph.py
from agents.graph import build_graph

if __name__ == "__main__":
    app = build_graph()

    # Terminal
    app.get_graph().print_ascii()

    # PNG
    with open("graph.png", "wb") as f:
        f.write(app.get_graph().draw_mermaid_png())
    print("graph.png saved.")