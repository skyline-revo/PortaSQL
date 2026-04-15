"""OpenAlex connector implementation."""

from __future__ import annotations

from typing import Any

import requests

from connectors.base import BaseConnector


class OpenAlexConnector(BaseConnector):
    """Fetch documents from OpenAlex works endpoint."""

    BASE_URL = "https://api.openalex.org/works"

    def get_source_name(self) -> str:
        """Return source name."""
        return "openalex"

    def fetch(self, query: str, max_results: int) -> list[dict[str, Any]]:
        """Fetch OpenAlex works for a query."""
        email = self.source_config.get("polite_email") or self.global_config.get("polite_email")
        params = {
            "search": query,
            "per-page": max_results,
            "mailto": email,
        }
        params = {k: v for k, v in params.items() if v}

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            payload = response.json()
        except Exception:
            return []

        items = payload.get("results", [])
        docs: list[dict[str, Any]] = []

        for item in items:
            authorships = item.get("authorships") or []
            authors = ", ".join(
                a.get("author", {}).get("display_name", "")
                for a in authorships
                if a.get("author", {}).get("display_name")
            )
            abstract = self._reconstruct_abstract(item.get("abstract_inverted_index"))
            topics = [c.get("display_name") for c in (item.get("concepts") or []) if c.get("display_name")]
            doi = item.get("doi")
            source_id = doi or item.get("id")

            docs.append(
                {
                    "title": item.get("display_name"),
                    "authors": authors,
                    "year": item.get("publication_year"),
                    "published_date": item.get("publication_date"),
                    "abstract": abstract,
                    "content": abstract,
                    "source_name": "OpenAlex",
                    "source_id": source_id,
                    "doi": doi,
                    "url": item.get("primary_location", {}).get("landing_page_url") or item.get("id"),
                    "cited_by_count": item.get("cited_by_count"),
                    "topics": topics,
                }
            )

        return docs

    @staticmethod
    def _reconstruct_abstract(index: dict[str, list[int]] | None) -> str | None:
        """Reconstruct abstract text from OpenAlex inverted index format."""
        if not index:
            return None

        positions: dict[int, str] = {}
        for word, idxs in index.items():
            for i in idxs:
                positions[i] = word

        return " ".join(positions[i] for i in sorted(positions)) if positions else None
