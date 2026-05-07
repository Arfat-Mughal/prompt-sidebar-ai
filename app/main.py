import logging
import logging.handlers
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import database
from app.routes import chat, history, providers

Path("logs").mkdir(exist_ok=True)
_file_handler = logging.handlers.RotatingFileHandler(
    "logs/chat.log", maxBytes=10 * 1024 * 1024, backupCount=3, encoding="utf-8"
)
_file_handler.setFormatter(logging.Formatter("%(message)s"))
logging.getLogger("app").addHandler(_file_handler)
logging.getLogger("app").setLevel(logging.DEBUG)


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db()
    yield


app = FastAPI(
    title="Prompt Sidebar API",
    description="Streams AI responses and persists conversations to MySQL.",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(history.router)
app.include_router(providers.router)


@app.get("/")
def health():
    db_up = database.is_available()
    return {
        "status":      "running",
        "db":          "connected" if db_up else "unavailable",
        "db_message":  "History is being saved." if db_up else "MySQL offline — chat works, history will not be saved.",
        "docs":        "http://localhost:8000/docs",
    }
