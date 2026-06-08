from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CRITICAL: wildcard + credentials via CORSMiddleware class
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
)

# CRITICAL: wildcard + credentials via string middleware
app.add_middleware(
    "CORSMiddleware",
    allow_origins=["*"],
    allow_credentials=True,
)

# CRITICAL: wildcard + credentials via FastAPI params
api = FastAPI(
    allow_origins=["*"],
    allow_credentials=True,
)
