from fastapi import APIRouter
from pydantic import BaseModel
from app.services.search_service import search_chunks

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

from app.services.rag_service import rag_answer


@router.post("/chat")
def chat(request: SearchRequest):

    answer = rag_answer(request.query)

    return {
        "question": request.query,
        "answer": answer
    }