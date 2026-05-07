import pymysql
import pymysql.cursors

from app.config import settings

# ── Connection factory ────────────────────────────────────────────────────────

def get_connection() -> pymysql.connections.Connection:
    return pymysql.connect(
        host=settings.db_host,
        port=settings.db_port,
        user=settings.db_user,
        password=settings.db_password,
        database=settings.db_name,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
        connect_timeout=3,
    )


# ── State ─────────────────────────────────────────────────────────────────────

_db_available: bool = False


def is_available() -> bool:
    return _db_available


# ── Init / reconnect ──────────────────────────────────────────────────────────

def init_db() -> bool:
    """Create table if needed. Called on startup and on-demand when offline."""
    global _db_available
    try:
        conn = get_connection()
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS conversations (
                        id         INT AUTO_INCREMENT PRIMARY KEY,
                        prompt     TEXT        NOT NULL,
                        response   LONGTEXT,
                        source_url VARCHAR(2048),
                        char_count INT          DEFAULT 0,
                        created_at DATETIME     DEFAULT CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)
            conn.commit()
        _db_available = True
        return True
    except Exception as exc:
        _db_available = False
        return False


def _ensure_connected() -> bool:
    """Return True if DB is ready. Auto-reconnects if it was previously offline."""
    if _db_available:
        return True
    connected = init_db()
    if connected:
        print("  ✓ MySQL reconnected  →  ai_extension.conversations")
    return connected


# ── Queries ───────────────────────────────────────────────────────────────────

def save_conversation(
    prompt: str,
    response: str,
    source_url: str,
    char_count: int,
) -> None:
    if not _ensure_connected():
        return
    try:
        conn = get_connection()
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO conversations
                           (prompt, response, source_url, char_count)
                       VALUES (%s, %s, %s, %s)""",
                    (prompt, response, source_url or "", char_count),
                )
            conn.commit()
    except Exception as exc:
        print(f"  DB write error: {exc}")


def fetch_history(limit: int = 50) -> list[dict]:
    if not _ensure_connected():
        return []
    try:
        conn = get_connection()
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT id, prompt, response, source_url, char_count,
                              DATE_FORMAT(created_at, '%%Y-%%m-%%dT%%H:%%i:%%s') AS created_at
                         FROM conversations
                        ORDER BY id DESC
                        LIMIT %s""",
                    (limit,),
                )
                return cur.fetchall()
    except Exception as exc:
        print(f"  DB read error: {exc}")
        return []


def clear_history() -> int:
    if not _ensure_connected():
        return 0
    try:
        conn = get_connection()
        with conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM conversations")
                affected = cur.rowcount
            conn.commit()
        return affected
    except Exception as exc:
        print(f"  DB clear error: {exc}")
        return 0
