# app/routes/websockets/connection_manager.py
import asyncio
import logging
from typing import Dict, Optional
from fastapi import WebSocket

logger = logging.getLogger("ws.manager")
logger.setLevel(logging.INFO)


class ConnectionManager:
    """
    - manager.connect_* will ACCEPT the websocket (so do NOT accept in the route).
    - manager maintains 1:1 mapping:
        active_esps: {esp_mac_address: (websocket, last_seen_task)}
        active_mobiles: {esp_mac_address: websocket}
    - provides safe send helpers and cleanup.
    """

    def __init__(self):
        self.active_esps: Dict[str, WebSocket] = {}
        self.active_mobiles: Dict[str, WebSocket] = {}
        self._lock = asyncio.Lock()

    async def connect_esp(self, esp_mac_address: str, websocket: WebSocket):
        """Accept and register an ESP websocket. Start background ping task."""
        await websocket.accept()
        async with self._lock:
            # if an ESP with same id exists, close old connection gracefully
            old = self.active_esps.get(esp_mac_address)
            if old:
                try:
                    await old.close()
                except Exception:
                    pass
            self.active_esps[esp_mac_address] = websocket
        logger.info("ESP connected: %s", esp_mac_address)

    async def connect_mobile(self, esp_mac_address: str, websocket: WebSocket):
        """Accept and register a mobile websocket subscribing to an esp_mac_address."""
        await websocket.accept()
        async with self._lock:
            # one mobile per session (1:1). If multiple viewers needed, change to list.
            old = self.active_mobiles.get(esp_mac_address)
            if old:
                try:
                    await old.close()
                except Exception:
                    pass
            self.active_mobiles[esp_mac_address] = websocket
        logger.info("Mobile subscribed to ESP: %s", esp_mac_address)

    async def disconnect_esp(self, esp_mac_address: str):
        async with self._lock:
            self.active_esps.pop(esp_mac_address, None)
            # also remove mobile subscription for that ESP optionally
            # but mobile may continue to try reconnect; we keep behavior as-is
        logger.info("ESP disconnected: %s", esp_mac_address)

    async def disconnect_mobile(self, esp_mac_address: str):
        async with self._lock:
            self.active_mobiles.pop(esp_mac_address, None)
        logger.info("Mobile disconnected subscription: %s", esp_mac_address)

    # Safe send wrappers (catch errors)
    async def send_to_esp(self, esp_mac_address: str, message: dict) -> bool:
        ws = self.active_esps.get(esp_mac_address)
        if not ws:
            logger.debug("No ESP ws for %s", esp_mac_address)
            return False
        try:
            await ws.send_json(message)
            return True
        except Exception as exc:
            logger.warning("Failed to send to esp %s: %s", esp_mac_address, exc)
            await self._try_close(ws)
            await self.disconnect_esp(esp_mac_address)
            return False

    async def send_to_mobile(self, esp_mac_address: str, message: dict) -> bool:
        ws = self.active_mobiles.get(esp_mac_address)
        if not ws:
            logger.debug("No mobile ws for %s", esp_mac_address)
            return False
        try:
            await ws.send_json(message)
            return True
        except Exception as exc:
            logger.warning("Failed to send to mobile for %s: %s", esp_mac_address, exc)
            await self._try_close(ws)
            await self.disconnect_mobile(esp_mac_address)
            return False

    async def _try_close(self, ws: WebSocket):
        try:
            await ws.close()
        except Exception:
            pass


# single module-level manager to import
manager = ConnectionManager()
