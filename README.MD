# Knowledge Platform

A multi-tenant AI knowledge platform built with **FastAPI, PostgreSQL, pgvector, and Ollama**.

The system allows users to:

- Upload documents
- Automatically extract and chunk text
- Generate embeddings
- Perform semantic search and AI chat over internal knowledge

---

# Architecture

FastAPI  
  │  
  ▼  
Authentication / Tenants  
  │  
  ▼  
Collections  
  │  
  ▼  
Document Upload  
  │  
  ▼  
File Storage (local)  
  │  
  ▼  
Background Processing  
  │  
  ▼  
Text Extraction  
  │  
  ▼  
Chunking  
  │  
  ▼  
Embeddings (Ollama)  
  │  
  ▼  
pgvector Storage  

---

# Technology Stack

## Backend

- FastAPI  
- SQLAlchemy  
- PostgreSQL  
- pgvector  
- Pydantic  

## AI / ML

- Ollama  
- nomic-embed-text  
- Llama3  

## Document Processing

- pypdf  
- python-docx  

## Infrastructure

- Docker  
- PostgreSQL container  

---

# Project Structure
backend/
├─ app/
│ ├─ api/
│ │ ├─ auth.py
│ │ ├─ collections.py
│ │ └─ documents.py
│ │
│ ├─ core/
│ │ └─ config.py
│ │
│ ├─ db/
│ │ ├─ models/
│ │ └─ session.py
│ │
│ └─ services/
│ ├─ document_processor.py
│ ├─ text_extractor.py
│ └─ chunker.py
│
└─ data/
└─ files/


---

# Running the System

### Start PostgreSQL container


docker start kp-postgres


### Activate Python environment


cd backend
..venv\Scripts\activate


### Run the API


python -m uvicorn app.main:app --port 8000


### Open Swagger


http://localhost:8000/docs


---

# Document Processing Workflow

Upload document  
       │  
       ▼  
File stored on disk  
       │  
       ▼  
Document record saved  
       │  
       ▼  
Background processing task  
       │  
       ▼  
Extract text  
       │  
       ▼  
Chunk text  
       │  
       ▼  
Generate embeddings  
       │  
       ▼  
Store vectors in pgvector  

---

# Current Status

## Working

- Authentication
- Tenants
- Collections
- Document upload
- File storage
- Background processing
- Text extraction
- Chunking
- pgvector enabled

## Next

- Embedding generation
- Vector search
- AI chat interface
