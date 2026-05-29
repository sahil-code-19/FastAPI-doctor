from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

app = FastAPI()


@app.post("/login", response_model=None)
async def login(db: Session = Depends(get_db)):
    return {"access_token": "abc123", "token_type": "bearer"}


@app.get("/users/{id}", response_model=None)
async def get_user(id: int, db: Session = Depends(get_db)):
    user = db.query(User).first()
    return user


@app.get("/config", response_model=None)
async def get_config():
    return {"secret_key": "sk-abc123", "api_key": "key-xyz"}
