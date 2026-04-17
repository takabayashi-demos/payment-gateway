"""Payment gateway tokenizer service."""
import re
import logging
from flask import Flask, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)

# Configure rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["1000 per hour"],
    storage_uri="memory://"
)

_tokenizers = {}
_next_id = 1

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security constants
MAX_NAME_LENGTH = 255
MAX_VALUE_LENGTH = 1000
NAME_PATTERN = re.compile(r'^[a-zA-Z0-9_\-\.\s]+$')


@app.after_request
def add_security_headers(response):
    """Add security headers to all responses."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    return response


def validate_tokenizer_input(payload):
    """Validate and sanitize tokenizer input."""
    if not isinstance(payload, dict):
        return None, "Invalid payload format"
    
    name = payload.get("name")
    value = payload.get("value")
    
    # Check required fields
    if not name or value is None:
        return None, "name and value are required"
    
    # Validate types
    if not isinstance(name, str):
        return None, "name must be a string"
    
    # Validate lengths
    if len(name) > MAX_NAME_LENGTH:
        return None, f"name exceeds maximum length of {MAX_NAME_LENGTH}"
    
    if isinstance(value, str) and len(value) > MAX_VALUE_LENGTH:
        return None, f"value exceeds maximum length of {MAX_VALUE_LENGTH}"
    
    # Sanitize name - allow only alphanumeric, underscore, dash, dot, space
    if not NAME_PATTERN.match(name):
        return None, "name contains invalid characters (allowed: a-z A-Z 0-9 _ - . space)"
    
    # Strip whitespace
    name = name.strip()
    if not name:
        return None, "name cannot be empty after trimming whitespace"
    
    return {"name": name, "value": value}, None


@app.route("/health")
def health():
    """Health check endpoint."""
    return jsonify({"status": "UP"})


@app.route("/api/v1/tokenizer", methods=["GET"])
def list_tokenizers():
    """List tokenizers with pagination."""
    limit = request.args.get("limit", 20, type=int)
    limit = min(max(1, limit), 100)  # Clamp between 1 and 100
    items = list(_tokenizers.values())[:limit]
    return jsonify({"items": items, "total": len(_tokenizers)})


@app.route("/api/v1/tokenizer/<token_id>", methods=["GET"])
def get_tokenizer(token_id):
    """Get a single tokenizer by ID."""
    # Validate token_id format
    if not re.match(r'^tok_\d+$', token_id):
        return jsonify({"error": "Invalid tokenizer ID format"}), 400
    
    entry = _tokenizers.get(token_id)
    if not entry:
        return jsonify({"error": "Tokenizer not found"}), 404
    return jsonify(entry)


@app.route("/api/v1/tokenizer", methods=["POST"])
@limiter.limit("100 per hour")
def create_tokenizer():
    """Create a new tokenizer entry."""
    global _next_id
    
    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({"error": "Invalid JSON payload"}), 400
    
    # Validate and sanitize input
    validated, error = validate_tokenizer_input(payload)
    if error:
        logger.warning(f"Tokenizer creation failed: {error} - IP: {request.remote_addr}")
        return jsonify({"error": error}), 400
    
    token_id = f"tok_{_next_id}"
    _next_id += 1
    entry = {
        "id": token_id,
        "name": validated["name"],
        "value": validated["value"]
    }
    _tokenizers[token_id] = entry
    
    logger.info(f"Tokenizer created: {token_id} - IP: {request.remote_addr}")
    return jsonify(entry), 201


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
