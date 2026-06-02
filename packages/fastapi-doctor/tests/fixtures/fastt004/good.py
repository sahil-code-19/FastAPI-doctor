from fastapi import FastAPI
import asyncio

app = FastAPI()


@app.get("/users")
async def get_users():
    result = await fetch_users()
    return result


@app.post("/items")
async def create_item():
    return {"status": "created"}


j@app.get("/blocking")
def sync_endpoint():
    asyncio.run(sync_work())
    return {"status": "ok"}
