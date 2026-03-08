# agents/state.py
from pydantic import BaseModel, Field
from typing import TypedDict, Dict, Any, List
from datetime import datetime, timezone


class BaseNodeOutput(BaseModel):
    node: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = {}


class WorkflowState(TypedDict):
    user_id: str
    message: str
    node_results: List[Dict[str, Any]]  # ← dicts, weil model_dump() rausgibt
    output: Dict[str, Any]