import requests
from app.core.config import get_settings

settings = get_settings()


def generate_embeddings(texts):

    response = requests.post(
        f"{settings.ollama_base_url}/api/embed",
        json={
            "model": settings.embed_model,
            "input": texts
        }
    )

    response.raise_for_status()

    data = response.json()

    # Ollama batch embeddings endpoint
    if "embeddings" in data:
        return data["embeddings"]

    # fallback if API returns single embedding
    if "embedding" in data:
        return [data["embedding"]]

    raise RuntimeError(f"Unexpected Ollama response: {data}")