import requests

OLLAMA_URL = "http://localhost:11434/api/embed"
MODEL = "nomic-embed-text"


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