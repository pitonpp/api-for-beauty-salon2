from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from app.api.routers import main_router
from app.core.db import AsyncSessionLocal
from app.core.initial_db import create_first_users

# from app.rabbitmq.connection import rabbitmq_connection_manager
# from app.rabbitmq.consumer import rabbitmq_consumer
from app.core.logger import setup_logging


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Управляет жизненным циклом приложения."""
    # await rabbitmq_connection_manager.connect()
    # await rabbitmq_connection_manager.connect()

    try:
        setup_logging()
        async with AsyncSessionLocal() as async_session:
            await create_first_users(async_session)
    except Exception:
        raise

    yield
    # await rabbitmq_connection_manager.close()


app = FastAPI(lifespan=lifespan)
app.include_router(main_router)
