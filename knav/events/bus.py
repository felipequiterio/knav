"""Thread-safe in-process pub/sub event bus.

FSW publishes from its thread; API consumers (WebSocket) await events on the async side.
"""

import asyncio
import logging
import queue
from collections.abc import Callable
from typing import Any

from knav.events.events import Event

logger = logging.getLogger(__name__)


class EventBus:
    """Dual-queue event bus for cross-thread communication.

    - sync_queue: queue.Queue for sync consumers (logging, etc.)
    - async_queue: asyncio.Queue for async consumers (WebSocket broadcaster)

    The GNC thread calls publish() which is thread-safe. Async consumers call
    subscribe_async() and iterate over events.
    """

    def __init__(self, async_queue_size: int = 256, sync_queue_size: int = 256) -> None:
        self._async_queue: asyncio.Queue[Event] | None = None
        self._async_queue_size = async_queue_size
        self._sync_queue: queue.Queue[Event] = queue.Queue(maxsize=sync_queue_size)
        self._sync_callbacks: list[Callable[[Event], Any]] = []
        self._loop: asyncio.AbstractEventLoop | None = None

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Bind to the asyncio event loop. Call once from the API thread at startup."""
        self._loop = loop
        self._async_queue = asyncio.Queue(maxsize=self._async_queue_size)

    def publish(self, event: Event) -> None:
        """Publish an event (thread-safe, called from GNC thread)."""
        # Sync consumers
        for cb in self._sync_callbacks:
            try:
                cb(event)
            except Exception:
                logger.exception("Sync callback error")

        try:
            self._sync_queue.put_nowait(event)
        except queue.Full:
            # Drop oldest sync event
            try:
                self._sync_queue.get_nowait()
                self._sync_queue.put_nowait(event)
            except queue.Empty:
                pass

        # Async consumers
        if self._loop is not None and self._async_queue is not None:
            self._loop.call_soon_threadsafe(self._async_put, event)

    def _async_put(self, event: Event) -> None:
        """Put event into async queue (runs on the event loop thread)."""
        if self._async_queue is None:
            return
        try:
            self._async_queue.put_nowait(event)
        except asyncio.QueueFull:
            # Drop oldest async event
            try:
                self._async_queue.get_nowait()
                self._async_queue.put_nowait(event)
            except asyncio.QueueEmpty:
                pass

    async def subscribe_async(self):
        """Async generator that yields events. Use in WebSocket handlers."""
        if self._async_queue is None:
            raise RuntimeError("EventBus.set_loop() not called")
        while True:
            event = await self._async_queue.get()
            yield event

    def subscribe_sync(self, callback: Callable[[Event], Any]) -> None:
        """Register a synchronous callback for all events."""
        self._sync_callbacks.append(callback)

    def unsubscribe_sync(self, callback: Callable[[Event], Any]) -> None:
        """Remove a synchronous callback."""
        self._sync_callbacks.remove(callback)

    def drain_sync(self, max_events: int = 100) -> list[Event]:
        """Drain up to max_events from the sync queue."""
        events = []
        for _ in range(max_events):
            try:
                events.append(self._sync_queue.get_nowait())
            except queue.Empty:
                break
        return events
