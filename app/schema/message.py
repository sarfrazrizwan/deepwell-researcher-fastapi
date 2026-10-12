from pydantic import BaseModel, Field
from typing import Literal, Any
from uuid import UUID
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, ToolMessage, SystemMessage

Role = Literal["user", "ai", "tool", "system"]
ThreadStatus = Literal["awaiting_reply", "awaiting_approval", "running", "done"]


class ToolCall(BaseModel):
    id: str | None = None
    name: str
    args: dict[str, Any]
class ChatMessage(BaseModel):
    
    id: str
    content: str = ""
    role: Role
    tool_calls: list[ToolCall] = Field(default_factory=list)
    meta: dict | None = {}
    
    @classmethod
    def from_langchain(self, message: BaseMessage):
        return self(
            id=message.id,
            content=message.content,
            role=_role_of(message=message),
            tool_calls=[ToolMessage(
                id=tool_call.get("tool_call_id"),
                name=tool_call.get("name"),
                args=tool_call.get("args", [])
                ) 
                        
                for tool_call in getattr(message, "tool_calls", None) or []
            ],
            meta=message.response_metadata
            
        )

def _role_of(message: BaseMessage) -> Role:
    if isinstance(message, HumanMessage):
        return "user"
    
    if isinstance(message, AIMessage):
        return "ai"
    
   
    if isinstance(message, ToolMessage):
        return "tool"   
    
    if isinstance(message, SystemMessage):
            return "system" 

def to_chat_message(message: BaseMessage) -> ChatMessage:
    return ChatMessage.from_langchain(message=message)

def to_chat_messages(messages: list[BaseMessage]) -> list[ChatMessage]:
    return [to_chat_message(m) for m in messages]
    
class MessageRequest(BaseModel):
    message: str
    thread_id: str | None = None   # omit to start a new conversation

class ApprovalRequest(BaseModel):
    thread_id: str
    user_id: str
    approved: bool
    brief: str = None
    feedback: str = None

class MessageResponse(BaseModel):
    thread_id: UUID
    message: ChatMessage
    title: str | None = None
    status: ThreadStatus
    research_brief: str | None = None
    report: str | None = None

class MessagesResponse(BaseModel):
    thread_id: UUID
    messages: list[ChatMessage]
    title: str | None = None
    status: ThreadStatus
    research_brief: str | None = None
    report: str | None = None
    raw_notes: list[str] | None = Field(default_factory=list)
