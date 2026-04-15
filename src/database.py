"""SQLite database schema and helper functions."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS documents (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source_type TEXT NOT NULL,
  source_id TEXT,
  title TEXT NOT NULL,
  authors TEXT,
  year INTEGER,
  published_date TEXT,
  content TEXT,
  url TEXT,
  domain TEXT,
  method TEXT,
  math_topic TEXT,
  extra_metadata TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(source_type, source_id)
);
"""


def init_db(db_path: str) -> None:
    """Initialize database and schema."""
    path = Path(db_path)
    if path.parent and str(path.parent) != ".":
        path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as conn:
        conn.execute(SCHEMA_SQL)
        conn.commit()


def _connect(db_path: str) -> sqlite3.Connection:
    """Create sqlite connection with Row factory."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def insert_document(db_path: str, document: dict[str, Any]) -> bool:
    """Insert a normalized document row. Returns True if inserted."""
    metadata = document.get("extra_metadata")
    if metadata is not None and not isinstance(metadata, str):
        metadata = json.dumps(metadata, ensure_ascii=True)

    sql = """
    INSERT OR IGNORE INTO documents (
      source_type, source_id, title, authors, year, published_date, content,
      url, domain, method, math_topic, extra_metadata
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    values = (
        document.get("source_type"),
        document.get("source_id"),
        document.get("title"),
        document.get("authors"),
        document.get("year"),
        document.get("published_date"),
        document.get("content"),
        document.get("url"),
        document.get("domain"),
        document.get("method"),
        document.get("math_topic"),
        metadata,
    )

    with _connect(db_path) as conn:
        cur = conn.execute(sql, values)
        conn.commit()
        return cur.rowcount > 0


def execute_query(db_path: str, sql: str) -> list[dict[str, Any]]:
    """Execute safe read-only SQL and return list of dict rows."""
    normalized = sql.strip().lower()
    if not normalized.startswith("select"):
        raise ValueError("Only SELECT queries are allowed")

    banned = ["delete", "update", "insert", "drop", "alter", "pragma", "attach"]
    if any(f" {kw} " in f" {normalized} " for kw in banned):
        raise ValueError("Dangerous SQL operation detected")

    with _connect(db_path) as conn:
        rows = conn.execute(sql).fetchall()
    return [dict(row) for row in rows]


def get_schema_info(db_path: str) -> str:
    """Return schema details for the documents table."""
    with _connect(db_path) as conn:
        rows = conn.execute("PRAGMA table_info(documents)").fetchall()

    lines = ["documents table columns:"]
    for row in rows:
        not_null = " NOT NULL" if row[3] else ""
        lines.append(f"- {row[1]} {row[2]}{not_null}")
    return "\n".join(lines)


def get_stats(db_path: str) -> dict[str, Any]:
    """Return aggregate database statistics."""
    with _connect(db_path) as conn:
        total = conn.execute("SELECT COUNT(*) AS c FROM documents").fetchone()["c"]
        by_source = conn.execute(
            "SELECT source_type, COUNT(*) AS c FROM documents GROUP BY source_type ORDER BY c DESC"
        ).fetchall()
        by_domain = conn.execute(
            "SELECT COALESCE(domain, 'unknown') AS domain, COUNT(*) AS c "
            "FROM documents GROUP BY COALESCE(domain, 'unknown') ORDER BY c DESC"
        ).fetchall()

    return {
        "total_documents": total,
        "by_source": [dict(r) for r in by_source],
        "by_domain": [dict(r) for r in by_domain],
    }
