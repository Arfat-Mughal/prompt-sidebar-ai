# Prompt Sidebar — AI Chat Extension

A Chrome side-panel extension paired with a local FastAPI server that streams AI responses from multiple providers (NVIDIA, OpenRouter) and optionally persists conversations to MySQL.

---

## How it works

```
Chrome Extension (sidebar)
        │  POST /chat  (prompt + provider)
        ▼
FastAPI Server (port 8000)
        ├─ NVIDIA API   →  minimax-m2.7          (if NVIDIA_API_KEY set)
        └─ OpenRouter   →  tencent/hy3-preview    (if OPENROUTER_API_KEY set)
        │
        ▼
MySQL / XAMPP  (ai_extension.conversations)
   optional — chat works without it
```

1. You type a prompt in the browser sidebar and press **Send** (or `Ctrl+Enter`).
2. The extension posts the prompt to the local server along with the selected provider.
3. The server streams the AI response back token by token via Server-Sent Events.
4. Each completed conversation is saved to MySQL (if connected).
5. When you reopen the sidebar, the full chat history loads from the database.

---

## Features

- **Multi-provider** — switch between NVIDIA and OpenRouter from a dropdown in the sidebar. A provider only appears if its API key is set in `.env`.
- **Streaming responses** — tokens appear in real time with a blinking cursor.
- **Persistent history** — conversations survive browser/server restarts via MySQL.
- **Works without MySQL** — chat and streaming work fully offline from the database. History is simply not saved when MySQL is unavailable.
- **Auto-reconnect** — if MySQL starts after the server, it reconnects automatically on the next request.
- **DB status badge** — green `DB` in the header when connected, amber `No DB` when MySQL is offline.
- **Chat UI** — user and AI bubbles with timestamps in Chrome's native Side Panel.
- **Clear history** — wipes both the UI and the database in one click.

---

## Project structure

```
product/
├── app/
│   ├── config.py          # All settings loaded from .env
│   ├── database.py        # MySQL connection, auto-reconnect, queries
│   ├── schemas.py         # Pydantic request / response models
│   ├── ai.py              # Provider client factory (NVIDIA / OpenRouter)
│   ├── main.py            # FastAPI app, CORS, lifespan, health route
│   └── routes/
│       ├── chat.py        # POST /chat  — streams AI response
│       ├── history.py     # GET /history, DELETE /history
│       └── providers.py   # GET /providers — available AI providers
├── prompt-sidebar-extracted/
│   ├── manifest.json      # Chrome extension config (MV3)
│   ├── background.js      # Opens Side Panel on icon click
│   ├── sidebar.html       # Chat UI shell
│   ├── sidebar.css        # Styles
│   └── sidebar.js         # Fetch + SSE stream handler
├── server.py              # Entry point — runs uvicorn
├── requirements.txt
├── .env                   # Secret keys (never commit)
└── .env.example           # Safe template
```

---

## Requirements

| Tool | Version |
|------|---------|
| Python | 3.10+ |
| Chrome | 114+ (Side Panel API) |
| XAMPP | Any — optional (MySQL on port 3306) |

---

## Setup

### 1. Clone / open the project

```
cd product
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

| Variable | Required | Description |
|----------|----------|-------------|
| `NVIDIA_API_KEY` | Yes* | Your NVIDIA API key |
| `NVIDIA_BASE_URL` | No | API base URL (default provided) |
| `AI_MODEL` | No | Model ID (default: `minimaxai/minimax-m2.7`) |
| `OPENROUTER_API_KEY` | No | Your OpenRouter API key — leave blank to disable |
| `OPENROUTER_BASE_URL` | No | OpenRouter base URL (default provided) |
| `OPENROUTER_MODEL` | No | Model ID (default: `tencent/hy3-preview:free`) |
| `DB_HOST` | No | MySQL host (default: `localhost`) |
| `DB_PORT` | No | MySQL port (default: `3306`) |
| `DB_USER` | No | MySQL user (default: `root`) |
| `DB_PASSWORD` | No | MySQL password (default: empty for XAMPP) |
| `DB_NAME` | No | Database name (default: `ai_extension`) |

*At least one AI provider key is required.

### 4. Create the database (optional)

Skip this step if you don't need history persistence.

Open phpMyAdmin at `http://localhost/phpmyadmin` and run:

```sql
CREATE DATABASE IF NOT EXISTS ai_extension;
```

The `conversations` table is created automatically on first server start.

### 5. Start the server

```bash
python server.py
```

With MySQL running:
```
╔══════════════════════════════════════╗
║   Prompt Sidebar API  — port 8000    ║
║   Swagger docs → /docs               ║
╚══════════════════════════════════════╝
  ✓ MySQL connected  →  ai_extension.conversations
```

Without MySQL:
```
╔══════════════════════════════════════╗
║   Prompt Sidebar API  — port 8000    ║
║   Swagger docs → /docs               ║
╚══════════════════════════════════════╝
  ✗ MySQL unavailable — running without persistence
```

### 6. Load the Chrome extension

1. Go to `chrome://extensions/`
2. Enable **Developer mode** (top right)
3. Click **Load unpacked**
4. Select the `prompt-sidebar-extracted/` folder
5. Click the extension icon in the toolbar — the sidebar opens

---

## AI providers

| Provider | Env key | Default model |
|----------|---------|---------------|
| NVIDIA | `NVIDIA_API_KEY` | `minimaxai/minimax-m2.7` |
| OpenRouter | `OPENROUTER_API_KEY` | `tencent/hy3-preview:free` |

- If only one key is configured, no selector is shown — that provider is used automatically.
- If both keys are configured, a **Model** dropdown appears at the top of the sidebar.
- Both providers use the OpenAI-compatible streaming API.

---

## MySQL behaviour

| MySQL state | Chat | History saved | History loaded | Badge |
|-------------|------|--------------|----------------|-------|
| Running at startup | ✓ | ✓ | ✓ | `DB` green |
| Offline at startup, starts later | ✓ | ✓ auto-reconnects | ✓ | updates on next request |
| Never running | ✓ | ✗ silently skipped | Returns empty | `No DB` amber |
| Server unreachable | ✗ | ✗ | ✗ | `Offline` amber |

---

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/chat` | Send a prompt, receive a streaming SSE response |
| `GET` | `/providers` | List AI providers that have an API key configured |
| `GET` | `/history?limit=50` | Fetch recent conversations (newest first) |
| `DELETE` | `/history` | Clear all conversation records |
| `GET` | `/` | Health check + DB status |
| `GET` | `/docs` | Interactive Swagger UI |

### POST /chat — request body

```json
{
  "prompt":     "Explain async/await in Python",
  "char_count": 34,
  "timestamp":  "2026-05-07T12:00:00.000Z",
  "source_url": "https://example.com",
  "provider":   "nvidia"
}
```

`provider` defaults to `"nvidia"` if omitted. Use `"openrouter"` to route via OpenRouter.

---

## Database schema

```sql
CREATE TABLE conversations (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    prompt     TEXT         NOT NULL,
    response   LONGTEXT,
    source_url VARCHAR(2048),
    char_count INT          DEFAULT 0,
    created_at DATETIME     DEFAULT CURRENT_TIMESTAMP
);
```

---

## Keyboard shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl + Enter` | Send prompt |
| Click a history bubble | Load that prompt back into the input |

---

## Adding a new AI provider or model

1. Add the provider's base URL and API key to `.env`.
2. Add a new branch in `app/ai.py` → `get_client()`.
3. Register the provider in `available_providers()`.
4. Restart the server — the new option appears in the extension dropdown automatically.
