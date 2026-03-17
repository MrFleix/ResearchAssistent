# main.py
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.app.agents.graph import run_chat_workflow, run_chat_workflow_stream
from backend.app.models.llm_provider import LLMProvider

load_dotenv()

# ── Pydantic Modell ─────────────────────────────
class ChatRequest(BaseModel):
    user_id: str
    message: str
    use_reasoning: bool = False
    reasoning_budget_tokens: int = 8000

# ── FastAPI Lifespan ────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.llm = LLMProvider()
    yield

# ── FastAPI App ────────────────────────────────
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── /chat Endpoint (normale JSON Ausgabe) ─────
@app.post("/chat")
async def chat_endpoint(request: ChatRequest, req: Request):
    try:
        final_state = await run_chat_workflow(
            user_id=request.user_id,
            message=request.message,
            llm_client=req.app.state.llm.llm,
            use_reasoning=request.use_reasoning,
            reasoning_budget_tokens=request.reasoning_budget_tokens,
        )
        return {
            "output": final_state["output"],
            "node_results": final_state["node_results"],
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

# ── Externer Streaming Generator ──────────────
async def chat_stream_generator(user_id: str, message: str, llm_client, use_reasoning: bool, reasoning_budget_tokens: int):
    async for token in run_chat_workflow_stream(
        user_id=user_id,
        message=message,
        llm_client=llm_client,
        use_reasoning=use_reasoning,
        reasoning_budget_tokens=reasoning_budget_tokens
    ):
        yield token

@app.post("/chat/stream")
async def chat_stream_endpoint(request: ChatRequest, req: Request):
    return StreamingResponse(
        chat_stream_generator(
            user_id=request.user_id,
            message=request.message,
            llm_client=req.app.state.llm.llm,
            use_reasoning=request.use_reasoning,
            reasoning_budget_tokens=request.reasoning_budget_tokens
        ),
        media_type="application/x-ndjson"  # ← war text/plain
    )