"""Payment gateway tokenizer service."""
import logging
from flask import Flask, jsonify, request

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Constants
DEFAULT_PAGE_LIMIT = 20
MAX_PAGE_LIMIT = 100

_tokenizers = {}
_next_id = 1


@app.route("/health")
def health():
    """Health check endpoint."""
    return jsonify({"status": "UP"})


@app.route("/api/v1/tokenizer", methods=["GET"])
def list_tokenizers():
    """List tokenizers with pagination."""
    limit = request.args.get("limit", DEFAULT_PAGE_LIMIT, type=int)
    limit = min(limit, MAX_PAGE_LIMIT)
    
    items = list(_tokenizers.values())[:limit]
    logger.info(f"Listed {len(items)} tokenizers (total={len(_tokenizers)}, limit={limit})")
    
    return jsonify({"items": items, "total": len(_tokenizers)})


@app.route("/api/v1/tokenizer/<token_id>", methods=["GET"])
def get_tokenizer(token_id):
    """Get a single tokenizer by ID."""
    entry = _tokenizers.get(token_id)
    if not entry:
        logger.warning(f"Tokenizer not found: {token_id}")
        return jsonify({"error": "Tokenizer not found"}), 404
    
    logger.info(f"Retrieved tokenizer: {token_id}")
    return jsonify(entry)


@app.route("/api/v1/tokenizer", methods=["POST"])
def create_tokenizer():
    """Create a new tokenizer entry."""
    global _next_id
    payload = request.get_json(silent=True) or {}

    if not payload.get("name") or payload.get("value") is None:
        logger.warning("Invalid tokenizer creation request: missing name or value")
        return jsonify({"error": "name and value are required"}), 400

    token_id = f"tok_{_next_id}"
    _next_id += 1
    entry = {"id": token_id, "name": payload["name"], "value": payload["value"]}
    _tokenizers[token_id] = entry
    
    logger.info(f"Created tokenizer: {token_id} (name={payload['name']})")
    return jsonify(entry), 201


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
