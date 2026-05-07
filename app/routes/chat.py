import json
from datetime import datetime, timezone

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app import database
from app.ai import get_client
from app.config import settings
from app.schemas import PromptPayload

router = APIRouter()


@router.post("/chat")
def chat(payload: PromptPayload):
    """Stream an AI response via SSE and persist the conversation to MySQL."""
    provider = payload.provider or "nvidia"
    client, model = get_client(provider)

    sep = "─" * 54
    print(f"\n{sep}")
    print(f"  CHAT  [{provider.upper()}]  {datetime.now(timezone.utc).isoformat()}")
    print(f"  Model : {model}")
    print(f"  From  : {payload.source_url or '(unknown)'}")
    print(sep)
    print(f"  {payload.prompt}")
    print(f"{sep}\n")

    def generate():
        tokens: list[str] = []
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": payload.prompt}],
                temperature=settings.ai_temperature,
                top_p=settings.ai_top_p,
                max_tokens=settings.ai_max_tokens,
                stream=True,
            )
            for chunk in completion:
                if not getattr(chunk, "choices", None):
                    continue
                delta = chunk.choices[0].delta.content
                if delta is not None:
                    tokens.append(delta)
                    yield f"data: {json.dumps(delta)}\n\n"
        finally:
            database.save_conversation(
                prompt=payload.prompt,
                response="".join(tokens),
                source_url=payload.source_url or "",
                char_count=payload.char_count,
            )
            yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
