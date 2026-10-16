import os
import logging
from typing import List, Dict, Any, Optional
import chromadb

from cache.redis_client import get_cached_retrieval, set_cached_retrieval

logger = logging.getLogger("rag.retrieve")

CHROMA_PERSIST_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "chroma_db"))
RELEVANCE_THRESHOLD = 0.65
TOP_K = 5

_chroma_client = None
_collection = None

def get_collection():
    global _chroma_client, _collection
    if _collection is None:
        os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        _collection = _chroma_client.get_or_create_collection(
            name="capstone-kb",
            metadata={"hnsw:space": "cosine"}
        )
    return _collection

def check_vector_store_health() -> bool:
    """Check if Chroma vector store is accessible."""
    try:
        col = get_collection()
        col.count()
        return True
    except Exception as e:
        logger.warning(f"Vector store health check failed: {e}")
        return False

def retrieve_chunks(query: str, top_k: int = TOP_K, min_score: float = RELEVANCE_THRESHOLD) -> Dict[str, Any]:
    """
    Retrieve top-k chunks with Redis cache lookup and score thresholding.
    Returns:
    {
        "query": str,
        "chunks": List[Dict[str, Any]],
        "top_score": float,
        "is_relevant": bool,
        "from_cache": bool
    }
    """
    # 1. Check Redis cache first
    cached_chunks = get_cached_retrieval(query)
    if cached_chunks is not None:
        top_score = max([c.get("score", 0.0) for c in cached_chunks], default=0.0)
        return {
            "query": query,
            "chunks": cached_chunks,
            "top_score": round(top_score, 4),
            "is_relevant": top_score >= min_score,
            "from_cache": True
        }

    # 2. Query Vector DB
    collection = get_collection()
    count = collection.count()
    if count == 0:
        logger.warning("Vector collection is empty. Run /admin/reindex or ingest.py first.")
        return {
            "query": query,
            "chunks": [],
            "top_score": 0.0,
            "is_relevant": False,
            "from_cache": False
        }

    results = collection.query(
        query_texts=[query],
        n_results=min(top_k, count)
    )

    chunks = []
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0] if "distances" in results else []

    for idx in range(len(docs)):
        # In cosine distance space [0, 2], normalized similarity is 1.0 - (distance / 2.0).
        # This maps matching chunks to ~0.75-0.90 (as shown in Section 6 of the spec)
        # while keeping unrelated chunks well below the 0.65 threshold.
        dist = distances[idx] if idx < len(distances) and distances[idx] is not None else 1.0
        score = max(0.0, min(1.0, 1.0 - (dist / 2.0)))
        metadata = metas[idx] if idx < len(metas) else {}
        
        chunks.append({
            "docId": metadata.get("docId", f"doc-{idx}"),
            "title": metadata.get("title", "Policy Document"),
            "section": metadata.get("section", "General"),
            "text": docs[idx],
            "score": round(score, 4)
        })

    # Sort descending by score
    chunks.sort(key=lambda x: x["score"], reverse=True)
    top_score = chunks[0]["score"] if chunks else 0.0
    is_relevant = top_score >= min_score

    # 3. Cache valid retrieval in Redis
    if chunks:
        set_cached_retrieval(query, chunks)

    return {
        "query": query,
        "chunks": chunks,
        "top_score": round(top_score, 4),
        "is_relevant": is_relevant,
        "from_cache": False
    }
