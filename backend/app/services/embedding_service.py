import requests

from app.core.config import get_settings

settings = get_settings()

OLLAMA_URL = f"{settings.ollama_base_url}/api/embed"
MODEL = settings.embed_model


def generate_embeddings(texts):

    print("Sending embedding request...")

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "input": texts
        },
        timeout=60
    )

    print("Received embedding response")

    response.raise_for_status()

    data = response.json()

    if "embeddings" in data:
        return data["embeddings"]

    if "embedding" in data:
        return [data["embedding"]]

    raise RuntimeError(f"Unexpected Ollama response: {data}")