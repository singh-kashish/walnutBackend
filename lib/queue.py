# lib/queue.py
import asyncio
import threading
from queue import Queue as ThreadQueue, Full as ThreadQueueFull
from typing import Any, Callable, Dict, Optional

Event = Dict[str, Any]
AsyncEventHandler = Callable[[Event], Any]


class AsyncEventQueue:
    """
    Background thread runs one asyncio loop.
    Flask request thread enqueues events via thread-safe ThreadQueue.
    Worker drains inbox using run_in_executor to avoid cross-loop futures.
    """
    def __init__(self, handler: AsyncEventHandler, workers: int = 1, maxsize: int = 1000):
        if not asyncio.iscoroutinefunction(handler):
            raise TypeError("handler must be async")
        self.handler = handler
        self.workers = max(1, workers)
        self._inbox: ThreadQueue[Event] = ThreadQueue(maxsize=maxsize)
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._running = threading.Event()

    def start(self):
        if self._thread and self._thread.is_alive():
            return

        def _run():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._running.set()
            for i in range(self.workers):
                self._loop.create_task(self._worker(i))
            try:
                self._loop.run_forever()
            finally:
                pending = asyncio.all_tasks(loop=self._loop)
                for t in pending:
                    t.cancel()
                try:
                    self._loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                except Exception:
                    pass
                self._loop.close()

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()
        self._running.wait()
        print(f"[AsyncEventQueue] started with {self.workers} worker(s)")

    def enqueue(self, event: Event):
        try:
            self._inbox.put_nowait(event)
        except ThreadQueueFull:
            print("[AsyncEventQueue] Inbox full, dropping event")

    async def _worker(self, i: int):
        print(f"[AsyncEventQueue] Worker-{i} started")
        while True:
            event = await self._loop.run_in_executor(None, self._blocking_get)
            try:
                await self.handler(event)
            except Exception as e:
                print(f"[AsyncEventQueue] Worker-{i} error: {e}")

    def _blocking_get(self) -> Event:
        return self._inbox.get()
