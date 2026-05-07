# Contributing to Prompt Sidebar

Thanks for your interest in improving this project! Whether it's a bug fix, a new AI provider, UI polish, or a feature idea — all contributions are welcome.

---

## Ways to contribute

- **Add a new AI provider** — OpenAI, Anthropic, Gemini, Mistral, etc.
- **Improve the chat UI** — markdown rendering, code highlighting, copy button
- **Add conversation context** — send previous messages so the AI has memory
- **Export history** — download conversations as JSON / Markdown
- **Settings panel** — temperature, max tokens, system prompt configurable from the sidebar
- **Auth / multi-user** — protect the API with a token
- **Bug fixes and performance improvements**

---

## Dev setup

### 1. Fork and clone

```bash
git clone https://github.com/Arfat-Mughal/prompt-sidebar-ai.git
cd prompt-sidebar-ai
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Fill in at least one AI provider key
```

### 4. Start the server

```bash
python server.py
```

### 5. Load the extension in Chrome

1. Go to `chrome://extensions/`
2. Enable **Developer mode**
3. Click **Load unpacked** → select `prompt-sidebar-extracted/`

---

## Project layout

```
app/
├── ai.py            ← Add new providers here
├── config.py        ← Add new env variables here
├── database.py      ← All SQL lives here
├── schemas.py       ← Pydantic models
└── routes/
    ├── chat.py      ← Streaming endpoint
    ├── history.py   ← History CRUD
    └── providers.py ← Provider list endpoint

prompt-sidebar-extracted/
├── sidebar.js       ← All extension logic
├── sidebar.html     ← UI structure
└── sidebar.css      ← Styles
```

---

## Adding a new AI provider

1. Add keys to `.env.example` (never commit real keys):
   ```
   NEWPROVIDER_API_KEY=your_key_here
   NEWPROVIDER_BASE_URL=https://api.newprovider.com/v1
   NEWPROVIDER_MODEL=model-name
   ```

2. Add settings to `app/config.py`:
   ```python
   newprovider_api_key:  str = os.getenv("NEWPROVIDER_API_KEY", "")
   newprovider_base_url: str = os.getenv("NEWPROVIDER_BASE_URL", "...")
   newprovider_model:    str = os.getenv("NEWPROVIDER_MODEL", "...")
   ```

3. Register in `app/ai.py` — add a branch in `get_client()` and an entry in `available_providers()`.

4. Restart the server — the new option appears in the extension dropdown automatically.

---

## Submitting a pull request

1. Create a branch: `git checkout -b feature/your-feature-name`
2. Make your changes and test them
3. Commit with a clear message
4. Push and open a PR against `master`
5. Describe what you changed and why in the PR description

---

## Code style

- **Python** — follow PEP 8, use type hints, keep functions small and focused
- **JavaScript** — ES2020+, no build step, keep it vanilla
- **No comments** explaining what the code does — use clear names instead
- **No unused files** — remove anything that isn't referenced

---

## Questions?

Open an issue on GitHub and tag it `question`.
