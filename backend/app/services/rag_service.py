import requests
from app.services.search_service import search_chunks

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "gpt-oss:20b"


def rag_answer(query: str):

    results = search_chunks(query, 12)

    context = "\n\n--- DOCUMENT CHUNK ---\n\n".join(r["content"] for r in results)

    prompt = f"""
You are a hydraulic motor product specialist.

Use ONLY the provided catalog text to answer the question.

Important rules:
- Extract numeric specifications when present
- Engineering manuals often contain tables with torque values
- If a chunk references bolts or torque, extract the numeric value
- If the torque appears as "105 +/-5 lb-ft", report it exactly

Context:
{context}

Question:
{query}

Answer clearly and concisely.
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