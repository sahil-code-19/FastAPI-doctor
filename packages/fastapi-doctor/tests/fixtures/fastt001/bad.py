from fastapi import FastAPI
import requests
import httpx
import time

app = FastAPI()


@app.get("/users")
async def get_users():
    """BAD: requests.get() inside async endpoint."""
    response = requests.get("https://api.example.com/users")
    return response.json()


@app.post("/users")
async def create_user():
    """BAD: requests.post() inside async endpoint."""
    response = requests.post("https://api.example.com/users", json={"name": "John"})
    return response.json()


@app.put("/users/{id}")
async def update_user(id: int):
    """BAD: time.sleep() inside async endpoint."""
    time.sleep(2)
    return {"status": "updated"}


@app.delete("/users/{id}")
async def delete_user(id: int):
    """BAD: sync httpx.get() inside async endpoint."""
    response = httpx.get(f"https://api.example.com/users/{id}")
    return response.json()


@app.head("/health")
async def health_check():
    """BAD: requests.head() inside async endpoint."""
    response = requests.head("https://api.example.com/health")
    return {"status": "ok"}
