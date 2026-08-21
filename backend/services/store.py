import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4
from config import settings

def _connect() -> sqlite3.Connection:
    path: Path = settings.sqlite_path
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS items (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                title TEXT NOT NULL,
                source TEXT,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()

def create_item(item_type: str,title: str,content: str,source: str | None,item_id: str | None = None) -> dict[str, Any]:
    item = {
        "id": item_id or str(uuid4()),
        "type": item_type,
        "title": title,
        "source": source,
        "content": content,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO items (id, type, title, source, content, created_at)
            VALUES (:id, :type, :title, :source, :content, :created_at)
            """,
            item,
        )
        conn.commit()
    return item

def list_items() -> list[dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, type, title, source, content, created_at FROM items ORDER BY created_at DESC"
        ).fetchall()
    items = []
    for row in rows:
        data = dict(row)
        data["preview"] = _preview(data.pop("content"))
        items.append(data)
    return items

def item_exists(item_id: str) -> bool:
    with _connect() as conn:
        row = conn.execute("SELECT 1 FROM items WHERE id = ?", (item_id,)).fetchone()
    return row is not None

def delete_item(item_id: str) -> bool:
    with _connect() as conn:
        cursor = conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
        conn.commit()
        return cursor.rowcount > 0

def _preview(content: str, limit: int = 180) -> str:
    collapsed = " ".join(content.split())
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[: limit - 1] + "…"