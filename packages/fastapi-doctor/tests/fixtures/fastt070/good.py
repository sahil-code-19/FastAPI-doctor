from fastapi import FastAPI

app = FastAPI()


@app.get("/items")
async def get_items():
    """GET doesn't need explicit status_code."""
    return []


@app.post("/items", status_code=201)
async def create_item():
    """POST with explicit status_code."""
    return {}


@app.put("/items/{id}", status_code=200)
async def update_item(id: int):
    """PUT with explicit status_code."""
    return {}


@app.delete("/items/{id}", status_code=204)
async def delete_item(id: int):
    """DELETE with explicit status_code."""
    return None


@app.patch("/items/{id}", status_code=200)
async def patch_item(id: int):
    """PATCH with explicit status_code."""
    return {}
