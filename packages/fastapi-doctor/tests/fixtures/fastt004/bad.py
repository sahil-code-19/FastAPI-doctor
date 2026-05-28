from fastapi import FastAPI, Depends
import asyncio

app = FastAPI()


async def fetch_data():
    return {"data": [1, 2, 3]}


@app.get("/users")
async def get_users():
    result = asyncio.run(fetch_data())
    return result


@app.put("/items/{id}")
async def update_item(id: int):
    async def helper():
        asyncio.run(something())

    await helper()
    return {"status": "updated"}

@app.get("/items")
async def get_items():
    return asyncio.run(fetch_data())
