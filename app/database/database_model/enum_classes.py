from enum import Enum

class Status(str, Enum):
    RUNNING = "running"
    IDLE = "idle"
    DONE = "done"
    OFFLINE = "offline"