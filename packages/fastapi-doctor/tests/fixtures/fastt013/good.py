import os
from app.core.config import settings

APP_NAME = "job-board"
VERSION = "0.1.0"
MAX_UPLOAD_SIZE = 5 * 1024 * 1024
DEBUG = "true"
PAGE_SIZE = "20"

SECRET_KEY = os.environ.get("SECRET_KEY")
API_KEY = os.getenv("API_KEY")
DATABASE_URL = settings.DATABASE_URL

if settings.DEBUG:
    print("Debug mode")
