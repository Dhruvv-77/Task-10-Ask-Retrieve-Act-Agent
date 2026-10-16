from fastapi import APIRouter, Response, status
from db.session import check_db_health
from cache.redis_client import check_redis_health
from rag.retrieve import check_vector_store_health

router = APIRouter()

@router.get("/health")
def get_health(response: Response):
    """
    Actively checks all dependencies: PostgreSQL, Redis, and Vector Store.
    Returns 200 if all healthy, 503 if any dependency fails.
    """
    db_ok = check_db_health()
    redis_ok = check_redis_health()
    vector_ok = check_vector_store_health()

    all_healthy = db_ok and redis_ok and vector_ok
    if not all_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "ok" if all_healthy else "degraded",
        "db": "ok" if db_ok else "down",
        "redis": "ok" if redis_ok else "down",
        "vector_store": "ok" if vector_ok else "down"
    }
