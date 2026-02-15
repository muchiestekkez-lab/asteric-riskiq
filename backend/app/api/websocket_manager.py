"""
Asteric RiskIQ - WebSocket Manager

Real-time communication for:
- Live risk score updates
- Alert notifications
- Dashboard refresh signals
"""

import asyncio
import json
from datetime import datetime
from typing import Optional
from fastapi import WebSocket
from loguru import logger


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Send message to all connected clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)

        for conn in disconnected:
            self.disconnect(conn)

    async def send_alert(self, alert: dict):
        """Broadcast an alert to all clients."""
        await self.broadcast({
            "type": "alert",
            "data": alert,
            "timestamp": datetime.now().isoformat(),
        })

    async def send_risk_update(self, patient_id: str, risk_data: dict):
        """Send risk score update for a specific patient."""
        await self.broadcast({
            "type": "risk_update",
            "patient_id": patient_id,
            "data": risk_data,
            "timestamp": datetime.now().isoformat(),
        })

    async def send_dashboard_refresh(self):
        """Signal all clients to refresh dashboard data."""
        await self.broadcast({
            "type": "dashboard_refresh",
            "timestamp": datetime.now().isoformat(),
        })


ws_manager = ConnectionManager()
