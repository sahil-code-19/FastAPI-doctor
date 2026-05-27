from fastapi import FastAPI
import httpx
import asyncio
from fastapi.concurrency import run_in_threadpool

app = FastAPI()


@app.get("/users")
async def get_users():
    """Correct: uses async HTTP client."""
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.example.com/users")
    return response.json()


@app.post("/users")
async def create_user():
    """Correct: blocking IO wrapped in asyncio.to_thread."""
    import requests

    response = await asyncio.to_thread(requests.get, "https://api.example.com/users")
    return response.json()


@app.put("/users/{id}")
async def update_user(id: int):
    """Correct: using run_in_threadpool."""
    import requests

    response = await run_in_threadpool(
        requests.get, f"https://api.example.com/users/{id}"
    )
    return response.json()


@app.delete("/users/{id}")
async def delete_user(id: int):
    """Correct: async sleep."""
    await asyncio.sleep(1)
    return {"status": "deleted"}


def sync_helper():
    """Sync helper - not an endpoint, not checked."""
    import requests

    return requests.get("https://api.example.com/data")
