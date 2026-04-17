"""Payment gateway tokenizer service."""
from flask import Flask, jsonify, request
import re

app = Flask(__name__)

_tokenizers = {}
_next_id = 1

# Security constants
MAX_NAME_LENGTH = 100
MAX_VALUE_LENGTH = 500
ALLOWED_VALUE_TYPES = (str, int, float, bool)


def validate_tokenizer_input(payload):
    """Validate tokenizer input for security."""
    if not isinstance(payload, dict):
        return "Invalid request format", 400
    
    name = payload.get("name")
    value = payload.get("value")
    
    # Check required fields
    if not name or value is None:
        return "name and value are required", 400
    
    # Validate name
    if not isinstance(name, str):
        return "name must be a string", 400
    
    if len(name) > MAX_NAME_LENGTH:
        return f"name must not exceed {MAX_NAME_LENGTH} characters", 400
    
    # Sanitize name - only allow alphanumeric, spaces, dashes, underscores
    if not re.match(r'^[a-zA-Z0-9\s_-]+$', name):
        return "name contains invalid characters", 400
    
    # Validate value type
    if not isinstance(value, ALLOWED_VALUE_TYPES):
        return "value must be string, number, or boolean", 400
    
    # Validate value length if string
    if isinstance(value, str) and len(value) > MAX_VALUE_LENGTH:
        return f"value must not exceed {MAX_VALUE_LENGTH} characters", 400
    
    return None, None


@app.route("/health")
def health():
    """Health check endpoint."""
    return jsonify({"status": "UP"})


@app.route("/api/v1/tokenizer", methods=["GET"])
def list_tokenizers():
    """List tokenizers with pagination."""
    limit = request.args.get("limit", 20, type=int)
    # Enforce max limit to prevent memory exhaustion
    limit = min(limit, 100)
    items = list(_tokenizers.values())[:limit]
    return jsonify({"items": items, "total": len(_tokenizers)})


@app.route("/api/v1/tokenizer/<token_id>", methods=["GET"])
def get_tokenizer(token_id):
    """Get a single tokenizer by ID."""
    # Validate token_id format to prevent path traversal
    if not re.match(r'^tok_\d+$', token_id):
        return jsonify({"error": "Invalid token ID format"}), 400
    
    entry = _tokenizers.get(token_id)
    if not entry:
        return jsonify({"error": "Tokenizer not found"}), 404
    return jsonify(entry)


@app.route("/api/v1/tokenizer", methods=["POST"])
def create_tokenizer():
    """Create a new tokenizer entry."""
    global _next_id
    
    # Validate content type
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 415
    
    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({"error": "Invalid JSON"}), 400
    
    # Validate input
    error_msg, status_code = validate_tokenizer_input(payload)
    if error_msg:
        return jsonify({"error": error_msg}), status_code
    
    token_id = f"tok_{_next_id}"
    _next_id += 1
    entry = {"id": token_id, "name": payload["name"], "value": payload["value"]}
    _tokenizers[token_id] = entry
    return jsonify(entry), 201


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
