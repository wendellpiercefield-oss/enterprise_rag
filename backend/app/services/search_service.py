import re
from sqlalchemy import text
from app.db.session import SessionLocal
from app.services.embedding_service import generate_embeddings


SPEC_WORDS = [
    "TORQUE", "PRE-TORQUE", "FINAL TORQUE", "BOLT", "BOLTS",
    "DATE", "DIMENSION", "PART NUMBER", "SPEC", "VALUE",
    "O-RING", "SQUARE CUT", "SEAL"
]

PROCEDURE_WORDS = [
    "REMOVE", "INSTALL", "TIGHTEN", "PRESS", "PLACE",
    "COAT", "CLEAN", "DRY", "LOOSEN", "DISCARD",
    "REASSEMBLE", "ASSEMBLE"
]

JUNK_TERMS = [
    "ALL RIGHTS RESERVED",
    "WHITE CAN ACCEPT NO RESPONSIBILITY",
    "CONTENTS",
    "EXPLODED VIEW",
    "TRADEMARKS",
]


def normalize_query(query: str) -> str:
    q = query.upper()
    q = re.sub(r"\b([A-Z]{1,4})[-\s]?(\d{3,4})\b", r"\1-\2", q)
    return q


def expand_query(query: str) -> str:
    q = normalize_query(query)

    if "PRE-TORQUE" in q or "TORQUE" in q:
        q += " PRE-TORQUE FINAL TORQUE TORQUE VALUE NM FT-LB BOLTS"

    if "DATE" in q or "CHANGE" in q or "CHANGED" in q:
        q += " NOTE DATE CHANGED MANUFACTURED AFTER PRIOR TO O-RING SQUARE CUT"

    if any(w in q for w in ["INSTALL", "SEAL", "KIT", "PROCEDURE", "HOW"]):
        q += " REMOVE INSTALL STEPS PROCEDURE SHAFT BEARING SEAL MOTOR"

    if any(w in q for w in ["DATE", "CHANGE", "CHANGED", "WHEN"]):
        q += (
            " EFFECTIVE DATE TRANSITION CHANGE EVENT "
            "PRIOR TO AFTER BEFORE "
            "MANUFACTURED AFTER MANUFACTURED PRIOR "
            "REPLACED BY SUPERSEDED CONVERTED UPDATED REVISION "
            "FROM TO BEFORE AFTER DIFFERENCE OLD NEW"
        )

    return q


def extract_model_terms(query: str):
    q = normalize_query(query)
    return re.findall(r"\b[A-Z]{1,4}-\d{3,4}\b", q)


def is_spec_query(query: str) -> bool:
    q = normalize_query(query)
    return any(w in q for w in SPEC_WORDS)


def is_procedure_query(query: str) -> bool:
    q = normalize_query(query)
    return any(w in q for w in ["HOW", "INSTALL", "REMOVE", "PROCEDURE", "REPAIR", "SEAL KIT"])


def score_chunk(query: str, filename: str, content: str, base_score: float) -> float:
    score = base_score

    normalized_query = normalize_query(query)
    model_terms = extract_model_terms(query)
    spec_query = is_spec_query(query)
    procedure_query = is_procedure_query(query)

    filename_u = (filename or "").upper()
    content_u = (content or "").upper()

    haystack = f"{filename_u} {content_u}"
    haystack_norm = haystack.replace(" ", "").replace("_", "").replace("/", "-")

    # -------------------------
    # Model / filename match
    # -------------------------
    for term in model_terms:
        term_norm = term.replace("-", "")

        if term in haystack or term_norm in haystack_norm:
            score += 0.30

        if term in filename_u or term_norm in filename_u.replace("-", ""):
            score += 0.40

    # -------------------------
    # Important note/date/spec signals
    # -------------------------
    if "NOTE:" in content_u or content_u.strip().startswith("NOTE"):
        score += 0.35

    if re.search(r"\b\d{4}\b", content_u):
        score += 0.20

    if any(x in content_u for x in ["O-RING", "SQUARE CUT", "MANUFACTURED AFTER", "PRIOR TO THIS DATE"]):
        score += 0.25

    # -------------------------
    # Spec query boosting
    # -------------------------
    if spec_query:
        spec_hits = sum(1 for w in SPEC_WORDS if w in content_u)
        score += min(spec_hits * 0.07, 0.35)

        if re.search(r"\b\d+(?:[.,]\d+)?\s*(NM|FT|FT\.|MM|PSI|RPM|IN|LB|LBS)\b", content_u):
            score += 0.25

        if any(x in content_u for x in ["PRE-TORQUE", "FINAL TORQUE", "TORQUE"]):
            score += 0.30

    # -------------------------
    # Procedure query boosting
    # -------------------------
    procedure_hits = sum(1 for w in PROCEDURE_WORDS if w in content_u)

    if procedure_query:
        if procedure_hits >= 4:
            score += 0.20
        elif procedure_hits >= 2:
            score += 0.10
    else:
        # Do not let procedure chunks dominate non-procedure questions
        if procedure_hits >= 4:
            score += 0.05

    # Small, not overpowering length boost
    if len(content_u) > 400:
        score += 0.04

    # -------------------------
    # Junk penalties
    # -------------------------
    junk_hits = sum(1 for t in JUNK_TERMS if t in content_u)

    if junk_hits >= 2:
        score -= 0.35
    elif junk_hits == 1:
        score -= 0.15

    # Penalize parts-table style chunks
    if ("ITEM NUMBER" in content_u and "DESCRIPTION" in content_u) or "ORDER NUMBER" in content_u:
        score -= 0.25

    if "TABLE " in content_u and not spec_query:
        score -= 0.10

    return score


def search_chunks(query: str, limit: int = 5):
    db = SessionLocal()

    try:
        normalized_query = normalize_query(query)
        expanded_query = expand_query(query)
        model_terms = extract_model_terms(query)

        embedding = generate_embeddings([expanded_query])[0]

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
                "limit": limit * 8
            }
        ).fetchall()

        # Prefer matching model-family docs when user asks for a model.
        if model_terms:
            filtered = []
            for r in vector_result:
                filename_u = (r.filename or "").upper()
                filename_norm = filename_u.replace(" ", "").replace("_", "").replace("/", "-")

                if any(term in filename_u or term.replace("-", "") in filename_norm.replace("-", "") for term in model_terms):
                    filtered.append(r)

            if filtered:
                vector_result = filtered

        keyword_result = db.execute(
            text("""
                SELECT
                    dc.content,
                    dc.document_id,
                    dc.chunk_index,
                    d.filename,
                    'keyword' AS source,
                    0.0 AS similarity
                FROM document_chunks dc
                JOIN documents d
                    ON d.id = dc.document_id
                WHERE dc.content ILIKE :pattern
                   OR d.filename ILIKE :pattern
                LIMIT :limit
            """),
            {
                "pattern": f"%{normalized_query}%",
                "limit": limit * 8
            }
        ).fetchall()

        merged = {}

        for r in list(vector_result) + list(keyword_result):
            key = (r.document_id, r.chunk_index)

            rescored = score_chunk(
                query=query,
                filename=r.filename,
                content=r.content,
                base_score=float(getattr(r, "similarity", 0))
            )

            row_data = {
                "content": r.content,
                "document_id": r.document_id,
                "filename": r.filename,
                "chunk_index": r.chunk_index,
                "similarity": rescored,
                "source": r.source
            }

            if key not in merged or row_data["similarity"] > merged[key]["similarity"]:
                merged[key] = row_data

        results = sorted(
            merged.values(),
            key=lambda x: x["similarity"],
            reverse=True
        )

        print("\nTOP SEARCH RESULTS")
        for r in results[:10]:
            print(f"[{r['source']}] score={r['similarity']:.3f} file={r['filename']} chunk={r['chunk_index']}")
            print(r["content"][:220])
            print("-----")

        return results[:limit]

    finally:
        db.close()