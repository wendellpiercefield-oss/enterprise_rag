import requests
from app.core.config import get_settings

settings = get_settings()


def generate_embedding(text: str):

    response = requests.post(
        f"{settings.ollama_base_url}/api/embed",
        json={
            "model": settings.embed_model,
            "input": text
        }
    )

    response.raise_for_status()

    return response.json()["embeddings"][0]