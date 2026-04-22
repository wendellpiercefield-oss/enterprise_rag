from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json

from app.services.search_service import search_chunks
from app.services.rag_service import rag_answer, stream_answer

router = APIRouter()


class SearchRequest(BaseModel):
    query: str
    limit: int = 5


@router.post("/search")
def search(request: SearchRequest):
    results = search_chunks(request.query, request.limit)
    return {
        "query": request.query,
        "results": results
    }


@router.post("/chat")
def chat(request: SearchRequest):
    answer = rag_answer(request.query)
    return {
        "question": request.query,
        "answer": answer
    }


@router.post("/chat/stream")
def chat_stream(request: SearchRequest):
    def event_generator():
        for chunk in stream_answer(request.query):
            yield f"data: {json.dumps(chunk)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )