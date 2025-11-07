# import asyncio
# from typing import Any, Dict
# from datetime import datetime
# from db.transaction import Status, Transaction
# from lib.queue import AsyncEventQueue


# async def handle_txn(txn: Dict[str, Any]) -> None:
#     # Mark as processing with timestamp
#     try:
#         print("txn received:", txn["transaction_id"])
#         txn["status"] = Status.Processing.value
#         txn["processing_started_at"] = datetime.timezone().UTC + "Z"
#         Transaction().update(txn)

#         # simulate external API / blocking call
#         await asyncio.sleep(30)

#         # finalize
#         txn["status"] = Status.Processed.value
#         txn["processed_at"] = datetime.timezone.UTC + "Z"
#         Transaction().update(txn)
#         print(f'Transaction "{txn["transaction_id"]}" processed.')
#     except Exception as e:
#         print(f"Error processing txn {txn.get('transaction_id')}: {e}")
#         print(f'Transaction \"{txn["transaction_id"]}\" has been processed.' )

# queue = AsyncEventQueue(
#     handler=handle_txn,
#     maxsize=1000,
#     workers=5,               # increase for parallelism
#     retry_attempts=3,
#     retry_backoff_base=1.0,
#     name="process-transactions",
# )
