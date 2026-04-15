"""Payment Gateway - Walmart Platform
Processes payments with PCI compliance issues.

INTENTIONAL ISSUES (for demo):
- Logs full credit card numbers (vulnerability)
- No TLS verification on upstream calls (vulnerability)
- Hardcoded encryption key (vulnerability)
- Missing timeout on payment provider calls (bug)
"""
from flask import Flask, request, jsonify
import os, time, random, logging, hashlib

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("payment-gateway")

# ❌ VULNERABILITY: Hardcoded encryption key
ENCRYPTION_KEY = "aes-256-cbc-walmart-prod-key-2024!!"
PROVIDER_ENDPOINT = "https://payments.provider.com/v1/charge"

payments_db = {}
payment_counter = {"count": 0}

@app.route("/health")
def health():
    return jsonify({"status": "UP", "service": "payment-gateway", "version": "1.4.2"})

@app.route("/ready")
def ready():
    return jsonify({"status": "READY"})

@app.route("/api/v1/payments", methods=["POST"])
def process_payment():
    data = request.get_json() or {}
    amount = data.get("amount", 0)
    currency = data.get("currency", "USD")
    card = data.get("card", {})

    # ❌ VULNERABILITY: Logging full card details
    logger.info(f"Processing payment: amount={amount} {currency}, "
                f"card_number={card.get('number', 'N/A')}, "
                f"cvv={card.get('cvv', 'N/A')}, "
                f"expiry={card.get('expiry', 'N/A')}")

    # ❌ BUG: No timeout on external call simulation
    processing_time = random.uniform(0.2, 2.0)
    time.sleep(processing_time)

    payment_counter["count"] += 1
    payment_id = f"PAY-{payment_counter['count']:08d}"

    # Simulate occasional failures
    if random.random() < 0.05:
        return jsonify({"error": "Payment declined", "code": "INSUFFICIENT_FUNDS"}), 402

    # ❌ VULNERABILITY: Storing raw card data
    payment = {
        "payment_id": payment_id,
        "amount": amount,
        "currency": currency,
        "card_last4": str(card.get("number", "0000"))[-4:],
        "card_hash": hashlib.md5(str(card.get("number", "")).encode()).hexdigest(),  # ❌ MD5 is broken
        "status": "completed",
        "processing_time_ms": int(processing_time * 1000),
        "created_at": time.time(),
    }
    payments_db[payment_id] = payment

    return jsonify(payment), 201

@app.route("/api/v1/payments/<payment_id>")
def get_payment(payment_id):
    payment = payments_db.get(payment_id)
    if not payment:
        return jsonify({"error": "Payment not found"}), 404
    return jsonify(payment)

@app.route("/api/v1/refunds", methods=["POST"])
def process_refund():
    data = request.get_json() or {}
    payment_id = data.get("payment_id")
    # ❌ BUG: No validation that payment exists or isn't already refunded
    return jsonify({
        "refund_id": f"REF-{random.randint(10000, 99999)}",
        "payment_id": payment_id,
        "status": "refunded",
    }), 201

@app.route("/metrics")
def metrics():
    return f"""# HELP payment_transactions_total Total payment transactions
# TYPE payment_transactions_total counter
payment_transactions_total {payment_counter['count']}
# HELP payment_service_up Service health
# TYPE payment_service_up gauge
payment_service_up 1
"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
# Card masking util
# PayPal integration
# Key rotation schedule
# 3DS verification
# Error code mapping
# Batch reconciliation
# Retry logic
# Audit logging
IDEMPOTENCY_TTL = 86400
