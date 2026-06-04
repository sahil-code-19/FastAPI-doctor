import os
import uvicorn

from fastapi import FastAPI

app = FastAPI()

# FastAPI without debug=True — OK
api = FastAPI(title="My App")

# debug controlled by env — OK
debug_mode = os.getenv("DEBUG", "false").lower() == "true"
app2 = FastAPI(debug=debug_mode)

# uvicorn.run without debug — OK
uvicorn.run("main:app")

# uvicorn.run with debug=False — OK
uvicorn.run("main:app", debug=False)
