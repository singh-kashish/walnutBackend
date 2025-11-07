import asyncio
import threading
from typing import Any, Callable, Dict, Optional

Event = Dict[str, Any]
AsyncEventHandler = Callable[[Event], None]


class AsyncEventQueue:
    def __init__(self, handler: AsyncEventHandler, workers: int = 1, maxsize: int = 1000):
        if not asyncio.iscoroutinefunction(handler):
            raise TypeError("handler must be async")
        self.handler = handler
        self.maxsize = maxsize
        self.workers = workers
        self.queue = asyncio.Queue(maxsize=maxsize)
        self.loop = asyncio.new_event_loop()
        self.thread: Optional[threading.Thread] = None

    def start(self):
        if self.thread and self.thread.is_alive():
            return

        def _run():
            asyncio.set_event_loop(self.loop)
            for i in range(self.workers):
                self.loop.create_task(self.worker(i))
            self.loop.run_forever()

        self.thread = threading.Thread(target=_run, daemon=True)
        self.thread.start()

    def enqueue(self, event: Event):
        def _put():
            try:
                self.queue.put_nowait(event)
            except asyncio.QueueFull:
                print("[AsyncEventQueue] Queue full, dropping event")

        self.loop.call_soon_threadsafe(_put)

    async def worker(self, i: int):
        print(f"[AsyncEventQueue] Worker-{i} started")
        while True:
            event = await self.queue.get()
            try:
                await self.handler(event)
            except Exception as e:
                print(f"[AsyncEventQueue] Worker-{i} error: {e}")
            finally:
                self.queue.task_done()
