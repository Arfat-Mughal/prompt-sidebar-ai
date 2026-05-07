from fastapi import APIRouter, HTTPException

from app import database
from app.schemas import ConversationRecord

router = APIRouter()


@router.get("/history", response_model=list[ConversationRecord])
def get_history(limit: int = 50):
    """Return recent conversations from MySQL, newest first."""
    try:
        return database.fetch_history(limit)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/history")
def clear_history():
    """Delete all conversation records from MySQL."""
    try:
        deleted = database.clear_history()
        return {"message": "History cleared", "deleted": deleted}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
