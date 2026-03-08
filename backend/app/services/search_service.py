from sqlalchemy import text
from app.db.session import SessionLocal
from app.services.embedding_service import generate_embeddings


def search_chunks(query: str, limit: int = 5):

    db = SessionLocal()

    try:
        embedding = generate_embeddings([query])[0]
        embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"

        # -------------------------
        # Vector search
        # -------------------------
        vector_result = db.execute(
            text("""
                SELECT
                    content,
                    document_id,
                    chunk_index,
                    1 - (embedding <=> CAST(:embedding AS vector)) AS similarity,
                    'vector' AS source
                FROM document_chunks
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> CAST(:embedding AS vector)
                LIMIT :limit
            """),
            {
                "embedding": embedding_str,
                "limit": limit
            }
        ).fetchall()

        # -------------------------
        # Keyword search
        # -------------------------
        keyword_result = db.execute(
            text("""
                SELECT
                    content,
                    document_id,
                    chunk_index,
                    0.75 AS similarity,
                    'keyword' AS source
                FROM document_chunks
                WHERE content ILIKE :pattern
                LIMIT :limit
            """),
            {
                "pattern": f"%{query}%",
                "limit": limit
            }
        ).fetchall()

        # -------------------------
        # Merge + dedupe
        # -------------------------
        merged = {}
        for r in list(vector_result) + list(keyword_result):
            key = (r.document_id, r.chunk_index)

            row_data = {
                "content": r.content,
                "document_id": r.document_id,
                "chunk_index": r.chunk_index,
                "similarity": float(r.similarity),
                "source": r.source
            }

            if key not in merged or row_data["similarity"] > merged[key]["similarity"]:
                merged[key] = row_data

        # sort best first
        results = sorted(
            merged.values(),
            key=lambda x: x["similarity"],
            reverse=True
        )

        return results[:limit]

    finally:
        db.close()