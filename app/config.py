import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    # ── AI (NVIDIA) ───────────────────────────────────────────
    nvidia_api_key:  str   = os.getenv("NVIDIA_API_KEY", "")
    nvidia_base_url: str   = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
    ai_model:        str   = os.getenv("AI_MODEL", "minimaxai/minimax-m2.7")

    # ── AI (OpenRouter) ───────────────────────────────────────
    openrouter_api_key:  str = os.getenv("OPENROUTER_API_KEY", "")
    openrouter_base_url: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    openrouter_model:    str = os.getenv("OPENROUTER_MODEL", "tencent/hy3-preview:free")

    # ── Shared AI params ──────────────────────────────────────
    ai_temperature: float = 1.0
    ai_top_p:       float = 0.95
    ai_max_tokens:  int   = 8192

    # ── MySQL ─────────────────────────────────────────────────
    db_host:     str = os.getenv("DB_HOST", "localhost")
    db_port:     int = int(os.getenv("DB_PORT", "3306"))
    db_user:     str = os.getenv("DB_USER", "root")
    db_password: str = os.getenv("DB_PASSWORD", "")
    db_name:     str = os.getenv("DB_NAME", "ai_extension")


settings = Settings()
