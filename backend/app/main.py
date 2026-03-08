# main.py
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agents.graph import run_chat_workflow
from models.async_local_llm import AsyncLocalLLM

load_dotenv()


class ChatRequest(BaseModel):
    user_id: str
    message: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.llm = AsyncLocalLLM(model_name=os.getenv("LLM_MODEL", "Qwen/Qwen3-0.6B"))
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