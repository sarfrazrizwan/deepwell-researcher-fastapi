from fastapi import FastAPI
from app.api.routes import messages, auth 

from app.core.lifespan import lifespan

app = FastAPI(lifespan=lifespan)


# @app.get("/")
# def read_root():
#     return {"Hello": "World"}


# @app.get("/items/{item_id}")
# def read_item(item_id: int, q: str | None = None):
#     return {"item_id": item_id, "q": q}

app.include_router(auth.router)
app.include_router(messages.router)
