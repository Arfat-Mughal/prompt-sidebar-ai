from openai import OpenAI
from fastapi import HTTPException

from app.config import settings


def get_client(provider: str) -> tuple[OpenAI, str]:
    """Return (OpenAI-compatible client, model name) for the given provider."""
    if provider == "openrouter":
        if not settings.openrouter_api_key:
            raise HTTPException(status_code=400, detail="OpenRouter API key not configured")
        return OpenAI(
            base_url=settings.openrouter_base_url,
            api_key=settings.openrouter_api_key,
        ), settings.openrouter_model

    # default: nvidia
    if not settings.nvidia_api_key:
        raise HTTPException(status_code=400, detail="NVIDIA API key not configured")
    return OpenAI(
        base_url=settings.nvidia_base_url,
        api_key=settings.nvidia_api_key,
    ), settings.ai_model


def available_providers() -> list[dict]:
    """Return providers that have an API key configured."""
    providers = []
    if settings.nvidia_api_key:
        providers.append({
            "id":    "nvidia",
            "name":  "NVIDIA",
            "model": settings.ai_model,
        })
    if settings.openrouter_api_key:
        providers.append({
            "id":    "openrouter",
            "name":  "OpenRouter",
            "model": settings.openrouter_model,
        })
    return providers
