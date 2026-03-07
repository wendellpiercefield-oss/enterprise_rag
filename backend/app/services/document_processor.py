from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models.document import Document

from app.services.text_extractor import extract_text
from app.services.chunker import chunk_text


def process_document(document_id: int):

    db: Session = SessionLocal()

    try:

        document = db.query(Document).filter(Document.id == document_id).first()

        if not document:
            print(f"Document {document_id} not found")
            return

        # update status
        document.status = "processing"
        db.commit()

        file_path = document.file_path

        print(f"Processing document {document.filename}")

        # extract text
        text = extract_text(file_path)

        if not text:
            raise ValueError("No text extracted")

        # split into chunks
        chunks = chunk_text(text)

        print(f"Created {len(chunks)} chunks")

        # TODO: store chunks in database
        # TODO: generate embeddings

        document.status = "indexed"
        db.commit()

    except Exception as e:

        print(f"Document processing failed: {e}")

        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            document.status = "failed"
            db.commit()

    finally:
        db.close()