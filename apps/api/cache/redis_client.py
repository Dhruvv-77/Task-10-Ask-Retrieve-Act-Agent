import os
import json
import hashlib
import re
import logging
from typing import Optional, List, Dict, Any
import redis

logger = logging.getLogger("cache.redis_client")

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")
DEFAULT_TTL_SECONDS = 600  # 10 minutes: balance freshness and multi-turn responsiveness

try:
    redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
except Exception as e:
    logger.warning(f"Could not connect to Redis: {e}")
    redis_client = None

def check_redis_health() -> bool:
    """Return True if Redis responds to PING."""
    try:
        if redis_client is None:
            return False
        return redis_client.ping() is True
    except Exception as e:
        logger.warning(f"Redis ping failed: {e}")
        return False

def normalize_query(query: str) -> str:
    """Normalize query by lowercasing, trimming, and stripping excess punctuation/spaces."""
    q = query.lower().strip()
    q = re.sub(r"[^\w\s]", "", q)
    q = re.sub(r"\s+", " ", q)
    return q

def compute_cache_key(normalized_query: str) -> str:
    """Compute SHA256 key for retrieval query caching."""
    q_hash = hashlib.sha256(normalized_query.encode("utf-8")).hexdigest()
    return f"rag:cache:{q_hash}"

def get_cached_retrieval(query: str) -> Optional[List[Dict[str, Any]]]:
    """Retrieve cached chunks + scores if present."""
    if not check_redis_health():
        return None
    try:
        norm_q = normalize_query(query)
        key = compute_cache_key(norm_q)
        cached_data = redis_client.get(key)
        if cached_data:
            logger.info(f"Redis cache HIT for key: {key} (query: '{norm_q}')")
            return json.loads(cached_data)
        logger.info(f"Redis cache MISS for key: {key} (query: '{norm_q}')")
        return None
    except Exception as e:
        logger.warning(f"Error reading from Redis cache: {e}")
        return None

def set_cached_retrieval(query: str, chunks_with_scores: List[Dict[str, Any]], ttl_seconds: int = DEFAULT_TTL_SECONDS):
    """Store retrieved chunks + scores into Redis with TTL."""
    if not check_redis_health():
        return
    try:
        norm_q = normalize_query(query)
        key = compute_cache_key(norm_q)
        serialized = json.dumps(chunks_with_scores)
        redis_client.set(key, serialized, ex=ttl_seconds)
        logger.info(f"Stored retrieval result in Redis with TTL={ttl_seconds}s for key: {key}")
    except Exception as e:
        logger.warning(f"Error setting Redis cache: {e}")

def clear_retrieval_cache():
    """Flush all retrieval cache keys on reindexing."""
    if not check_redis_health():
        return
    try:
        keys = redis_client.keys("rag:cache:*")
        if keys:
            redis_client.delete(*keys)
            logger.info(f"Cleared {len(keys)} RAG cache entries from Redis.")
    except Exception as e:
        logger.warning(f"Error clearing Redis cache: {e}")
