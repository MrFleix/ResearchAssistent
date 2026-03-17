# agents/graphs/ingest_graph.py
from langgraph.graph import StateGraph
from backend.app.agents.state import IngestState
from backend.app.agents.nodes.ingest.pdf_parser_node      import PDFParserNode
from backend.app.agents.nodes.ingest.entity_extractor_node import EntityExtractorNode
from backend.app.agents.nodes.ingest.embedder_node         import EmbedderNode
from backend.app.agents.nodes.ingest.storage_node          import StorageNode


def build_ingest_graph(
    llm_client,
    embedder,
    kw_model,
    db_session,
    neo4j_session,
):
    """
    Kompilierter LangGraph für den ingest_workflow.

    Pipeline:
      parse_pdf → extract_entities → embed → store

    LLM-Calls: 1 pro Paper (~$0.001)
      → EntityExtractorNode: gaps + innovations aus Abstract

    Kosten-Aufteilung:
      PDFParserNode      → $0   (pymupdf4llm, lokal)
      EntityExtractorNode→ $0   (KeyBERT, lokal) + ~$0.001 (LLM, Abstract only)
      EmbedderNode       → $0   (sentence-transformers, lokal)
      StorageNode        → $0   (PostgreSQL + Neo4j)
    """

    async def parse_pdf(state: IngestState) -> IngestState:
        return await PDFParserNode.run(state)

    async def extract_entities(state: IngestState) -> IngestState:
        return await EntityExtractorNode.run(state, llm_client, kw_model)

    async def embed(state: IngestState) -> IngestState:
        return await EmbedderNode.run(state, embedder)

    async def store(state: IngestState) -> IngestState:
        return await StorageNode.run(state, db_session, neo4j_session)

    graph = StateGraph(IngestState)

    graph.add_node("parse_pdf",         parse_pdf)
    graph.add_node("extract_entities",  extract_entities)
    graph.add_node("embed",             embed)
    graph.add_node("store",             store)

    graph.set_entry_point("parse_pdf")
    graph.add_edge("parse_pdf",         "extract_entities")
    graph.add_edge("extract_entities",  "embed")
    graph.add_edge("embed",             "store")
    graph.set_finish_point("store")

    return graph.compile()


async def run_ingest_workflow(
    user_id:       str,
    file_path:     str,
    llm_client,
    embedder,
    kw_model,
    db_session,
    neo4j_session,
) -> dict:
    """
    Führt den kompletten ingest_workflow aus.

    Input:
      user_id   → UUID des Users
      file_path → Pfad zur PDF-Datei

    Output (finaler State):
      paper_id     → UUID des gespeicherten Papers
      title        → extrahierter Titel
      abstract     → extrahierter Abstract
      sections     → {"abstract": "...", "methods": "...", ...}
      entities     → {
                       "concepts":    ["attention mechanism", ...],
                       "methods":     ["sparse attention", ...],
                       "techniques":  ["tiling strategy", ...],
                       "keywords":    ["transformer", ...],
                       "gaps":        ["quadratic complexity", ...],  ← LLM
                       "innovations": ["io-aware attention", ...]     ← LLM
                     }
      embeddings   → [[0.1, 0.3, ...], ...]  (384-dim, L2-normalisiert)
      entity_texts → ["attention mechanism", ...]  (parallel zu embeddings)
      entity_types → ["concepts", ...]             (parallel zu embeddings)
    """
    compiled = build_ingest_graph(
        llm_client, embedder, kw_model,
        db_session, neo4j_session
    )

    initial_state: IngestState = {
        # Input
        "user_id":      user_id,
        "file_path":    file_path,

        # PDFParserNode füllt diese
        "raw_text":     "",
        "abstract":     "",
        "sections":     {},
        "title":        "",

        # EntityExtractorNode füllt diese
        "entities":     {},

        # EmbedderNode füllt diese
        "embeddings":   [],
        "entity_texts": [],
        "entity_types": [],

        # StorageNode füllt diese
        "paper_id":     "",

        # Shared
        "node_results": [],
        "output":       {},
    }

    return await compiled.ainvoke(initial_state)
