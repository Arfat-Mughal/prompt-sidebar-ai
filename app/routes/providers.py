from fastapi import APIRouter

from app.ai import available_providers

router = APIRouter()


@router.get("/providers")
def get_providers():
    """Return all providers that have an API key configured in .env"""
    return available_providers()
