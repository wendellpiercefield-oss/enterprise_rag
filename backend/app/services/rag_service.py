import requests
from app.services.search_service import search_chunks

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "gpt-oss:20b"


def rag_answer(query: str):

    results = search_chunks(query, 12)

    context = "\n\n--- DOCUMENT CHUNK ---\n\n".join(r["content"] for r in results)

    prompt = f"""
You are a hydraulic motor service specialist.

Answer the question using ONLY the provided service manual text.

If the manual contains a procedure, list the steps clearly.

Do not invent steps that are not present.

If the answer cannot be determined from the text, say so.

Context:
{context}

Question:
{query}

Answer:
"""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False
        }
    )

    return {
        "answer": response.json()["response"],
        "sources": results
    }