from pydantic import BaseModel
from typing import Literal

class MessageRequest(BaseModel):
    message: str
    thread_id: str | None = None   # omit to start a new conversation
    user_id: str | None = None

class ApprovalRequest(BaseModel):
    thread_id: str
    user_id: str
    approved: bool
    brief: str = None
    feedback: str = None


ThreadStatus = Literal["awaiting_reply", "awaiting_approval", "running", "done"]

class MessageResponse(BaseModel):
    thread_id: str
    reply: str
    status: ThreadStatus
    research_brief: str | None = None
    report: str | None = None
