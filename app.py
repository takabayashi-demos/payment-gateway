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
MIN_NAME_LENGTH = 1
MAX_NAME_LENGTH = 255

_tokenizers = {}
_next_id = 1


def validate_tokenizer_payload(payload):
    """Validate tokenizer creation payload.
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not payload:
        return False, "Request body is required"
    
    name = payload.get("name")
    if not name:
        return False, "Field 'name' is required"
    
    if not isinstance(name, str):
        return False, "Field 'name' must be a string"
    
    if len(name) < MIN_NAME_LENGTH or len(name) > MAX_NAME_LENGTH:
        return False, f"Field 'name' must be between {MIN_NAME_LENGTH} and {MAX_NAME_LENGTH} characters"
    
    if "value" not in payload:
        return False, "Field 'value' is required"
    
    return True, None


def error_response(message, status_code=400):
    """Create standardized error response.
    
    Args:
        message: Error message
        status_code: HTTP status code
        
    Returns:
        tuple: (json_response, status_code)
    """
    logger.warning(f"Error response: {message} (status={status_code})")
    return jsonify({"error": message, "status": status_code}), status_code


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
        return error_response("Tokenizer not found", 404)
    
    logger.info(f"Retrieved tokenizer: {token_id}")
    return jsonify(entry)


@app.route("/api/v1/tokenizer", methods=["POST"])
def create_tokenizer():
    """Create a new tokenizer entry."""
    global _next_id
    payload = request.get_json(silent=True)
    
    is_valid, error_msg = validate_tokenizer_payload(payload)
    if not is_valid:
        return error_response(error_msg)
    
    token_id = f"tok_{_next_id}"
    _next_id += 1
    entry = {"id": token_id, "name": payload["name"], "value": payload["value"]}
    _tokenizers[token_id] = entry
    
    logger.info(f"Created tokenizer: {token_id} (name={payload['name']})")
    return jsonify(entry), 201


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
