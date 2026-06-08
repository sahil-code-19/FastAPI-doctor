import uvicorn

from fastapi import FastAPI

# Pattern 1: FastAPI(debug=True)
app = FastAPI(debug=True)

# Pattern 1 variation: extra args + debug=True
api = FastAPI(title="My App", version="1.0", debug=True)

# Pattern 2: uvicorn.run(..., debug=True)
uvicorn.run("main:app", debug=True)

# Pattern 2 variation
uvicorn.run("main:app", host="0.0.0.0", port=8000, debug=True)
