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