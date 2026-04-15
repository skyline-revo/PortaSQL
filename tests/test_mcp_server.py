"""MCP server tests."""

from __future__ import annotations

import json

from config import AppConfig, SourceConfig
from database import init_db, insert_document
from mcp_server import MCPServer


class FakeNL2SQL:
    """Mock NL2SQL service."""

    def ask(self, question: str):
        class R:
            pass

        r = R()
        r.question = question
        r.sql_query = "SELECT 1"
        r.raw_results = [{"x": 1}]
        r.natural_language_answer = "answer"
        return r


def _config(path: str) -> AppConfig:
    return AppConfig(
        project_name="x",
        database_path=path,
        llm_model="claude-sonnet-4-20250514",
        polite_email=None,
        sources=[SourceConfig(name="S", connector="arxiv", queries=["ml"], max_results_per_query=5)],
    )


def _seed(path: str) -> None:
    init_db(path)
    insert_document(
        path,
        {
            "source_type": "arxiv",
            "source_id": "1",
            "title": "Transformer paper",
            "authors": "Alice",
            "year": 2024,
            "published_date": "2024-01-01",
            "content": "abc",
            "url": "https://example",
            "domain": "nlp",
            "method": "transformer",
            "math_topic": "optimization",
            "extra_metadata": {},
        },
    )


def test_initialize_handshake(tmp_path) -> None:
    """JSON-RPC initialize returns capabilities."""
    db = str(tmp_path / "db.sqlite")
    _seed(db)
    server = MCPServer(_config(db))
    resp = server.handle_request({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    assert "result" in resp
    assert resp["result"]["capabilities"]["tools"] == {}


def test_tools_list(tmp_path) -> None:
    """tools/list returns expected tool names."""
    db = str(tmp_path / "db.sqlite")
    _seed(db)
    server = MCPServer(_config(db))
    resp = server.handle_request({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}})
    names = [t["name"] for t in resp["result"]["tools"]]
    assert set(names) == {"query", "stats", "search", "sources"}


def test_each_tool_call(tmp_path) -> None:
    """All tools can be called successfully."""
    db = str(tmp_path / "db.sqlite")
    _seed(db)
    server = MCPServer(_config(db))
    server.nl2sql = FakeNL2SQL()

    q = server.handle_request(
        {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "query", "arguments": {"question": "x"}}}
    )
    assert "answer" in q["result"]["content"][0]["text"]

    s = server.handle_request({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "stats", "arguments": {}}})
    assert "total_documents" in s["result"]["content"][0]["text"]

    se = server.handle_request(
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "search", "arguments": {"keyword": "Transformer"}}}
    )
    parsed = json.loads(se["result"]["content"][0]["text"])
    assert len(parsed) >= 1

    so = server.handle_request({"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "sources", "arguments": {}}})
    parsed_sources = json.loads(so["result"]["content"][0]["text"])
    assert parsed_sources[0]["connector"] == "arxiv"


def test_invalid_tool_name(tmp_path) -> None:
    """Unknown tools return JSON-RPC error."""
    db = str(tmp_path / "db.sqlite")
    _seed(db)
    server = MCPServer(_config(db))
    resp = server.handle_request(
        {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "nope", "arguments": {}}}
    )
    assert "error" in resp
