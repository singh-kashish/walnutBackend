# app.py
from datetime import datetime, timezone
from flask import Flask, jsonify, request
from db.transaction import Transaction, Status
from db.transaction_lock import try_acquire_lock
from lib.queue import AsyncEventQueue
from process_transaction import process_transaction

app = Flask(__name__)

queue = None  # type: AsyncEventQueue

def init_queue_once():
    global queue
    if queue is None:
        print("[init_queue] starting AsyncEventQueue")
        queue = AsyncEventQueue(process_transaction, workers=2, maxsize=1000)
        queue.start()

@app.route("/", methods=["GET"])
def healthcheck():
    return jsonify({
        "status": "HEALTHY",
        "current_time": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    })

@app.route("/v1/webhooks/transactions", methods=["POST"])
def webhook_txn():
    init_queue_once()

    # tolerant parsing (JSON preferred)
    data = request.get_json(silent=True)
    if not data and request.data:
        try:
            import json
            data = json.loads(request.data.decode("utf-8"))
        except Exception:
            data = None
    if not data and request.form:
        data = request.form.to_dict()

    if not data:
        return jsonify({"error": "Missing body"}), 400

    required = ["transaction_id", "source_account", "destination_account", "amount", "currency"]
    for k in required:
        if k not in data:
            return jsonify({"error": f"missing {k}"}), 400

    txn_id = data["transaction_id"]
    tx = Transaction()

    existing = tx.get(txn_id)

    if not existing:
        # First-time row: insert with PROCESSING
        rec = tx.create_record({
            "transaction_id": txn_id,
            "source_account": data["source_account"],
            "destination_account": data["destination_account"],
            "amount": data["amount"],
            "currency": data["currency"],
            "initial_status": Status.Processing,
        })
        saved, code = tx.save(rec)
        print(f"[webhook] inserted {txn_id} status={Status.Processing} code={code}")
    else:
        # Already exists
        status = existing.get("status")
        if status == Status.Processed:
            print(f"[webhook] {txn_id} already PROCESSED, ack")
            return ("", 202)
        elif status != Status.Processing:
            # Optional: allow retry from FAILED/PENDING
            tx.update({"transaction_id": txn_id, "status": Status.Processing})
            print(f"[webhook] {txn_id} moved to PROCESSING")
        else:
            print(f"[webhook] {txn_id} already PROCESSING")

    # Acquire distributed lock to ensure only one enqueue/run per transaction_id
    acquired, _ = try_acquire_lock(txn_id)
    if not acquired:
        print(f"[webhook] {txn_id} lock not acquired, ack without enqueue")
        return ("", 202)

    # Enqueue for background processing
    if queue:
        print(f"[webhook] enqueue {txn_id}")
        queue.enqueue({"transaction_id": txn_id})
    else:
        print("[webhook] ERROR: queue not initialized")

    # Fast ACK
    return ("", 202)

@app.route("/v1/transactions/<transaction_id>", methods=["GET"])
def get_txn(transaction_id):
    tx = Transaction()
    record = tx.get(transaction_id)
    if not record:
        return jsonify({"error": "not found"}), 404
    return jsonify(record), 200

if __name__ == "__main__":
    init_queue_once()
    app.run(host="0.0.0.0", port=5020, debug=False)
