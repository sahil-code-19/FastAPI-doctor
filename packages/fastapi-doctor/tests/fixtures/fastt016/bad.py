from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# FastAPI without HTTPSRedirectMiddleware — MISSING
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["Content-Type"],
)
