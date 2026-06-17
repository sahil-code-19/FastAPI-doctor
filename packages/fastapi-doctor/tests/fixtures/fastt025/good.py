from fastapi import FastAPI
from contextlib import asynccontextmanager

app = FastAPI()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


api = FastAPI(lifespan=lifespan)


@app.get("/users")
async def get_users():
    return {"users": []}
