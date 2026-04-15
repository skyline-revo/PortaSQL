"""Database helper tests."""

from __future__ import annotations

import json
import sqlite3

import pytest

from database import execute_query, get_stats, init_db, insert_document


def _sample_doc() -> dict:
    return {
        "source_type": "arxiv",
        "source_id": "1234.5678",
        "title": "Test Title",
        "authors": "Alice",
        "year": 2024,
        "published_date": "2024-01-01",
        "content": "Test abstract",
        "url": "https://arxiv.org/abs/1234.5678",
        "domain": "nlp",
        "method": "transformer",
        "math_topic": "optimization",
        "extra_metadata": {"foo": "bar"},
    }


def test_init_db_creates_table(tmp_path) -> None:
    """init_db creates documents table."""
    db_path = str(tmp_path / "test.db")
    init_db(db_path)

    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='documents'"
        ).fetchone()
    assert row is not None


def test_insert_document_valid(tmp_path) -> None:
    """insert_document stores valid data."""
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    assert insert_document(db_path, _sample_doc()) is True


def test_duplicate_rejection(tmp_path) -> None:
    """Duplicate source_type + source_id are ignored."""
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    assert insert_document(db_path, _sample_doc()) is True
    assert insert_document(db_path, _sample_doc()) is False


def test_execute_query_rejects_dangerous_sql(tmp_path) -> None:
    """execute_query rejects non-SELECT operations."""
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    with pytest.raises(ValueError):
        execute_query(db_path, "DELETE FROM documents")


def test_get_stats_counts(tmp_path) -> None:
    """get_stats returns counts by source and domain."""
    db_path = str(tmp_path / "test.db")
    init_db(db_path)

    first = _sample_doc()
    second = {**_sample_doc(), "source_id": "x2", "source_type": "openalex", "domain": "computer vision"}
    insert_document(db_path, first)
    insert_document(db_path, second)

    stats = get_stats(db_path)
    assert stats["total_documents"] == 2
    assert any(s["source_type"] == "arxiv" for s in stats["by_source"])


def test_extra_metadata_json_roundtrip(tmp_path) -> None:
    """extra_metadata is persisted as JSON string."""
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    insert_document(db_path, _sample_doc())

    rows = execute_query(db_path, "SELECT extra_metadata FROM documents")
    payload = json.loads(rows[0]["extra_metadata"])
    assert payload["foo"] == "bar"
