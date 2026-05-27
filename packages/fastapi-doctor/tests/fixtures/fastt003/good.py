from fastapi import FastAPI, Depends

app = FastAPI()


@app.get("/users")
async def get_users():
    result = await fetch_users()
    return result


@app.post("/users")
async def create_user():
    async with get_session() as session:
        return await session.execute()


@app.get("/items")
async def stream_items():
    async for item in stream():
        yield item


@app.delete("/users/{id}")
async def delete_user(id: int):
    return await db.delete(id)


@app.get("/sync")
def get_sync():
    return {"status": "ok"}
