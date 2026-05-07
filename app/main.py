from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import database
from app.routes import chat, history


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


@app.get("/")
def health():
    return {
        "status": "running",
        "db":     "connected" if database.is_available() else "unavailable",
        "docs":   "http://localhost:8000/docs",
    }
