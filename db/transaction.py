from datetime import datetime, timezone
from typing import Any, Dict, Optional
from db.client import supabase


class Status:
    Processing = "PROCESSING"
    Processed = "PROCESSED"
    Pending = "PENDING"
    Failed = "FAILED"


class Transaction:
    def __init__(self):
        self.table = "Transactions"

    def create_record(self, data: Dict[str, Any]) -> Dict[str, Any]:
        required = ["transaction_id", "source_account", "destination_account", "amount", "currency"]
        for k in required:
            if k not in data:
                raise ValueError(f"Missing required field: {k}")

        record = {
            "transaction_id": data["transaction_id"],
            "source_account": data["source_account"],
            "destination_account": data["destination_account"],
            "amount": float(data["amount"]),
            "currency": data["currency"],
            "status": data.get("initial_status", Status.Processing),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "processed_at": None,
        }
        return record

    def save(self, record: Dict[str, Any]):
        try:
            res = supabase.from_(self.table).upsert(record, on_conflict="transaction_id").execute()
            data = getattr(res, "data", None)
            code = getattr(res, "status_code", 200)
            return data, code
        except Exception as e:
            print(f"[Transaction.save] Error: {e}")
            return None, 500

    def get(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        try:
            res = supabase.from_(self.table).select("*").eq("transaction_id", transaction_id).limit(1).execute()
            data = getattr(res, "data", [])
            if data and len(data) > 0:
                return data[0]
            return None
        except Exception as e:
            print(f"[Transaction.get] Error: {e}")
            return None

    def update(self, record: Dict[str, Any]):
        try:
            txid = record["transaction_id"]
            update_data = {k: v for k, v in record.items() if k != "transaction_id"}
            res = supabase.from_(self.table).update(update_data).eq("transaction_id", txid).execute()
            data = getattr(res, "data", None)
            code = getattr(res, "status_code", 200)
            return data, code
        except Exception as e:
            print(f"[Transaction.update] Error: {e}")
            return None, 500
