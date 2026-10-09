from fastapi import FastAPI
from app.api.routes import messages
from app.config import get_settings
from contextlib import asynccontextmanager
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.postgres.aio import AsyncPostgresStore
from app.core.lifespan import lifespan

app = FastAPI(lifespan=lifespan)


# @app.get("/")
# def read_root():
#     return {"Hello": "World"}


# @app.get("/items/{item_id}")
# def read_item(item_id: int, q: str | None = None):
#     return {"item_id": item_id, "q": q}

app.include_router(messages.router)
