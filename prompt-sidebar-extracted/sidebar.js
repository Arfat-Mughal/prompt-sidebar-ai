const CHAT_URL    = 'http://localhost:8000/chat';
const HISTORY_URL = 'http://localhost:8000/history';

document.addEventListener('DOMContentLoaded', () => {
  const textarea     = document.getElementById('promptInput');
  const sendBtn      = document.getElementById('sendBtn');
  const clearBtn     = document.getElementById('clearBtn');
  const clearAllBtn  = document.getElementById('clearAllBtn');
  const chatMessages = document.getElementById('chatMessages');
  const emptyState   = document.getElementById('emptyState');
  const charCountEl  = document.getElementById('charCount');
  const toast        = document.getElementById('toast');

  let toastTimer  = null;
  let isStreaming = false;

  // ── Boot ─────────────────────────────────────────────────
  loadHistory();
  textarea.focus();

  // ── Input events ─────────────────────────────────────────
  textarea.addEventListener('input', () => {
    charCountEl.textContent = textarea.value.length;
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
  });

  textarea.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      sendPrompt();
    }
  });

  sendBtn.addEventListener('click', sendPrompt);

  clearBtn.addEventListener('click', () => {
    textarea.value = '';
    charCountEl.textContent = '0';
    textarea.style.height = '';
    textarea.focus();
  });

  clearAllBtn.addEventListener('click', async () => {
    if (!confirm('Clear all chat history?')) return;
    try {
      await fetch('http://localhost:8000/history', { method: 'DELETE' });
    } catch (_) {}
    chatMessages.innerHTML = '';
    showEmptyState();
  });

  // ── Load history from MySQL ───────────────────────────────
  async function loadHistory() {
    try {
      const res = await fetch(HISTORY_URL + '?limit=30');
      if (!res.ok) return;
      const rows = await res.json();
      if (!rows.length) { showEmptyState(); return; }

      hideEmptyState();
      // rows are newest-first; render oldest-first
      rows.slice().reverse().forEach((row) => {
        appendUserBubble(row.prompt, row.created_at);
        if (row.response) appendAiBubble(row.response);
      });
      scrollToBottom();
    } catch (_) {
      showEmptyState();
    }
  }

  // ── Send ─────────────────────────────────────────────────
  async function sendPrompt() {
    const prompt = textarea.value.trim();
    if (!prompt || isStreaming) return;

    isStreaming = true;
    sendBtn.disabled = true;
    hideEmptyState();

    appendUserBubble(prompt);

    textarea.value = '';
    charCountEl.textContent = '0';
    textarea.style.height = '';

    const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
    const sourceUrl = tabs[0]?.url ?? '';

    const payload = {
      prompt,
      char_count: prompt.length,
      timestamp:  new Date().toISOString(),
      source_url: sourceUrl,
    };

    const aiBubble = appendStreamingAiBubble();

    try {
      await streamChat(payload, (token) => {
        aiBubble.appendToken(token);
        scrollToBottom();
      });
      aiBubble.finalize();
    } catch (err) {
      aiBubble.finalize('⚠ Server offline. Make sure it is running on port 8000.');
      aiBubble.el.classList.add('error');
      showToast('Server offline');
    }

    isStreaming = false;
    sendBtn.disabled = false;
    textarea.focus();
  }

  // ── SSE streaming fetch ───────────────────────────────────
  async function streamChat(payload, onToken) {
    const response = await fetch(CHAT_URL, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(payload),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);

    const reader  = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer    = '';

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop();

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        const data = line.slice(6);
        if (data === '[DONE]') return;
        try { onToken(JSON.parse(data)); } catch { onToken(data); }
      }
    }
  }

  // ── DOM helpers ───────────────────────────────────────────
  function appendUserBubble(text, timestamp) {
    const wrap   = document.createElement('div');
    wrap.className = 'msg-row msg-row--user';

    const bubble = document.createElement('div');
    bubble.className = 'msg-bubble msg-bubble--user';
    bubble.textContent = text;

    if (timestamp) {
      const ts = document.createElement('span');
      ts.className = 'msg-ts';
      ts.textContent = formatTs(timestamp);
      bubble.appendChild(ts);
    }

    wrap.appendChild(bubble);
    chatMessages.appendChild(wrap);
    return bubble;
  }

  // Used when rendering history (full text already known)
  function appendAiBubble(text) {
    const wrap   = document.createElement('div');
    wrap.className = 'msg-row msg-row--ai';

    const avatar = document.createElement('div');
    avatar.className = 'ai-avatar';
    avatar.textContent = 'AI';

    const bubble = document.createElement('div');
    bubble.className = 'msg-bubble msg-bubble--ai';
    bubble.textContent = text;

    wrap.appendChild(avatar);
    wrap.appendChild(bubble);
    chatMessages.appendChild(wrap);
    return bubble;
  }

  // Used for live streaming — returns a controller object
  function appendStreamingAiBubble() {
    const wrap   = document.createElement('div');
    wrap.className = 'msg-row msg-row--ai';

    const avatar = document.createElement('div');
    avatar.className = 'ai-avatar';
    avatar.textContent = 'AI';

    const bubble = document.createElement('div');
    bubble.className = 'msg-bubble msg-bubble--ai';

    const cursor = document.createElement('span');
    cursor.className = 'stream-cursor';
    bubble.appendChild(cursor);

    wrap.appendChild(avatar);
    wrap.appendChild(bubble);
    chatMessages.appendChild(wrap);

    let accumulated = '';

    return {
      el: bubble,
      appendToken(token) {
        accumulated += token;
        bubble.textContent = accumulated;
        bubble.appendChild(cursor);
      },
      finalize(overrideText) {
        cursor.remove();
        if (overrideText !== undefined) bubble.textContent = overrideText;
      },
    };
  }

  function showEmptyState() {
    if (!document.getElementById('emptyState')) {
      chatMessages.appendChild(emptyState);
    }
    emptyState.style.display = '';
  }

  function hideEmptyState() {
    emptyState.style.display = 'none';
  }

  function scrollToBottom() {
    const main = document.getElementById('mainArea');
    main.scrollTop = main.scrollHeight;
  }

  function formatTs(iso) {
    try {
      return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch { return ''; }
  }

  function showToast(message) {
    toast.textContent = message;
    toast.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove('show'), 2500);
  }
});
