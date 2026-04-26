import json
import re
import requests
from app.services.search_service import search_chunks
from app.core.config import get_settings

settings = get_settings()

OLLAMA_URL = f"{settings.ollama_base_url}/api/generate"
MODEL = settings.chat_model
#GOOD_THRESHOLD = 0.40
#SPEC_THRESHOLD = 0.42

def should_use_rag(query: str) -> bool:
    q = query.lower().strip()

    manual_terms = [
        "motor", "ce", "dr", "dt", "hb", "hp", "lag", "omew",
        "seal", "kit", "torque", "pre-torque", "final torque",
        "shaft", "bearing", "bolt", "install", "remove",
        "repair", "procedure", "manual", "spec", "part number",
        "o-ring", "square cut"
    ]

    smalltalk = [
        "hi", "hello", "hey", "how are you", "what's up",
        "thanks", "thank you", "who are you"
    ]

    if any(q.startswith(s) for s in smalltalk):
        return False

    return any(term in q for term in manual_terms)

def is_spec_query(query: str) -> bool:
    q = query.upper()
    spec_words = [
        "TORQUE", "PRE-TORQUE", "FINAL TORQUE", "BOLT", "BOLTS",
        "DATE", "DIMENSION", "PART NUMBER", "SPEC", "VALUE"
    ]
    return any(word in q for word in spec_words)


def format_history(history):
    if not history:
        return ""

    lines = []
    for msg in history[-6:]:
        role = "User" if msg.get("role") == "user" else "Assistant"
        content = msg.get("content", "").strip()
        if content:
            lines.append(f"{role}: {content}")

    return "\n".join(lines)


def build_rag_prompt(query: str, context: str, history_text: str, spec_query: bool) -> str:
    if spec_query:
        extra_rules = """
7. If the question asks for torque, date, bolt count, dimensions, part numbers, or any numeric specification:
   - answer ONLY if the exact value or directly equivalent wording is explicitly present in the context.
   - for date/change questions, phrases like "manufactured after [date]" or "prior to this date" are valid evidence of the effective change date.
   - in those cases, extract and return the date clearly.
   - do NOT provide approximate values, typical values, guessed values, or values from similar models.
   - if the exact value or directly equivalent wording is not visible in the context, reply exactly:
     "I could not find that in the provided manuals."
"""
    else:
        extra_rules = """
7. If the question asks for a procedure, installation, removal, repair, or how to perform a task:
   - you MAY combine steps from multiple parts of the provided context.
   - organize the answer into a clear step-by-step process.
   - synthesis is allowed, but ONLY from the provided context.
   - do NOT add steps that are not supported by the context.
   - if the procedure is not supported by the context, reply exactly:
     "I could not find that in the provided manuals."
"""

    return f"""
Your name is Jeff and you are a hydraulic motor product specialist.

You MUST follow these rules:

1. Only answer using the provided context.
2. Do not invent unsupported information.
3. Do not substitute values from similar models.
4. Prefer being incomplete over being wrong.
5. If the question asks for multiple values and only some are present, state only what is present and clearly state the rest is not found.
{extra_rules}

Conversation history:
{history_text}

Context:
{context}

Question:
{query}

Answer clearly and concisely.
"""

def decide_context(query: str, history=None):
    history = history or []
    history_text = format_history(history)
    spec_query = is_spec_query(query)

    # ROUTER: decide if we should use RAG or not
    if not should_use_rag(query):
        return {
            "mode": "general",
            "prompt": query,
            "sources": []
        }

    try:
        results = search_chunks(query, 25)
    except Exception as e:
        print(f"search_chunks failed: {e}")
        results = []

    # If nothing found at all
    if not results:
        return {
            "mode": "no_context",
            "prompt": "",
            "sources": []
        }

    # -----------------------------
    # CORE FIX: DO NOT FILTER
    # -----------------------------
    good_results = results[:8]

    # Spec queries = tighter context
    if spec_query:
        good_results = results[:5]

    # Procedure queries = more context
    q_lower = query.lower()
    if any(word in q_lower for word in ["how", "install", "procedure", "repair"]):
        good_results = results[:10]

    # Optional: remove near duplicates
    seen = set()
    unique = []

    for r in good_results:
        key = r["content"][:120]
        if key not in seen:
            seen.add(key)
            unique.append(r)

    good_results = unique

    context = "\n\n--- DOCUMENT CHUNK ---\n\n".join(r["content"] for r in good_results)

    print("\n=== CONTEXT USED ===")
    print(context[:2000])
    print("=== END CONTEXT ===\n")

    return {
        "mode": "rag",
        "prompt": build_rag_prompt(query, context, history_text, spec_query),
        "sources": good_results
    }


def rag_answer(query: str, history=None):
    decision = decide_context(query, history or [])

    if decision["mode"] == "general":
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": decision["prompt"],
                "stream": False,
                "options": {"temperature": 0.3}
            },
            timeout=120
        )
        response.raise_for_status()

        data = response.json()

        return {
            "answer": data["response"],
            "sources": [],
            "mode": "general"
        }

    if decision["mode"] == "no_context":
        return {
            "answer": "I could not find that in the provided manuals.",
            "sources": [],
            "mode": "no_context"
        }

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": decision["prompt"],
            "stream": False,
            "options": {
                "temperature": 0
            }
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


def stream_answer(query: str, history=None):
    decision = decide_context(query, history or [])

    if decision["mode"] == "general":
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": decision["prompt"],
                "stream": True,
                "options": {"temperature": 0.3}
            },
            stream=True,
            timeout=120
        )
        response.raise_for_status()

        for line in response.iter_lines():
            if not line:
                continue

            obj = json.loads(line.decode("utf-8"))

            yield {
                "token": obj.get("response", ""),
                "done": obj.get("done", False),
                "sources": [],
                "mode": "general"
            }

        return


    if decision["mode"] == "no_context":
        yield {
            "token": "I could not find that in the provided manuals.",
            "done": True,
            "sources": [],
            "mode": "no_context"
        }
        return

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": decision["prompt"],
            "stream": True,
            "options": {
                "temperature": 0
            }
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