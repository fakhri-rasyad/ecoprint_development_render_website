from app.core.enum.enum_classes import Status
from typing import Optional

from dataclasses import dataclass
from datetime import datetime


@dataclass
class SessionCacheEntry:
    session_id: int
    status: Status
    end_time: Optional[datetime]