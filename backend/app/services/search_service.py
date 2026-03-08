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
                    dc.content,
                    dc.document_id,
                    dc.chunk_index,
                    d.filename,
                    'vector' AS source,
                    1 - (dc.embedding <=> CAST(:embedding AS vector)) AS similarity
                FROM document_chunks dc
                JOIN documents d
                ON d.id = dc.document_id
                WHERE dc.embedding IS NOT NULL
                ORDER BY dc.embedding <=> CAST(:embedding AS vector)
                LIMIT :limit
            """),
            {
                "embedding": embedding,
                "limit": limit
            }
        ).fetchall()

        # -------------------------
        # Keyword search
        # -------------------------
        keyword_result = db.execute(
            text("""
                SELECT
                    dc.content,
                    dc.document_id,
                    dc.chunk_index,
                    d.filename,
                    'keyword' AS source
                FROM document_chunks dc
                JOIN documents d
                ON d.id = dc.document_id
                WHERE dc.content ILIKE :pattern
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
                "filename": r.filename,   # <-- ADD THIS
                "chunk_index": r.chunk_index,
                "similarity": float(getattr(r, "similarity", 0)),  # safe for keyword rows
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