# app/core/telemetry_batcher.py
import asyncio
from sqlalchemy import insert
from sqlmodel import Session
from app.database.database import engine
from app.database.database_model.sensor_reading_database_model import SensorReading


class TelemetryBatcher:
    def __init__(self, flush_interval: float = 5.0, max_buffer: int = 20):
        self.flush_interval = flush_interval
        self.max_buffer = max_buffer
        self.buffers = {}
        self.locks = {}
        self.running = False

    def _get_lock(self, session_id: int):
        if session_id not in self.locks:
            self.locks[session_id] = asyncio.Lock()
        return self.locks[session_id]

    async def add(self, session_id: int, row: dict):
        if session_id not in self.buffers:
            self.buffers[session_id] = []

        lock = self._get_lock(session_id)

        async with lock:
            self.buffers[session_id].append(row)

            # Auto-flush if too many entries
            if len(self.buffers[session_id]) >= self.max_buffer:
                await self.flush_one(session_id)

    async def flush_one(self, session_id: int):
        """Flush one session's buffer all at once."""
        if session_id not in self.buffers or not self.buffers[session_id]:
            return

        lock = self._get_lock(session_id)

        # pop buffer safely
        async with lock:
            rows = self.buffers[session_id]
            self.buffers[session_id] = []

        # 🚀 Perform bulk insert via SQLAlchemy Core (10x faster)
        try:
            with engine.begin() as conn:
                conn.execute(
                    insert(SensorReading),
                    rows  # dictionary mappings
                )
        except Exception as e:
            print("Batch insert failed:", e)

    async def flush_loop(self):
        """Background interval flush."""
        self.running = True
        while self.running:
            await asyncio.sleep(self.flush_interval)
            for session_id in list(self.buffers.keys()):
                await self.flush_one(session_id)

    def stop(self):
        self.running = False


telemetry_batcher = TelemetryBatcher()
