from enum import StrEnum


class ThreadStatus(StrEnum):
    RUNNING = "running"
    AWAITING_INPUT = "awaiting_input"
    DONE = "done"
    FAILED = "failed"
