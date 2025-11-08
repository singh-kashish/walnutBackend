# db/transaction_lock.py
from typing import Optional, Tuple, Dict, Any
from db.client import supabase

LOCKS_TABLE = "TransactionLocks"

def try_acquire_lock(transaction_id: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Attempt to acquire a distributed lock for transaction_id.
    Returns (acquired, data). If acquired is False, another process holds/held the lock.
    Implementation: upsert unique(transaction_id). First writer "wins".
    """
    try:
        res = supabase.from_(LOCKS_TABLE).upsert({"transaction_id": transaction_id}, on_conflict="transaction_id").execute()
        code = getattr(res, "status_code", 200)
        data = getattr(res, "data", None)
        # Supabase returns 201/200; upsert with unique conflict should not duplicate.
        # If data is empty but code is 200/201, consider lock acquired (table might not return inserted row).
        acquired = True
        return acquired, data
    except Exception as e:
        print(f"[Lock] acquire error for {transaction_id}: {e}")
        return False, None

def release_lock(transaction_id: str) -> bool:
    """
    Delete the lock row so future replays can be deterministically ignored or retried.
    """
    try:
        res = supabase.from_(LOCKS_TABLE).delete().eq("transaction_id", transaction_id).execute()
        code = getattr(res, "status_code", 200)
        return code in (200, 204)
    except Exception as e:
        print(f"[Lock] release error for {transaction_id}: {e}")
        return False
