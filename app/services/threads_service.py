from app.db.session import AsyncSession, get_async_session
from uuid import UUID
from app.models.thread import Thread
from typing import Annotated
from fastapi import Depends
from sqlalchemy import select, update
from app.auth.deps import CurrentUser
from langchain_core.messages import BaseMessage
from app.utils.chat import generate_title as generate_chat_title

class ThreadsService():
    
    def __init__(self, 
            session: Annotated[AsyncSession, Depends(get_async_session)],
            user: CurrentUser,
           
        ):
        self.session = session
        self.user = user
        
    
    async def index(self) -> list[Thread]:
        stmt = select(Thread).where(Thread.user_id == self.user.id)
        stmt = stmt.order_by(Thread.updated_at.desc())
        result = await self.session.execute(stmt)
        threads = result.scalars().all()
        
        return threads
            
    async def find(self, id: str) -> Thread | None:
        stmt = select(Thread).where(Thread.id == id)
        result = await self.session.execute(stmt)
        
        return result.scalar_one_or_none()
    
    
    async def create(self, user_id: str) -> Thread:
        
        thread = Thread(
            user_id=user_id
        )
        
        self.session.add(thread)
        await self.session.commit()
        await self.session.refresh(thread)
        
        return thread
    
    async def generate_title(self, thread: str | Thread, messages: list[BaseMessage]):
        if not isinstance (thread, Thread):
            thread = await self.find(thread)
            
        title: str = await generate_chat_title(messages=messages)
        
        await self.session.execute(
            update(Thread).where(Thread.id == thread.id)
            .values(title=title)
            )
        
        await self.session.commit()
        await self.session.refresh(thread)
        
        return thread
   
