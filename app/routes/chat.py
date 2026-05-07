import json
import logging
import re
from datetime import datetime, timezone

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app import database
from app.ai import get_client
from app.config import settings
from app.schemas import PromptPayload

router = APIRouter()
logger = logging.getLogger(__name__)

_PAGE_TOOL = {
    "type": "function",
    "function": {
        "name": "get_page_content",
        "description": (
            "Returns the cleaned HTML of the web page the user is currently viewing. "
            "Call this when the user's question is about the current page, its content, "
            "or anything visible on screen."
        ),
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
}


_NOISE_BLOCKS = re.compile(
    r'<(script|style|svg|template|noscript|iframe|canvas|picture|video|audio'
    r'|nav|header|footer|aside|dialog|details|button|form)'
    r'[^>]*>.*?</\1>',
    re.DOTALL | re.IGNORECASE,
)
# self-closing / void noise elements
_VOID_NOISE  = re.compile(r'<(?:link|meta|source|input|br|hr|img)\b[^>]*/?>',  re.IGNORECASE)
# custom web-component tags (hyphenated) — strip as pass-through wrappers
_CUSTOM_TAGS = re.compile(r'</?[a-z][\w]*-[\w-]+[^>]*>', re.IGNORECASE)
_COMMENTS    = re.compile(r'<!--.*?-->',  re.DOTALL)
_ATTRS       = re.compile(r'<([a-zA-Z][a-zA-Z0-9]*)\s[^>]*?(/?)>')
_EMPTY_TAG   = re.compile(r'<([a-zA-Z][a-zA-Z0-9]*)>\s*</\1>')
_WHITESPACE  = re.compile(r'\s+')


def _clean_page_html(raw: str) -> str:
    html = _NOISE_BLOCKS.sub('', raw)    # remove block noise + all content inside
    html = _VOID_NOISE.sub('', html)     # remove void noise elements
    html = _CUSTOM_TAGS.sub('', html)    # strip custom element wrappers (keep inner text)
    html = _COMMENTS.sub('', html)       # remove <!-- comments -->
    html = _ATTRS.sub(r'<\1\2>', html)   # strip all remaining tag attributes
    prev = None                          # collapse empty tags until stable
    while prev != html:
        prev = html
        html = _EMPTY_TAG.sub('', html)
    html = _WHITESPACE.sub(' ', html).strip()
    return html


def _log_page_capture(payload: "PromptPayload", cleaned: str) -> None:
    sep = "═" * 60
    ts  = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    raw_preview = (payload.page_html[:3000] + "\n…(truncated)") if len(payload.page_html) > 3000 else payload.page_html
    logger.debug(
        "\n%s\n"
        "CHAT  %s\n"
        "URL   : %s\n"
        "Prompt: %s\n"
        "Raw HTML  : %s chars  |  Cleaned: %s chars\n"
        "\n── document.body.innerHTML (raw, first 3 000 chars) ──\n%s\n"
        "\n── Cleaned HTML (sent to AI) ──\n%s\n"
        "%s\n",
        sep, ts,
        payload.source_url or "(unknown)",
        payload.prompt[:300],
        f"{len(payload.page_html):,}", f"{len(cleaned):,}",
        raw_preview,
        cleaned,
        sep,
    )


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
    if payload.page_html:
        print(f"  Page  : {len(payload.page_html):,} chars available (tool-gated)")
    print(sep)
    print(f"  {payload.prompt}")
    print(f"{sep}\n")

    user_messages = [{"role": "user", "content": payload.prompt}]

    def _stream_completion(messages, tokens):
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
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

    def generate():
        tokens: list[str] = []
        try:
            if payload.page_html:
                # Pass 1 — non-streaming: let AI decide whether it needs the page
                first = client.chat.completions.create(
                    model=model,
                    messages=user_messages,
                    tools=[_PAGE_TOOL],
                    tool_choice="auto",
                    temperature=settings.ai_temperature,
                    top_p=settings.ai_top_p,
                    max_tokens=settings.ai_max_tokens,
                    stream=False,
                )
                choice = first.choices[0]

                if choice.finish_reason == "tool_calls":
                    # AI called get_page_content — clean HTML, log it, then stream Pass 2
                    print(f"  [tool] get_page_content called — providing cleaned HTML")
                    cleaned = _clean_page_html(payload.page_html)
                    _log_page_capture(payload, cleaned)

                    tc = choice.message.tool_calls[0]
                    messages_with_tool = user_messages + [
                        {
                            "role": "assistant",
                            "content": choice.message.content,
                            "tool_calls": [{
                                "id": tc.id,
                                "type": "function",
                                "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                            }],
                        },
                        {
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": cleaned,
                        },
                    ]
                    yield from _stream_completion(messages_with_tool, tokens)

                else:
                    # AI answered directly — no page context needed; emit as single chunk
                    print(f"  [tool] get_page_content not called — answered directly")
                    text = choice.message.content or ""
                    tokens.append(text)
                    yield f"data: {json.dumps(text)}\n\n"

            else:
                # No page HTML available — stream directly
                yield from _stream_completion(user_messages, tokens)

        except Exception:
            # Tool calling not supported by model — fall back to direct streaming
            logger.exception("Tool-call pass failed, falling back to direct stream")
            yield from _stream_completion(user_messages, tokens)

        finally:
            database.save_conversation(
                prompt=payload.prompt,
                response="".join(tokens),
                source_url=payload.source_url or "",
                char_count=payload.char_count,
            )
            yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
