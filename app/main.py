from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from app.api.main import api_router
import app.core.config as config

import app.agent as agent


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Cannot use DI here because it's not a FastAPI dependency
    settings = config.get_settings()
    agent.configure(settings)
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(api_router, prefix=config.get_settings().api_v1_str)


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
    return {"status": "200 OK"}


@app.post("/recipe")
async def ingest_recipe(recipe: dict):
    recommendations = agent.get_recipe_recommendations(recipe)
    return recommendations
