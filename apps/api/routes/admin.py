import os
from fastapi import APIRouter, Header, HTTPException, status
from rag.ingest import ingest_documents
from cache.redis_client import clear_retrieval_cache

router = APIRouter()

ADMIN_API_KEY = os.environ.get("ADMIN_API_KEY", "capstone-secret-reindex-key-2026")

@router.post("/admin/reindex")
def reindex_documents(x_admin_key: str = Header(None, alias="X-Admin-Key")):
    """
    Reindex the knowledge base vector store from markdown documents and clear Redis cache.
    Protected by simple API key header.
    """
    if x_admin_key != ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Admin-Key header."
        )

    chunks_count = ingest_documents()
    clear_retrieval_cache()

    return {
        "status": "success",
        "message": f"Successfully reindexed {chunks_count} chunks into vector store.",
        "cache_cleared": True
    }
