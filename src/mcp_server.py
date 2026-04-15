"""MCP-compatible JSON-RPC server over stdin/stdout."""

from __future__ import annotations

import json
import sys
from typing import Any

from config import AppConfig, load_config
from database import execute_query, get_stats
from nl2sql import NL2SQLService


class MCPServer:
    """Minimal MCP JSON-RPC server exposing retrieval tools."""

    def __init__(self, config: AppConfig) -> None:
        """Initialize server from app config."""
        self.config = config
        self.nl2sql = NL2SQLService(db_path=config.database_path, model=config.llm_model)

    def tools(self) -> list[dict[str, Any]]:
        """Return tool descriptors."""
        return [
            {"name": "query", "description": "Natural language question over the documents database"},
            {"name": "stats", "description": "Database statistics"},
            {"name": "search", "description": "Keyword search across titles"},
            {"name": "sources", "description": "List configured data sources"},
        ]

    def _search_titles(self, keyword: str) -> list[dict[str, Any]]:
        """Run keyword search across titles safely."""
        escaped = keyword.replace("'", "''")
        sql = (
            "SELECT id, title, source_type, year, url FROM documents "
            f"WHERE title LIKE '%{escaped}%' ORDER BY year DESC, id DESC LIMIT 50"
        )
        return execute_query(self.config.database_path, sql)

    def handle_tool_call(self, name: str, arguments: dict[str, Any]) -> Any:
        """Dispatch tool call."""
        if name == "query":
            question = str(arguments.get("question", "")).strip()
            if not question:
                raise ValueError("'question' is required")
            result = self.nl2sql.ask(question)
            return {
                "question": result.question,
                "sql_query": result.sql_query,
                "raw_results": result.raw_results,
                "natural_language_answer": result.natural_language_answer,
            }

        if name == "stats":
            return get_stats(self.config.database_path)

        if name == "search":
            keyword = str(arguments.get("keyword", "")).strip()
            if not keyword:
                raise ValueError("'keyword' is required")
            return self._search_titles(keyword)

        if name == "sources":
            return [
                {
                    "name": s.name,
                    "connector": s.connector,
                    "queries": s.queries,
                    "max_results_per_query": s.max_results_per_query,
                }
                for s in self.config.sources
            ]

        raise ValueError(f"Unknown tool: {name}")

    def handle_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """Handle one JSON-RPC request object."""
        request_id = request.get("id")
        method = request.get("method")
        params = request.get("params") or {}

        try:
            if method == "initialize":
                result = {
                    "protocolVersion": "2025-03-26",
                    "serverInfo": {"name": "llm-knowledge-retrieval", "version": "0.1.0"},
                    "capabilities": {"tools": {}},
                }
            elif method == "tools/list":
                result = {"tools": self.tools()}
            elif method == "tools/call":
                name = params.get("name")
                arguments = params.get("arguments") or {}
                if not name:
                    raise ValueError("Missing tool name")
                result = {"content": [{"type": "text", "text": json.dumps(self.handle_tool_call(name, arguments))}]}
            else:
                raise ValueError(f"Unknown method: {method}")

            return {"jsonrpc": "2.0", "id": request_id, "result": result}
        except Exception as exc:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32000, "message": str(exc)},
            }


def run_stdio_server(config_path: str | None = None) -> None:
    """Run the MCP server loop over stdin/stdout."""
    config = load_config(config_path)
    server = MCPServer(config)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            response = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}
        else:
            response = server.handle_request(request)
        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    run_stdio_server()
