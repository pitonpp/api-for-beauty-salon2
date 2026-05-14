from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from app.api.routers import main_router
from app.core.initial_db import create_first_users
from app.core.db import AsyncSessionLocal


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    try:
        async with AsyncSessionLocal() as async_session:
            await create_first_users(async_session)
    except Exception:
        raise

    yield


app = FastAPI(lifespan=lifespan)
app.include_router(main_router)
