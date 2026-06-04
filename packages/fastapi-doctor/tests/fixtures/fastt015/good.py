from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Secure: specific origins with credentials — OK
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://example.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# Secure: wildcard origins WITHOUT credentials — OK
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# Secure: credentials with specific origin list — OK
app.add_middleware(
    "CORSMiddleware",
    allow_origins=["https://app.com", "https://api.com"],
    allow_credentials=True,
)

# Secure: FastAPI with specific origins — OK
api = FastAPI(
    allow_origins=["https://secure.com"],
    allow_credentials=True,
)
