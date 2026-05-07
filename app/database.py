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
    )


# ── State ─────────────────────────────────────────────────────────────────────

_db_available: bool = False


def is_available() -> bool:
    return _db_available


# ── Init ──────────────────────────────────────────────────────────────────────

def init_db() -> None:
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
        print("  ✓ MySQL connected  →  ai_extension.conversations")
    except Exception as exc:
        print(f"  ✗ MySQL unavailable ({exc}) — running without persistence")


# ── Queries ───────────────────────────────────────────────────────────────────

def save_conversation(
    prompt: str,
    response: str,
    source_url: str,
    char_count: int,
) -> None:
    if not _db_available:
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
    if not _db_available:
        return []
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


def clear_history() -> int:
    if not _db_available:
        return 0
    conn = get_connection()
    with conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM conversations")
            affected = cur.rowcount
        conn.commit()
    return affected
