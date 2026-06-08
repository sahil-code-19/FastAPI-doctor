from fastapi import FastAPI
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.cors import CORSMiddleware

# FastAPI with HTTPSRedirectMiddleware — OK
app = FastAPI()
app.add_middleware(HTTPSRedirectMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://example.com"],
)

# FastAPI with HTTPSRedirectMiddleware as string — OK
api = FastAPI()
api.add_middleware("HTTPSRedirectMiddleware")
