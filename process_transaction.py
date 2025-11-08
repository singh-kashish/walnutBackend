# process_transaction.py
import asyncio
from datetime import datetime, timezone
from db.transaction import Transaction, Status
from db.transaction_lock import release_lock

async def process_transaction(event: dict):
    txn_id = event.get("transaction_id")
    if not txn_id:
        print("[worker] missing transaction_id")
        return
    try:
        print(f"[worker] started {txn_id}")
        # Simulate external API latency (~30s)
        await asyncio.sleep(30)

        tx = Transaction()
        # Update atomically: only transition if still PROCESSING
        update_payload = {
            "transaction_id": txn_id,
            "status": Status.Processed,
            "processed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        data, code = tx.update(update_payload)
        print(f"[worker] finished {txn_id} update_code={code} data={data}")
    except Exception as e:
        print(f"[worker] ERROR {txn_id}: {e}")
    finally:
        # Release lock regardless (to avoid stale locks)
        ok = release_lock(txn_id)
        if not ok:
            print(f"[worker] WARN: failed to release lock for {txn_id}")
