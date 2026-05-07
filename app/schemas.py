from typing import Optional
from pydantic import BaseModel


class PromptPayload(BaseModel):
    prompt:     str
    char_count: int
    timestamp:  str
    source_url: Optional[str] = ""
    provider:   Optional[str] = "nvidia"


class ConversationRecord(BaseModel):
    id:         int
    prompt:     str
    response:   Optional[str] = ""
    source_url: Optional[str] = ""
    char_count: Optional[int] = 0
    created_at: str
