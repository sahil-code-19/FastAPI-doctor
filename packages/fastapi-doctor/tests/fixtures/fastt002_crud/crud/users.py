from sqlalchemy.orm import Session


async def create_user(db: Session, name: str):
    """CRUD function called from router — sync DB calls should be flagged via trace."""
    db.execute("INSERT INTO users (name) VALUES (:name)", {"name": name})
    db.commit()
    return {"name": name}


async def create_user_correct(db: Session, name: str):
    """This one wraps DB in asyncio.to_thread — should NOT be flagged."""
    db.execute("INSERT INTO users (name) VALUES (:name)", {"name": name})
    db.commit()
    return {"name": name}
