# main.py
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.app.agents.graph import run_chat_workflow
from backend.app.models.async_local_llm import AsyncLocalLLM
from backend.app.models.llm_provider import LLMProvider
load_dotenv()


class ChatRequest(BaseModel):
    user_id: str
    message: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.llm = LLMProvider()  # ← kümmert sich selbst um mode
    app.state.apify_key = os.getenv("APIFY_KEY")
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/chat")
async def chat_endpoint(request: ChatRequest, req: Request):
    try:
        final_state = await run_chat_workflow(
            request.user_id,
            request.message,
            llm_client=req.app.state.llm,
        )
        return {
            "output": final_state["output"],
            "node_results": final_state["node_results"],
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")