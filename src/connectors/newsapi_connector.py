"""NewsAPI connector implementation."""

from __future__ import annotations

from typing import Any

import requests

from connectors.base import BaseConnector


class NewsapiConnector(BaseConnector):
    """Fetch articles from NewsAPI as a non-academic source example."""

    BASE_URL = "https://newsapi.org/v2/everything"

    def get_source_name(self) -> str:
        """Return source name."""
        return "newsapi"

    def fetch(self, query: str, max_results: int) -> list[dict[str, Any]]:
        """Fetch NewsAPI articles."""
        api_key = self.source_config.get("api_key")
        if not api_key:
            return []

        params = {
            "q": query,
            "pageSize": max_results,
            "sortBy": "publishedAt",
            "language": "en",
            "apiKey": api_key,
        }

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            payload = response.json()
        except Exception:
            return []

        docs: list[dict[str, Any]] = []
        for article in payload.get("articles", []):
            source_name = (article.get("source") or {}).get("name")
            docs.append(
                {
                    "title": article.get("title"),
                    "authors": article.get("author"),
                    "author": article.get("author"),
                    "year": (article.get("publishedAt") or "")[:4] or None,
                    "published_date": article.get("publishedAt"),
                    "description": article.get("description"),
                    "content": article.get("content") or article.get("description"),
                    "source_name": source_name,
                    "source_id": article.get("url"),
                    "url": article.get("url"),
                }
            )

        return docs
