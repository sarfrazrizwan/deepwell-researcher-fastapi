from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Annotated
from app.schema.message import MessageRequest, MessageResponse, MessagesResponse, to_chat_message, to_chat_messages
from app.api.deps import DeepwellAgent
from langchain_core.messages import HumanMessage, AIMessage
from uuid import uuid4
from langgraph.types import Command
from app.auth.deps import CurrentUser
from app.services.threads_service import ThreadsService



router = APIRouter(prefix="/threads", tags=["threads"])


def _config(thread_id: str, user_id: str | None = None, ) -> dict:
    
    configurable = {"thread_id": thread_id}
    
    if user_id:
        configurable["user_id"] = user_id
    
    return {"configurable": configurable}    
        
async def _build_response(agent, thread):
    
    thread_id = thread.id
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
        
    
    return {
        "data": MessageResponse(
            thread_id=thread_id,
            status=status,
            title=thread.title,
            message=to_chat_message(values.get("messages")[-1]),
            research_brief=values.get("research_brief"),
            report=values.get("report")
        )
    }
        
        
@router.post("")
async def send_message(
        req: MessageRequest, 
        agent: DeepwellAgent, 
        user: CurrentUser, 
        thread_service: Annotated[ThreadsService, Depends(ThreadsService)],
        background: BackgroundTasks
    ):
    
    thread_id = req.thread_id
    thread = await thread_service.find(thread_id) if thread_id else await thread_service.create(user.id)

    
    config = _config(thread_id=thread.id)

    snapshot = await agent.aget_state(config=config)
    is_paused = any(tasks.interrupts for tasks in snapshot.tasks)
    
    if is_paused:
        await agent.ainvoke(Command(resume=req.message), config=config)
    
    else:     
        await agent.ainvoke({"messages": [HumanMessage(content=req.message)]}, config=config)
    
    if thread.title is None:
        thread = await thread_service.generate_title(thread=thread, messages=snapshot.values.get("messages", []))  
    
    return await _build_response(agent=agent, thread=thread )


@router.get("/{thread_id}")
async def messages(
        thread_id: str, 
        thread_service: Annotated[ThreadsService, Depends(ThreadsService)],
        agent: DeepwellAgent,
        user: CurrentUser
    ):
    
    thread = await thread_service.find(thread_id)
    if thread is None:
        raise HTTPException(detail="Thread not found", status_code=404)
    
    config = _config(thread_id=thread.id)
    state = await agent.aget_state(config=config)
    messages = state.values.get("messages", [])
    compressed_research = state.values.get("compressed_research", None)
    messages.append(
        AIMessage(
            content=compressed_research, 
            id="last",
            response_metadata={
                "ui_kind": "markdown"
            }
        )
        
        ) if compressed_research else None

    return {
        "data": MessagesResponse(
            thread_id=thread_id,
            messages=to_chat_messages(messages=messages),
            status="awaiting_reply",
            report=state.values.get("compressed_research", ""),
            raw_notes=state.values.get("raw_notes", "")
        )
    }


@router.get("")
async def messages(thread_service: Annotated[ThreadsService, Depends(ThreadsService)]):
    
    return {
        "data":  await thread_service.index()
    }

