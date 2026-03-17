"""
Wrapper für sentence-transformers.
Wird wie llm_client per closure in Nodes reingegeben.

- Embedder.__init__(): lädt "all-MiniLM-L6-v2" model
- Embedder.encode(texts: List[str]) → List[List[float]]

Wird in main.py initialisiert:
app.state.embedder = Embedder()
"""