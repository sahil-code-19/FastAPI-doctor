from fastapi import FastAPI, Depends
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession

app = FastAPI()


def get_db():
    """Sync session — not used in async endpoints here."""
    ...


async def get_async_db():
    """Async session generator."""
    ...


@app.get("/users")
async def get_users(db: AsyncSession = Depends(get_async_db)):
    """Correct: awaiting async session methods."""
    result = await db.execute("SELECT * FROM users")
    users = result.scalars().all()
    return {"users": users}


@app.post("/users")
async def create_user(db: AsyncSession = Depends(get_async_db)):
    """Correct: using await with async session."""
    await db.commit()
    return {"status": "created"}


@app.put("/users/{id}")
async def update_user(id: int):
    """Correct: sync DB call wrapped in asyncio.to_thread."""

    def sync_update():
        db = get_db()
        db.execute("UPDATE users SET name='test' WHERE id=:id", {"id": id})
        db.commit()

    await asyncio.to_thread(sync_update)
    return {"status": "updated"}


@app.delete("/users/{id}")
async def delete_user(id: int):
    """Correct: no DB calls at all."""
    return {"status": "deleted"}


@app.patch("/users/{id}")
async def patch_user(id: int, db: AsyncSession = Depends(get_async_db)):
    """Correct: AsyncSession methods called with await."""
    result = await db.execute("SELECT * FROM users WHERE id=:id", {"id": id})
    user = result.scalar()
    return {"user": user}
