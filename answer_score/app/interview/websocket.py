# placeholder: websocket.py
"""
Lightweight WebSocket helpers for real-time interview sessions.

Provides:
- `ConnectionManager` to track connections per session
- `websocket_endpoint` async handler (to be mounted by the API layer)
This is a minimal stub for local prototyping.
"""

import json
import asyncio
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect

class ConnectionManager:
    def __init__(self):
        # session_id -> set of websockets
        self._connections: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self._connections.setdefault(session_id, set()).add(websocket)

    async def disconnect(self, session_id: str, websocket: WebSocket):
        async with self._lock:
            conns = self._connections.get(session_id)
            if conns and websocket in conns:
                conns.remove(websocket)
                if not conns:
                    del self._connections[session_id]

    async def send_personal(self, websocket: WebSocket, message: dict):
        await websocket.send_text(json.dumps(message))

    async def broadcast(self, session_id: str, message: dict):
        conns = list(self._connections.get(session_id, []))
        if not conns:
            return
        data = json.dumps(message)
        for ws in conns:
            try:
                await ws.send_text(data)
            except Exception:
                # ignore send errors for prototype
                pass


manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    Basic endpoint signature for mounting:
    `app.websocket("/ws/{session_id}")(websocket_endpoint)`
    Clients should send/receive JSON messages with keys: {type, payload}
    """
    await manager.connect(session_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
            except Exception:
                msg = {"type": "raw", "payload": data}
            # echo back or broadcast depending on message type
            typ = msg.get("type")
            if typ == "answer":
                # broadcast candidate answer to all session listeners
                await manager.broadcast(session_id, {"type": "answer", "payload": msg.get("payload")})
            elif typ == "question":
                await manager.broadcast(session_id, {"type": "question", "payload": msg.get("payload")})
            else:
                # echo
                await manager.send_personal(websocket, {"type": "ack", "payload": msg})
    except WebSocketDisconnect:
        await manager.disconnect(session_id, websocket)
    except Exception:
        await manager.disconnect(session_id, websocket)