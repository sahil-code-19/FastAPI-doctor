from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from crud.users import create_user, create_user_correct

app = FastAPI()


@app.post("/users")
async def create_user_endpoint(db: Session = Depends(lambda: Session())):
    """Calls create_user from CRUD — trace should find db.execute() inside."""
    return await create_user(db, "test")


@app.put("/users")
async def update_user_endpoint(db: Session = Depends(lambda: Session())):
    """Calls create_user_correct from CRUD — has to_thread, should not flag."""
    import asyncio

    return await asyncio.to_thread(create_user_correct, db, "test")
