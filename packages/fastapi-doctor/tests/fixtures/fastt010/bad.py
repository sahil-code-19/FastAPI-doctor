from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

app = FastAPI()


@app.get("/users")
async def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()


@app.get("/users/{id}")
async def get_user(id: int, db: Session = Depends(get_db)):
    return db.get(User, id)


@app.get("/search")
async def search_users(db: Session = Depends(get_db)):
    result = db.execute("SELECT * FROM users").scalars().all()
    return result


@app.get("/items/{id}")
async def get_item(id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == id).first()
    return item


@app.get("/sync-bad")
def sync_bad(db: Session = Depends(get_db)):
    return db.query(User).first()
