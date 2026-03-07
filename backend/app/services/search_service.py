from sqlalchemy import text
from app.db.session import SessionLocal
from app.services.embedding_service import generate_embeddings


def search_chunks(query: str, limit: int = 5):

    db = SessionLocal()

    try:

        embedding = generate_embeddings([query])[0]

        # convert python list -> pgvector format
        embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"

        result = db.execute(
            text("""
                SELECT
                    content,
                    document_id,
                    chunk_index,
                    1 - (embedding <=> CAST(:embedding AS vector)) AS similarity
                FROM document_chunks
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> CAST(:embedding AS vector)
                LIMIT :limit
            """),
            {
                "embedding": embedding_str,
                "limit": limit
            }
        )

        rows = result.fetchall()

        return [
            {
                "content": r.content,
                "document_id": r.document_id,
                "chunk_index": r.chunk_index,
                "similarity": float(r.similarity)
            }
            for r in rows
        ]

    finally:
        db.close()