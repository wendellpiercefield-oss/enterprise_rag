Knowledge Platform



A multi-tenant AI knowledge platform built with FastAPI, PostgreSQL, pgvector, and Ollama.



The system allows users to:



Upload documents



Automatically extract and chunk text



Generate embeddings



Perform semantic search and AI chat over internal knowledge



Architecture

FastAPI

&nbsp;  │

&nbsp;  ▼

Authentication / Tenants

&nbsp;  │

&nbsp;  ▼

Collections

&nbsp;  │

&nbsp;  ▼

Document Upload

&nbsp;  │

&nbsp;  ▼

File Storage (local)

&nbsp;  │

&nbsp;  ▼

Background Processing

&nbsp;  │

&nbsp;  ▼

Text Extraction

&nbsp;  │

&nbsp;  ▼

Chunking

&nbsp;  │

&nbsp;  ▼

Embeddings (Ollama)

&nbsp;  │

&nbsp;  ▼

pgvector Storage

Technology Stack



Backend:



FastAPI

SQLAlchemy

PostgreSQL

pgvector

Pydantic



AI / ML:



Ollama

nomic-embed-text

Llama3



Document Processing:



pypdf

python-docx



Infrastructure:



Docker

PostgreSQL container

Project Structure

backend/

&nbsp;├─ app/

&nbsp;│   ├─ api/

&nbsp;│   │   ├─ auth.py

&nbsp;│   │   ├─ collections.py

&nbsp;│   │   └─ documents.py

&nbsp;│   │

&nbsp;│   ├─ core/

&nbsp;│   │   └─ config.py

&nbsp;│   │

&nbsp;│   ├─ db/

&nbsp;│   │   ├─ models/

&nbsp;│   │   └─ session.py

&nbsp;│   │

&nbsp;│   └─ services/

&nbsp;│       ├─ document\_processor.py

&nbsp;│       ├─ text\_extractor.py

&nbsp;│       └─ chunker.py

&nbsp;│

&nbsp;└─ data/

&nbsp;    └─ files/

Running the System



Start PostgreSQL container:



docker start kp-postgres



Activate Python environment:



cd backend

.\\.venv\\Scripts\\activate



Run the API:



python -m uvicorn app.main:app --port 8000



Open Swagger:



http://localhost:8000/docs

Document Processing Workflow

Upload document

&nbsp;       │

&nbsp;       ▼

File stored on disk

&nbsp;       │

&nbsp;       ▼

Document record saved

&nbsp;       │

&nbsp;       ▼

Background processing task

&nbsp;       │

&nbsp;       ▼

Extract text

&nbsp;       │

&nbsp;       ▼

Chunk text

&nbsp;       │

&nbsp;       ▼

Generate embeddings

&nbsp;       │

&nbsp;       ▼

Store vectors in pgvector

Current Status



Working:



Authentication

Tenants

Collections

Document upload

File storage

Background processing

Text extraction

Chunking

pgvector enabled



Next:



Embedding generation

Vector search

AI chat interface

