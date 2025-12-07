from typing import Optional, Dict, Any
import asyncio
from datetime import datetime
from app.core.mqtt.SessionCacheEntry import SessionCacheEntry


class SessionStateManager:
    def __init__(self):
        self.cached_bs: Dict[str, Any] = {}
        self.esp_last_seen: Dict[str, datetime] = {}
        self._lock = asyncio.Lock()  

    async def set_session(self, esp_mac: str, data: Any):
        async with self._lock:
            self.cached_bs[esp_mac] = data

    async def get_session(self, esp_mac: str) -> Optional[Any]:
        async with self._lock:
            return self.cached_bs.get(esp_mac)

    async def remove_session(self, esp_mac: str):
        async with self._lock:
            self.cached_bs.pop(esp_mac, None)

    async def get_all_sessions(self):
        async with self._lock:
            return dict(self.cached_bs)  
        
    async def update_esp_seen(self, esp_id: str):
        async with self._lock:
            self.esp_last_seen[esp_id] = datetime.now()

    async def get_esp_last_seen(self, esp_id: str) -> Optional[datetime]:
        async with self._lock:
            return self.esp_last_seen.get(esp_id)

    async def get_all_esp_last_seen(self):
        async with self._lock:
            return dict(self.esp_last_seen)

    async def remove_esp(self, esp_id: str):
        async with self._lock:
            self.esp_last_seen.pop(esp_id, None)
