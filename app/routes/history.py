from fastapi import APIRouter, HTTPException

from app import database
from app.schemas import ConversationRecord

router = APIRouter()


@router.get("/history", response_model=list[ConversationRecord])
def get_history(limit: int = 50):
    """Return recent conversations from MySQL, newest first. Returns [] if DB is offline."""
    try:
        return database.fetch_history(limit)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/history")
def clear_history():
    """Delete all conversation records. Returns status of the operation."""
    if not database.is_available() and not database._ensure_connected():
        return {"message": "Database not connected — nothing to clear", "deleted": 0}
    try:
        deleted = database.clear_history()
        return {"message": "History cleared", "deleted": deleted}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
