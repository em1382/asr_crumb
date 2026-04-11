from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.agent import configure as configure_agent
from app.api.main import api_router
from app.core.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Cannot use DI here because it's not a FastAPI dependency
    configure_agent(get_settings())
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(api_router, prefix=get_settings().api_v1_str)


@app.get("/")
async def read_root():
    """Root endpoint."""
    return {"status": "200 OK"}
