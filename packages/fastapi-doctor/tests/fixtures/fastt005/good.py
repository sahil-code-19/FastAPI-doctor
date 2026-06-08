import anyio
from fastapi import FastAPI
import asyncio

app = FastAPI()


@app.get("/users")
async def get_users():
    result = await fetch_users()
    return result


@app.get("/config")
async def get_config():
    async with anyio.open_file("config.json") as f:
        data = await f.read()
    return {"config": data}


@app.get("/export")
async def export_data():
    def write_file():
        with open("export.json", "w") as f:
            f.write("data")

    await asyncio.to_thread(write_file)
    return {"status": "ok"}


@app.get("/sync")
def sync_read():
    with open("data.txt") as f:
        return f.read()
