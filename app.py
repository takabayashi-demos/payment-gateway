"""Payment-gateway microservice — tokenizer endpoints."""
import os
import json
import time
import hashlib
import logging
from functools import wraps

from flask import Flask, request, jsonify, g
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
import redis

logger = logging.getLogger(__name__)

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Database connection pool
# ---------------------------------------------------------------------------
DB_URL = os.environ.get("DATABASE_URL", "postgresql://localhost:5432/payments")

engine = create_engine(
    DB_URL,
    poolclass=QueuePool,
    pool_size=int(os.environ.get("DB_POOL_SIZE", "10")),
    max_overflow=int(os.environ.get("DB_POOL_OVERFLOW", "20")),
    pool_timeout=int(os.environ.get("DB_POOL_TIMEOUT", "30")),
    pool_recycle=300,
    pool_pre_ping=True,
)

# ---------------------------------------------------------------------------
# Redis cache
# ---------------------------------------------------------------------------
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
CACHE_TTL = int(os.environ.get("TOKENIZER_CACHE_TTL", "300"))  # 5 minutes

_redis_pool = redis.ConnectionPool.from_url(REDIS_URL, max_connections=20)


def _get_redis():
    return redis.Redis(connection_pool=_redis_pool)


def _cache_key(prefix: str, identifier: str) -> str:
    return f"pg:tok:{prefix}:{identifier}"


def _cache_list_key(query_string: str) -> str:
    h = hashlib.md5(query_string.encode(), usedforsecurity=False).hexdigest()[:12]
    return f"pg:tok:list:{h}"


def cached_response(prefix, ttl=None):
    """Decorator that caches JSON responses in Redis."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            identifier = kwargs.get("tokenizer_id", request.query_string.decode())
            key = _cache_key(prefix, identifier) if "tokenizer_id" in kwargs else _cache_list_key(identifier)
            r = _get_redis()
            try:
                hit = r.get(key)
                if hit is not None:
                    logger.debug("cache hit: %s", key)
                    return jsonify(json.loads(hit))
            except redis.RedisError:
                logger.warning("redis read failed, falling through to db")

            response = fn(*args, **kwargs)

            if response.status_code == 200:
                try:
                    r.setex(key, ttl or CACHE_TTL, response.get_data(as_text=True))
                except redis.RedisError:
                    logger.warning("redis write failed, skipping cache")

            return response
        return wrapper
    return decorator


def _invalidate_cache():
    """Remove all tokenizer cache entries after a write."""
    r = _get_redis()
    try:
        cursor = 0
        while True:
            cursor, keys = r.scan(cursor, match="pg:tok:*", count=200)
            if keys:
                r.delete(*keys)
            if cursor == 0:
                break
    except redis.RedisError:
        logger.warning("cache invalidation failed")


# ---------------------------------------------------------------------------
# Request lifecycle — connection management
# ---------------------------------------------------------------------------
@app.before_request
def _open_conn():
    g.db = engine.connect()


@app.teardown_appcontext
def _close_conn(exc):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
@app.route("/health")
def health():
    return jsonify({"status": "UP", "pool_size": engine.pool.size(), "checked_out": engine.pool.checkedout()})


# ---------------------------------------------------------------------------
# Tokenizer CRUD
# ---------------------------------------------------------------------------
@app.route("/api/v1/tokenizer", methods=["GET"])
@cached_response("list")
def list_tokenizers():
    limit = min(int(request.args.get("limit", 20)), 100)
    offset = int(request.args.get("offset", 0))
    rows = g.db.execute(
        text("SELECT id, name, value, created_at FROM tokenizers ORDER BY created_at DESC LIMIT :l OFFSET :o"),
        {"l": limit, "o": offset},
    ).fetchall()
    items = [{"id": r[0], "name": r[1], "value": r[2], "created_at": str(r[3])} for r in rows]
    return jsonify({"items": items, "limit": limit, "offset": offset})


@app.route("/api/v1/tokenizer/<tokenizer_id>", methods=["GET"])
@cached_response("single")
def get_tokenizer(tokenizer_id):
    row = g.db.execute(
        text("SELECT id, name, value, created_at FROM tokenizers WHERE id = :id"),
        {"id": tokenizer_id},
    ).fetchone()
    if row is None:
        return jsonify({"error": "not found"}), 404
    return jsonify({"id": row[0], "name": row[1], "value": row[2], "created_at": str(row[3])})


@app.route("/api/v1/tokenizer", methods=["POST"])
def create_tokenizer():
    data = request.get_json(silent=True) or {}
    if not data.get("name") or "value" not in data:
        return jsonify({"error": "name and value are required"}), 400
    result = g.db.execute(
        text("INSERT INTO tokenizers (name, value) VALUES (:name, :value) RETURNING id, created_at"),
        {"name": data["name"], "value": data["value"]},
    ).fetchone()
    g.db.commit()
    _invalidate_cache()
    return jsonify({"id": result[0], "name": data["name"], "value": data["value"], "created_at": str(result[1])}), 201


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
