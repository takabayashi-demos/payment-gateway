"""Payment gateway tokenizer service."""
import threading
from flask import Flask, jsonify, request

app = Flask(__name__)

_tokenizers = {}
_next_id = 1
_id_lock = threading.Lock()


@app.route("/health")
def health():
    """Health check endpoint."""
    return jsonify({"status": "UP"})


@app.route("/api/v1/tokenizer", methods=["GET"])
def list_tokenizers():
    """List tokenizers with pagination."""
    limit = request.args.get("limit", 20, type=int)
    items = list(_tokenizers.values())[:limit]
    return jsonify({"items": items, "total": len(_tokenizers)})


@app.route("/api/v1/tokenizer/<token_id>", methods=["GET"])
def get_tokenizer(token_id):
    """Get a single tokenizer by ID."""
    entry = _tokenizers.get(token_id)
    if not entry:
        return jsonify({"error": "Tokenizer not found"}), 404
    return jsonify(entry)


@app.route("/api/v1/tokenizer", methods=["POST"])
def create_tokenizer():
    """Create a new tokenizer entry."""
    global _next_id
    payload = request.get_json(silent=True) or {}

    if not payload.get("name") or payload.get("value") is None:
        return jsonify({"error": "name and value are required"}), 400

    with _id_lock:
        token_id = f"tok_{_next_id}"
        _next_id += 1

    entry = {"id": token_id, "name": payload["name"], "value": payload["value"]}
    _tokenizers[token_id] = entry
    return jsonify(entry), 201


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
