from fastapi import FastAPI

app = FastAPI()


@app.get("/users")
async def get_users():
    return {"users": []}


@app.post("/users")
async def create_user(data: dict):
    result = create_in_db(data)
    return result


@app.put("/users/{id}")
async def update_user(id: int, data: dict):
    update_in_db(id, data)
    return {"status": "ok"}
