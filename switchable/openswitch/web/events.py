"""Server-Sent Events (SSE) publisher and subscription manager."""

import asyncio
import json
import logging
from collections import defaultdict
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("openswitch.web.events")


class EventBroadcaster:
    """Manages active SSE subscriber queues for experiments."""

    def __init__(self) -> None:
        # experiment_id -> set of asyncio.Queue
        self._subscribers: dict[str, set[asyncio.Queue[str]]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def subscribe(self, experiment_id: str) -> AsyncGenerator[str, None]:
        """Subscribe to SSE events for a specific experiment."""
        queue: asyncio.Queue[str] = asyncio.Queue()
        async with self._lock:
            self._subscribers[experiment_id].add(queue)

        try:
            # Yield initial connection ping
            yield f"event: ping\ndata: {json.dumps({'time': datetime.now(UTC).isoformat()})}\n\n"

            while True:
                msg = await queue.get()
                yield msg
        except asyncio.CancelledError:
            pass
        finally:
            async with self._lock:
                self._subscribers[experiment_id].discard(queue)
                if not self._subscribers[experiment_id]:
                    del self._subscribers[experiment_id]

    async def publish(
        self,
        experiment_id: str,
        event_type: str,
        data: dict[str, Any],
    ) -> None:
        """Broadcast an event to all connected clients for an experiment."""
        payload = {
            "type": event_type,
            "experiment_id": experiment_id,
            "timestamp": datetime.now(UTC).isoformat(),
            **data,
        }
        msg = f"event: {event_type}\ndata: {json.dumps(payload)}\n\n"

        async with self._lock:
            queues = list(self._subscribers.get(experiment_id, set()))

        for q in queues:
            try:
                q.put_nowait(msg)
            except asyncio.QueueFull:
                logger.warning(f"Queue full for experiment {experiment_id}, dropping message.")


# Singleton broadcaster
broadcaster = EventBroadcaster()
