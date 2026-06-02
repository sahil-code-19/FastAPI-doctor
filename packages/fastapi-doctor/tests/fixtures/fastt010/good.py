from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

app = FastAPI()


class UserSchema(BaseModel):
    id: int
    name: str


@app.get("/users/{id}")
async def get_user(id: int, db: Session = Depends(get_db)):
    user = db.query(User).first()
    return UserSchema.model_validate(user)


@app.get("/items")
def get_items(db: Session = Depends(get_db)):
    return {"items": ["a", "b"]}


@app.post("/users")
async def create_user(db: Session = Depends(get_db)):
    return {"status": "created"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/items/{id}")
async def get_item(id: int, db: Session = Depends(get_db)):
    item = db.get(Item, id)
    return ItemSchema.model_validate(item) if item else None


@app.get("/sync-ok")
def sync_read(db: Session = Depends(get_db)):
    user = db.query(User).first()
    return {"name": user.name}
