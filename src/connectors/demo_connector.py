"""Demo connector that reads bundled local records for portfolio-safe runs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from connectors.base import BaseConnector


class DemoConnector(BaseConnector):
    """Load records from `demo/sample_documents.json` with simple query filtering."""

    def get_source_name(self) -> str:
        """Return source name."""
        return "demo"

    def fetch(self, query: str, max_results: int) -> list[dict[str, Any]]:
        """Return local sample records matching the query string."""
        root = Path(__file__).resolve().parents[2]
        sample_path = root / "demo" / "sample_documents.json"
        if not sample_path.exists():
            return []

        with sample_path.open("r", encoding="utf-8") as f:
            rows = json.load(f)

        needle = query.strip().lower()
        if not needle:
            subset = rows
        else:
            subset = [
                row
                for row in rows
                if needle in (row.get("title", "").lower() + " " + row.get("abstract", "").lower())
            ]

        docs: list[dict[str, Any]] = []
        for row in subset[:max_results]:
            docs.append(
                {
                    "title": row.get("title"),
                    "authors": row.get("authors"),
                    "year": row.get("year"),
                    "published_date": row.get("published_date"),
                    "abstract": row.get("abstract"),
                    "content": row.get("abstract"),
                    "source_name": "DemoDataset",
                    "source_id": row.get("source_id"),
                    "url": row.get("url"),
                    "domain": row.get("domain"),
                    "method": row.get("method"),
                    "math_topic": row.get("math_topic"),
                }
            )
        return docs
