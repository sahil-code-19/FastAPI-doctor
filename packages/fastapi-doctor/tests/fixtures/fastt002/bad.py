from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

app = FastAPI()


def get_db():
    """Sync session generator."""
    db = Session()
    try:
        yield db
    finally:
        db.close()


@app.get("/users")
async def get_users(db: Session = Depends(get_db)):
    """BAD: db.execute() without await inside async endpoint."""
    result = db.execute("SELECT * FROM users")
    users = result.fetchall()
    return {"users": users}


@app.post("/users")
async def create_user(db: Session = Depends(get_db)):
    """BAD: db.flush() and db.commit() without await."""
    user = {"name": "test"}
    db.add(user)
    db.flush()
    db.commit()
    return {"status": "created"}


@app.put("/users/{id}")
async def update_user(id: int, db: Session = Depends(get_db)):
    """BAD: multiple sync DB calls."""
    db.query("SELECT * FROM users WHERE id=:id", {"id": id})
    db.execute("UPDATE users SET name='test' WHERE id=:id", {"id": id})
    db.commit()
    return {"status": "updated"}


@app.delete("/users/{id}")
async def delete_user(id: int, db: Session = Depends(get_db)):
    """BAD: db.delete() without await."""
    db.delete(id)
    db.commit()
    return {"status": "deleted"}
