import json
import requests
from app.services.search_service import search_chunks

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "gpt-oss:20b"
GOOD_THRESHOLD = 0.50


def build_rag_prompt(query: str, context: str) -> str:
    return f"""
You are a hydraulic motor product specialist.

Use ONLY the provided catalog text to answer the question.

If the answer is not explicitly supported by the context, say:
"I could not find that in the provided manuals."

Context:
{context}

Question:
{query}

Answer clearly and concisely.
"""


def build_general_prompt(query: str) -> str:
    return query


def decide_context(query: str):
    results = search_chunks(query, 15)
    good_results = [r for r in results if r.get("similarity", 0) >= GOOD_THRESHOLD]

    if not good_results:
        return {
            "mode": "general",
            "prompt": build_general_prompt(query),
            "sources": []
        }

    context = "\n\n--- DOCUMENT CHUNK ---\n\n".join(r["content"] for r in good_results)

    return {
        "mode": "rag",
        "prompt": build_rag_prompt(query, context),
        "sources": good_results
    }


def rag_answer(query: str):
    decision = decide_context(query)

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": decision["prompt"],
            "stream": False
        },
        timeout=120
    )
    response.raise_for_status()

    data = response.json()

    return {
        "answer": data["response"],
        "sources": decision["sources"],
        "mode": decision["mode"]
    }


def stream_answer(query: str):
    decision = decide_context(query)

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": decision["prompt"],
            "stream": True
        },
        stream=True,
        timeout=120
    )
    response.raise_for_status()

    for line in response.iter_lines():
        if not line:
            continue

        obj = json.loads(line.decode("utf-8"))
        token = obj.get("response", "")
        done = obj.get("done", False)

        yield {
            "token": token,
            "done": done,
            "sources": decision["sources"] if done else [],
            "mode": decision["mode"] if done else None
        }