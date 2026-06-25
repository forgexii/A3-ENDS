"""
WebSocket Routes

Provides real-time push notifications for:
  - New detections / alerts
  - HITL pending approvals
  - Drift events
  - System health updates

The FastAPI app mounts this router at /api/ws.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Set
import asyncio
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["WebSocket"])

# ---------------------------------------------------------------------------
# Connection registry — keyed by channel name
# ---------------------------------------------------------------------------

_connections: dict[str, Set[WebSocket]] = {
    "alerts":   set(),
    "hitl":     set(),
    "health":   set(),
}


async def _broadcast(channel: str, payload: dict):
    """Send a JSON message to all subscribers on a channel."""
    dead = set()
    message = json.dumps(payload, default=str)
    for ws in _connections.get(channel, set()):
        try:
            await ws.send_text(message)
        except Exception:
            dead.add(ws)
    _connections.get(channel, set()).difference_update(dead)


# ---------------------------------------------------------------------------
# ALERT PUSH  (called from detection_orchestration background task)
# ---------------------------------------------------------------------------

async def push_alert(alert_data: dict):
    """Push a new alert to all alert subscribers."""
    await _broadcast("alerts", {
        "type":      "new_alert",
        "data":      alert_data,
        "timestamp": datetime.utcnow().isoformat(),
    })


async def push_hitl(approval_data: dict):
    """Push a new HITL approval request to all HITL subscribers."""
    await _broadcast("hitl", {
        "type":      "approval_needed",
        "data":      approval_data,
        "timestamp": datetime.utcnow().isoformat(),
    })


async def push_hitl_resolved(detection_id: str, resolution: str):
    """Push HITL resolution (approved / rejected / timeout) to all subscribers."""
    await _broadcast("hitl", {
        "type":       "approval_resolved",
        "detection_id": detection_id,
        "resolution": resolution,
        "timestamp":  datetime.utcnow().isoformat(),
    })


# ---------------------------------------------------------------------------
# WS ENDPOINTS
# ---------------------------------------------------------------------------

@router.websocket("/alerts")
async def ws_alerts(websocket: WebSocket):
    """Subscribe to real-time alert push notifications."""
    await websocket.accept()
    _connections["alerts"].add(websocket)
    logger.info(f"[WS] Alert subscriber connected ({len(_connections['alerts'])} total)")
    try:
        while True:
            try:
                # Keep connection alive; client can send ping
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                if data.strip() == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except asyncio.TimeoutError:
                await websocket.send_text(json.dumps({"type": "heartbeat", "timestamp": datetime.utcnow().isoformat()}))
    except WebSocketDisconnect:
        pass
    finally:
        _connections["alerts"].discard(websocket)
        logger.info(f"[WS] Alert subscriber disconnected ({len(_connections['alerts'])} remaining)")


@router.websocket("/hitl")
async def ws_hitl(websocket: WebSocket):
    """Subscribe to HITL approval push notifications."""
    await websocket.accept()
    _connections["hitl"].add(websocket)
    logger.info(f"[WS] HITL subscriber connected ({len(_connections['hitl'])} total)")
    try:
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                if data.strip() == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except asyncio.TimeoutError:
                await websocket.send_text(json.dumps({"type": "heartbeat", "timestamp": datetime.utcnow().isoformat()}))
    except WebSocketDisconnect:
        pass
    finally:
        _connections["hitl"].discard(websocket)
        logger.info(f"[WS] HITL subscriber disconnected ({len(_connections['hitl'])} remaining)")


@router.websocket("/health")
async def ws_health(websocket: WebSocket):
    """Push system health updates every 5 seconds."""
    await websocket.accept()
    _connections["health"].add(websocket)
    try:
        while True:
            await asyncio.sleep(5)
            await websocket.send_text(json.dumps({
                "type":      "health_update",
                "timestamp": datetime.utcnow().isoformat(),
                "status":    "online",
            }))
    except WebSocketDisconnect:
        pass
    finally:
        _connections["health"].discard(websocket)
