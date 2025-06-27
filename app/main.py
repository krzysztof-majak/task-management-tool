import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from app.api.v1 import projects, tasks
from app.config import setup_logging
from app.database import Base, engine
from app.routes import health, meta

setup_logging()

logger = logging.getLogger("project-api")


async def init_models() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await init_models()
    yield


app = FastAPI(lifespan=lifespan, title="Task Management Tool")

app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(meta.router, prefix="", tags=["Meta"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["Projects"])
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["Tasks"])
