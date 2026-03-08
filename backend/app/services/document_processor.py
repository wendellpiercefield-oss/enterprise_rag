from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.session import SessionLocal
from app.db.models.document import Document

from app.services.text_extractor import extract_text
from app.services.chunker import chunk_text
from app.services.embedding_service import generate_embeddings


MAX_CHARS = 2800
MIN_CHARS = 40
BATCH_SIZE = 12


def clean_chunks(chunks):

    cleaned = []

    for c in chunks:

        if not c:
            continue

        c = c.strip()

        if len(c) < MIN_CHARS:
            continue

        c = " ".join(c.split())

        if len(c) > MAX_CHARS:
            c = c[:MAX_CHARS]

        cleaned.append(c)

    return cleaned


def process_document(document_id: int):

    db: Session = SessionLocal()

    try:

        document = db.query(Document).filter(Document.id == document_id).first()

        if not document:
            print("Document not found")
            return

        file_path = document.file_path

        print(f"Processing document {document_id}")

        # -----------------------------
        # CLEAN OLD CHUNKS (safe reindex)
        # -----------------------------
        db.execute(
            text("DELETE FROM document_chunks WHERE document_id = :doc_id"),
            {"doc_id": document_id}
        )

        # -----------------------------
        # Extract text
        # -----------------------------

        text_content = extract_text(file_path)

        # -----------------------------
        # Chunk text
        # -----------------------------

        chunks = chunk_text(text_content)
        print(f"Created {len(chunks)} raw chunks")

        chunks = clean_chunks(chunks)
        print(f"{len(chunks)} usable chunks after cleaning")

        if not chunks:
            print("No usable chunks created")
            return

        # -----------------------------
        # Generate embeddings (BATCH)
        # -----------------------------

        embeddings = []

        for i in range(0, len(chunks), BATCH_SIZE):

            batch = chunks[i:i + BATCH_SIZE]

            print(f"Embedding batch {i+1}-{i+len(batch)} of {len(chunks)}")

            try:

                batch_embeddings = generate_embeddings(batch)

                if not batch_embeddings:
                    print("Batch embedding failed — skipping batch")
                    embeddings.extend([None] * len(batch))
                    continue

                embeddings.extend(batch_embeddings)

            except Exception as batch_error:

                print(f"Batch failed: {batch_error}")

                embeddings.extend([None] * len(batch))

        # -----------------------------
        # Store chunks
        # -----------------------------

        for idx, chunk in enumerate(chunks):

            embedding = embeddings[idx]

            if not embedding:
                print(f"Skipping chunk {idx} due to missing embedding")
                continue

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

    except Exception as e:

        print("Document processing failed:", e)
        db.rollback()

    finally:

        db.close()