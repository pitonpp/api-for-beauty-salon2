from fastapi import FastAPI
from app.endpoints.test import router

app = FastAPI()
app.include_router(router)
