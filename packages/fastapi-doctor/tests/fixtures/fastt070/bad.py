from fastapi import FastAPI

app = FastAPI()


@app.post("/items")
async def create_item():
    """Missing status_code."""
    return {}


@app.put("/items/{id}")
async def update_item(id: int):
    """Missing status_code."""
    return {}


@app.delete("/items/{id}")
async def delete_item(id: int):
    """Missing status_code."""
    return None


@app.patch("/items/{id}")
async def patch_item(id: int):
    """Missing status_code."""
    return {}
