from fastapi import FastAPI
from sqlalchemy import text
from app.db.session import engine
from app.api.tenant import router as tenant_router
from app.api.auth import router as auth_router
from app.api.collection import router as collection_router
from app.api.documents import router as documents_router

app = FastAPI(title="Knowledge Platform")

app.include_router(tenant_router)
app.include_router(auth_router)
app.include_router(collection_router)
app.include_router(documents_router)

for route in app.routes:
    print("ROUTE:", route.path, route.methods)

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/db")
def health_db():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        return {"db": result.scalar()}