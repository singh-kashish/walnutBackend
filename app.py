from datetime import datetime, timezone
from flask import Flask, jsonify, request
from db.transaction import Transaction, Status
from lib.queue import AsyncEventQueue
import asyncio

app = Flask(__name__)

async def process_transaction(event):
    txn_id = event.get("transaction_id")
    print(f"[worker] started {txn_id}")
    await asyncio.sleep(2)
    tx = Transaction()
    tx.update({
        "transaction_id": txn_id,
        "status": Status.Processed,
        "processed_at": datetime.utcnow().isoformat() + "Z"
    })
    print(f"[worker] finished {txn_id}")

queue = AsyncEventQueue(process_transaction, workers=2)
queue.start()

@app.route("/", methods=["GET"])
def healthcheck():
    return jsonify({
        "status": "HEALTHY",
        "current_time": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    })

@app.route("/v1/webhooks/transactions", methods=["POST"])
def webhook_txn():
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"error": "Missing body"}), 400

    required = ["transaction_id", "source_account", "destination_account", "amount", "currency"]
    for k in required:
        if k not in data:
            return jsonify({"error": f"missing {k}"}), 400

    tx = Transaction()
    rec = tx.create_record({**data, "initial_status": "PROCESSING"})
    tx.save(rec)

    queue.enqueue(rec)
    return ("", 202)

@app.route("/v1/transactions/<transaction_id>", methods=["GET"])
def get_txn(transaction_id):
    tx = Transaction()
    record = tx.get(transaction_id)
    if not record:
        return jsonify({"error": "not found"}), 404
    return jsonify(record), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5020, debug=True)
