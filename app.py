"""Payment-gateway microservice — tokenizer API."""
import uuid
from datetime import datetime, timezone
from flask import Flask, request, jsonify

app = Flask(__name__)

# In-memory store (replaced by vault-backed store in production)
_tokens: dict[str, dict] = {}


@app.route("/health")
def health():
    return jsonify({"status": "UP", "service": "payment-gateway"})


@app.route("/api/v1/tokenizer", methods=["GET"])
def list_tokens():
    limit = request.args.get("limit", 20, type=int)
    limit = max(1, min(limit, 100))
    status_filter = request.args.get("status")

    items = list(_tokens.values())
    if status_filter:
        items = [t for t in items if t.get("status") == status_filter]

    items = sorted(items, key=lambda t: t["created_at"], reverse=True)[:limit]
    return jsonify({"items": items, "count": len(items)})


@app.route("/api/v1/tokenizer", methods=["POST"])
def create_token():
    data = request.get_json(silent=True) or {}
    if not data.get("name") or "value" not in data:
        return jsonify({"error": "name and value are required"}), 400

    token_id = str(uuid.uuid4())
    token = {
        "id": token_id,
        "name": data["name"],
        "value": data["value"],
        "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "revoked_at": None,
    }
    _tokens[token_id] = token
    return jsonify(token), 201


@app.route("/api/v1/tokenizer/<token_id>", methods=["GET"])
def get_token(token_id):
    token = _tokens.get(token_id)
    if not token:
        return jsonify({"error": "token not found"}), 404
    return jsonify(token)


@app.route("/api/v1/tokenizer/<token_id>", methods=["DELETE"])
def revoke_token(token_id):
    token = _tokens.get(token_id)
    if not token:
        return jsonify({"error": "token not found"}), 404

    if token["status"] == "revoked":
        return jsonify(token), 200

    token["status"] = "revoked"
    token["revoked_at"] = datetime.now(timezone.utc).isoformat()
    return jsonify(token), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
