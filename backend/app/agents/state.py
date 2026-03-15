# agents/state.py
# ── ERWEITERUNG: IngestState ───────────────────────────────────
# Füge diese Felder zu deiner bestehenden IngestState hinzu.
# Die anderen States (WorkflowState etc.) bleiben unverändert.
 
from typing import TypedDict, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime, timezone
 
 
class BaseNodeOutput(BaseModel):
    node:      str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata:  Dict[str, Any] = {}
 
 
class BaseWorkflowState(TypedDict):
    user_id:      str
    node_results: List[Dict[str, Any]]
    output:       Dict[str, Any]
 
 
class WorkflowState(BaseWorkflowState):
    message: str
 
 
class IngestState(BaseWorkflowState):
    # ── Input ──────────────────────────────────────────────────
    file_path:    str
 
    # ── PDFParserNode ──────────────────────────────────────────
    raw_text:     str
    abstract:     str
    title:        str                    # NEU
    sections:     Dict[str, str]         # NEU: {"abstract": "...", "methods": "..."}
 
    # ── EntityExtractorNode ────────────────────────────────────
    entities:     Dict[str, List[str]]   # {concepts, methods, techniques, keywords, gaps, innovations}
 
    # ── EmbedderNode ───────────────────────────────────────────
    embeddings:   List[List[float]]
    entity_texts: List[str]              # NEU: parallel zu embeddings
    entity_types: List[str]              # NEU: parallel zu embeddings
 
    # ── StorageNode ────────────────────────────────────────────
    paper_id:     str