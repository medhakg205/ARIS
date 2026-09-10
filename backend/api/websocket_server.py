"""
ARIS WebSocket Real-Time Telemetry Streaming Server.
Streams validated canonical telemetry samples to connected frontend clients on:
/ws/telemetry/{run_id}
Also provides backward-compatible fallback on /ws/telemetry.
"""

import json
import asyncio
import logging
from typing import Dict, List, Set, Optional
from fastapi import WebSocket, WebSocketDisconnect

from backend.telemetry.telemetry_schema import TelemetrySample
from backend.api.dependencies import get_ingestor

logger = logging.getLogger("aris.api.websocket")


class WebSocketTelemetryManager:
    """
    Manages active client WebSocket connections grouped by target run_id.
    """

    def __init__(self):
        # Map run_id to set of connected WebSockets
        self.connections: Dict[str, Set[WebSocket]] = {}
        # Catch-all connections that listen to any active run
        self.broadcast_connections: Set[WebSocket] = set()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._lock = asyncio.Lock()

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Stores reference to running asyncio event loop for threadsafe dispatch."""
        self._loop = loop

    async def connect(self, websocket: WebSocket, run_id: Optional[str] = None) -> None:
        """Registers a new client WebSocket."""
        await websocket.accept()
        async with self._lock:
            if run_id:
                if run_id not in self.connections:
                    self.connections[run_id] = set()
                self.connections[run_id].add(websocket)
            else:
                self.broadcast_connections.add(websocket)
        logger.info(f"WebSocket client connected for run: {run_id or 'ALL'}")

    async def disconnect(self, websocket: WebSocket, run_id: Optional[str] = None) -> None:
        """Removes a client WebSocket connection."""
        async with self._lock:
            if run_id and run_id in self.connections:
                self.connections[run_id].discard(websocket)
                if not self.connections[run_id]:
                    del self.connections[run_id]
            self.broadcast_connections.discard(websocket)
        logger.info(f"WebSocket client disconnected for run: {run_id or 'ALL'}")

    def dispatch_sample(self, sample: TelemetrySample) -> None:
        """
        Thread-safe dispatch of a validated TelemetrySample to relevant WebSockets.
        Invoked as a subscriber callback from TelemetryIngestor.
        """
        if not self._loop or self._loop.is_closed():
            return

        payload_json = json.dumps(sample.model_dump())
        targets = set(self.broadcast_connections)
        if sample.run_id in self.connections:
            targets.update(self.connections[sample.run_id])

        for ws in targets:
            try:
                if self._loop and self._loop.is_running():
                    asyncio.run_coroutine_threadsafe(ws.send_text(payload_json), self._loop)
                else:
                    try:
                        loop = asyncio.get_running_loop()
                        loop.create_task(ws.send_text(payload_json))
                    except RuntimeError:
                        pass
            except Exception as e:
                logger.debug(f"Failed sending telemetry over WebSocket: {e}")


# Singleton instance
ws_manager = WebSocketTelemetryManager()

# Hook dispatch_sample into the telemetry ingestor
get_ingestor().subscribe(ws_manager.dispatch_sample)
