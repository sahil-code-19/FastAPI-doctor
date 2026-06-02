from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

app = FastAPI()


class UserResponse(BaseModel):
    id: int
    name: str


class TokenResponse(BaseModel):
    access_token: str


@app.get("/users/{id}", response_model=UserResponse)
async def get_user(id: int, db: Session = Depends(get_db)):
    user = db.query(User).first()
    return user


@app.post("/login", response_model=TokenResponse)
async def login(db: Session = Depends(get_db)):
    return {"access_token": "abc", "token_type": "bearer"}


@app.post("/items", response_model=None)
async def create_item(data: dict):
    return {"status": "ok", "id": 1}
