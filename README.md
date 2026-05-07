# Prompt Sidebar — AI Chat Extension

A Chrome side-panel extension paired with a local FastAPI server that streams AI responses powered by NVIDIA's model API and persists every conversation to a MySQL database.

---

## How it works

```
Chrome Extension (sidebar)
        │  POST /chat  (prompt)
        ▼
FastAPI Server (port 8000)
        │  OpenAI-compatible stream
        ▼
NVIDIA API  →  minimax-m2.7
        │
        ▼
MySQL / XAMPP  (ai_extension.conversations)
```

1. You type a prompt in the browser sidebar and press **Send** (or `Ctrl+Enter`).
2. The extension posts the prompt to the local server.
3. The server streams the AI response back token by token via Server-Sent Events.
4. Each completed conversation is saved to MySQL.
5. When you reopen the sidebar, the full chat history loads from the database.

---

## Features

- **Streaming responses** — tokens appear in real time with a blinking cursor.
- **Persistent history** — conversations survive browser/server restarts via MySQL.
- **Chat UI** — user and AI bubbles with timestamps in Chrome's native Side Panel.
- **Clear history** — wipes both the UI and the database in one click.
- **Offline-safe** — server gracefully starts without MySQL if XAMPP is not running.

---

## Project structure

```
product/
├── app/
│   ├── config.py          # All settings loaded from .env
│   ├── database.py        # MySQL connection, queries
│   ├── schemas.py         # Pydantic request / response models
│   ├── main.py            # FastAPI app, CORS, lifespan
│   └── routes/
│       ├── chat.py        # POST /chat  — streams AI response
│       └── history.py     # GET /history, DELETE /history
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
| XAMPP | Any (MySQL on port 3306) |

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

| Variable | Description |
|----------|-------------|
| `NVIDIA_API_KEY` | Your NVIDIA API key |
| `NVIDIA_BASE_URL` | API base URL (default provided) |
| `AI_MODEL` | Model ID (default: `minimaxai/minimax-m2.7`) |
| `DB_HOST` | MySQL host (default: `localhost`) |
| `DB_PORT` | MySQL port (default: `3306`) |
| `DB_USER` | MySQL user (default: `root`) |
| `DB_PASSWORD` | MySQL password (default: empty for XAMPP) |
| `DB_NAME` | Database name (default: `ai_extension`) |

### 4. Create the database

Open phpMyAdmin at `http://localhost/phpmyadmin` and run:

```sql
CREATE DATABASE IF NOT EXISTS ai_extension;
```

The `conversations` table is created automatically on first server start.

### 5. Start the server

```bash
python server.py
```

Expected output:
```
╔══════════════════════════════════════╗
║   Prompt Sidebar API  — port 8000    ║
║   Swagger docs → /docs               ║
╚══════════════════════════════════════╝
  ✓ MySQL connected  →  ai_extension.conversations
```

### 6. Load the Chrome extension

1. Go to `chrome://extensions/`
2. Enable **Developer mode** (top right)
3. Click **Load unpacked**
4. Select the `prompt-sidebar-extracted/` folder
5. Click the extension icon in the toolbar — the sidebar opens

---

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/chat` | Send a prompt, receive a streaming SSE response |
| `GET` | `/history?limit=50` | Fetch recent conversations (newest first) |
| `DELETE` | `/history` | Clear all conversation records |
| `GET` | `/` | Health check + DB status |
| `GET` | `/docs` | Interactive Swagger UI |

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
| Click history bubble | Load prompt back into input |

---

## Adding a new AI model

1. Update `AI_MODEL` in `.env` to any model supported by the NVIDIA API.
2. Restart the server — no code changes needed.
