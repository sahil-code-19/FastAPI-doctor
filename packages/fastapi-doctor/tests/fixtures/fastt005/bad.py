from fastapi import FastAPI
import json

app = FastAPI()


@app.get("/config")
async def get_config():
    with open("config.json") as f:
        data = json.load(f)
    return data


@app.get("/export")
async def export_data():
    f = open("export.csv", "w")
    f.write("header")
    f.close()
    return {"status": "ok"}


@app.post("/upload")
async def upload_file():
    data = json.load(open("data.json"))
    return {"count": len(data)}
