from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Literal
import json

from app.services.search_service import search_chunks
from app.services.rag_service import rag_answer, stream_answer

router = APIRouter()


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class SearchRequest(BaseModel):
    query: str
    limit: int = 5


class ChatRequest(BaseModel):
    query: str
    history: List[ChatMessage] = []


@router.post("/search")
def search(request: SearchRequest):
    results = search_chunks(request.query, request.limit)
    return {
        "query": request.query,
        "results": results
    }


@router.post("/chat")
def chat(request: ChatRequest):
    answer = rag_answer(
        query=request.query,
        history=[msg.model_dump() for msg in request.history]
    )
    return {
        "question": request.query,
        "answer": answer
    }


@router.post("/chat/stream")
def chat_stream(request: ChatRequest):
    def event_generator():
        for chunk in stream_answer(
            query=request.query,
            history=[msg.model_dump() for msg in request.history]
        ):
            yield f"data: {json.dumps(chunk)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )