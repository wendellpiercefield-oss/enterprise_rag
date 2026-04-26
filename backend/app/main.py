from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import text
from pathlib import Path

from app.db.session import engine
from app.api.tenant import router as tenant_router
from app.api.auth import router as auth_router
from app.api.collection import router as collection_router
from app.api.documents import router as documents_router
from app.api.search import router as search_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Knowledge Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tenant_router)
app.include_router(auth_router)
app.include_router(collection_router)
app.include_router(documents_router)
app.include_router(search_router)

BASE_DIR = Path(__file__).resolve().parents[2]
frontend_path = BASE_DIR / "UI"

app.mount("/static", StaticFiles(directory=frontend_path), name="static")

@app.get("/")
def serve_index():
    return FileResponse(frontend_path / "index.html")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/health/db")
def health_db():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        return {"db": result.scalar()}

for route in app.routes:
    print("ROUTE:", route.path, getattr(route, "methods", "MOUNT"))