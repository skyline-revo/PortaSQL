"""Tests for portfolio-safe demo connector."""

from __future__ import annotations

from connectors.demo_connector import DemoConnector


def test_demo_connector_fetch_returns_records() -> None:
    """Demo connector returns local records with expected shape."""
    connector = DemoConnector({"name": "Demo", "connector": "demo"})
    rows = connector.fetch("transformer", 10)

    assert len(rows) >= 1
    sample = rows[0]
    assert sample.get("title")
    assert sample.get("source_id")
    assert sample.get("content")
