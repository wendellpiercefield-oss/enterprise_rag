from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models.document import Document
from app.services.text_extractor import extract_text
from app.services.chunker import chunk_text
from app.services.embedding_service import generate_embedding

from sqlalchemy import text


def process_document(document_id: int):

    db: Session = SessionLocal()

    document = db.query(Document).filter(Document.id == document_id).first()

    if not document:
        print("Document not found")
        return

    file_path = document.file_path

    print(f"Processing document {document_id}")

    # Extract text
    text_content = extract_text(file_path)

    # Chunk text
    chunks = chunk_text(text_content)

    print(f"Created {len(chunks)} chunks")

    for idx, chunk in enumerate(chunks):

        embedding = generate_embedding(chunk)

        db.execute(
            text("""
                INSERT INTO document_chunks
                (
                    tenant_id,
                    collection_id,
                    document_id,
                    chunk_index,
                    content,
                    embedding
                )
                VALUES
                (
                    :tenant_id,
                    :collection_id,
                    :document_id,
                    :chunk_index,
                    :content,
                    :embedding
                )
            """),
            {
                "tenant_id": document.tenant_id,
                "collection_id": document.collection_id,
                "document_id": document.id,
                "chunk_index": idx,
                "content": chunk,
                "embedding": embedding
            }
        )

    document.status = "indexed"

    db.commit()

    print("Chunks saved")

    db.close()