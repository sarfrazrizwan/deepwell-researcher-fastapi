from fastapi import APIRouter, HTTPException
from langchain_core.runnables import RunnableConfig
from app.schema.message import MessageRequest, MessageResponse
from app.api.deps import DeepwellAgent
from langchain_core.messages import HumanMessage
from uuid import uuid4
from langgraph.types import Command


router = APIRouter(prefix="/messages", tags=["messages"])


def _config(thread_id: str, user_id: str | None = None) -> dict:
    configurable = {"thread_id": thread_id}
    
    if user_id:
        configurable["user_id"] = user_id
    
    return {"configurable": configurable}    
        
async def _build_response(agent, thread_id):
    
    snap = await agent.aget_state(_config(thread_id=thread_id))
    values = snap.values
    
    if not values:
        raise HTTPException("Thread not found")
    
    
    if values.get("report"):
        status = "done"
    elif snap.interrupts:
        status = "awaiting_approval"
    elif snap.next:
        status = "running"
    else:
        status = "awaiting_reply"
        
    
    return MessageResponse(
        thread_id=thread_id,
        status=status,
        reply=values.get("messages")[-1].content if values.get("messages") else None,
        research_brief=values.get("research_brief"),
        report=values.get("report")
    )
        
        
@router.post("")
async def send_message(req: MessageRequest, agent: DeepwellAgent):
    
    thread_id = req.thread_id or str(uuid4())
    config = _config(thread_id=thread_id)

    snapshot = await agent.aget_state(config=config)
    is_paused = any(tasks.interrupts for tasks in snapshot.tasks)
    
    if is_paused:
        await agent.ainvoke(Command(resume=req.message))
    
    else:     
        await agent.ainvoke({"messages": [HumanMessage(content=req.message)]}, config=config)
    
    return await _build_response(agent=agent, thread_id=thread_id)

