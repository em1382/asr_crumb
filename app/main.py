from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from app.core.config import get_settings

import app.agent as agent


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    agent.configure(settings)
    yield


app = FastAPI(lifespan=lifespan)


@app.websocket("/ingest")
async def websocket_json(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            message: Any = await websocket.receive_json()
            # await websocket.send_json({"ok": True, "received": message})
    except WebSocketDisconnect:
        pass


@app.get("/")
async def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}


@app.post("/recipe")
async def ingest_recipe(recipe: dict):
    recommendations = agent.get_recipe_recommendations(recipe)
    return recommendations
