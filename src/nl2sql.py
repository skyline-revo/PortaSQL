"""Natural-language to SQL pipeline using Anthropic Claude."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any

from anthropic import Anthropic

from database import execute_query, get_schema_info


@dataclass(slots=True)
class NL2SQLResult:
    """Response object for NL2SQL flow."""

    question: str
    sql_query: str
    raw_results: list[dict[str, Any]]
    natural_language_answer: str


class NL2SQLService:
    """Convert NL questions to SQL and summarize results."""

    def __init__(self, db_path: str, model: str, api_key: str | None = None, client: Any | None = None) -> None:
        """Initialize NL2SQL service."""
        self.db_path = db_path
        self.model = model
        key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.client = client or (Anthropic(api_key=key) if key else None)

    def _build_sql_system_prompt(self) -> str:
        """Build strict SQL generation system prompt."""
        schema = get_schema_info(self.db_path)
        return (
            "You are a SQLite expert. Convert user questions into SQLite SELECT queries only.\n"
            "Rules:\n"
            "1) Output ONLY SQL. No markdown fences.\n"
            "2) Only SELECT statements are allowed.\n"
            "3) Never use DELETE, UPDATE, INSERT, DROP, ALTER, PRAGMA, ATTACH.\n"
            "4) Use exact column names from this schema:\n"
            f"{schema}\n"
            "5) Query the documents table only."
        )

    @staticmethod
    def extract_sql(text: str) -> str:
        """Extract SQL from Claude output, removing markdown fences if present."""
        stripped = text.strip()
        fenced = re.match(r"```(?:sql)?\s*(.*?)\s*```", stripped, flags=re.IGNORECASE | re.DOTALL)
        if fenced:
            stripped = fenced.group(1).strip()
        return stripped.rstrip(";")

    @staticmethod
    def _validate_select_only(sql: str) -> None:
        """Validate SQL is safe read-only SELECT."""
        normalized = sql.strip().lower()
        if not normalized.startswith("select"):
            raise ValueError("Generated SQL is not a SELECT statement")
        banned = ["delete", "update", "insert", "drop", "alter", "pragma", "attach"]
        if any(f" {kw} " in f" {normalized} " for kw in banned):
            raise ValueError("Generated SQL contains prohibited operation")

    def _call_claude(self, system_prompt: str, user_prompt: str) -> str:
        """Call Claude Messages API and return text output."""
        if not self.client:
            raise RuntimeError("Anthropic client is not configured. Set ANTHROPIC_API_KEY.")

        response = self.client.messages.create(
            model=self.model,
            max_tokens=600,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        parts = getattr(response, "content", [])
        text_parts = [p.text for p in parts if getattr(p, "type", "") == "text"]
        return "\n".join(text_parts).strip()

    def ask(self, question: str) -> NL2SQLResult:
        """Run full NL -> SQL -> DB -> NL answer pipeline."""
        sql_prompt = self._build_sql_system_prompt()

        try:
            raw_sql = self._call_claude(sql_prompt, question)
            sql_query = self.extract_sql(raw_sql)
            self._validate_select_only(sql_query)
            results = execute_query(self.db_path, sql_query)
        except Exception as exc:
            return NL2SQLResult(
                question=question,
                sql_query="",
                raw_results=[],
                natural_language_answer=f"I couldn't execute that request safely: {exc}",
            )

        if not results:
            return NL2SQLResult(
                question=question,
                sql_query=sql_query,
                raw_results=[],
                natural_language_answer="I ran the query successfully, but there were no matching results.",
            )

        answer_prompt = (
            "Summarize these SQL results for the user in plain English with concise bullet points.\n"
            f"Question: {question}\n"
            f"SQL: {sql_query}\n"
            f"Results: {results[:20]}"
        )

        try:
            answer = self._call_claude("You are a helpful data analyst.", answer_prompt)
        except Exception:
            answer = f"Found {len(results)} rows."

        return NL2SQLResult(
            question=question,
            sql_query=sql_query,
            raw_results=results,
            natural_language_answer=answer,
        )
