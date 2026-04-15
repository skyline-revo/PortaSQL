"""arXiv connector implementation."""

from __future__ import annotations

from typing import Any

import arxiv

from connectors.base import BaseConnector


METHOD_KEYWORDS = {
    "transformer": "transformer",
    "diffusion": "diffusion",
    "reinforcement learning": "reinforcement learning",
    "rl": "reinforcement learning",
    "bayesian": "bayesian",
    "graph neural": "graph neural network",
    "cnn": "convolutional neural network",
    "convolution": "convolutional neural network",
}

MATH_KEYWORDS = {
    "optimization": "optimization",
    "convex": "optimization",
    "probability": "probability",
    "statistical": "statistics",
    "statistics": "statistics",
    "linear algebra": "linear algebra",
    "differential": "differential equations",
}

DOMAIN_KEYWORDS = {
    "vision": "computer vision",
    "image": "computer vision",
    "language": "nlp",
    "text": "nlp",
    "robot": "robotics",
    "medical": "healthcare",
    "finance": "finance",
    "climate": "climate",
    "quantum": "quantum computing",
}


class ArxivConnector(BaseConnector):
    """Fetch documents from the arXiv API."""

    def get_source_name(self) -> str:
        """Return source name."""
        return "arxiv"

    def fetch(self, query: str, max_results: int) -> list[dict[str, Any]]:
        """Fetch arXiv results and normalize connector-level fields."""
        try:
            search = arxiv.Search(query=query, max_results=max_results, sort_by=arxiv.SortCriterion.SubmittedDate)
            client = arxiv.Client()
            results: list[dict[str, Any]] = []

            for paper in client.results(search):
                combined = f"{paper.title} {paper.summary}".lower()
                method, math_topic, domain = self._autotag(combined)

                results.append(
                    {
                        "title": paper.title,
                        "authors": ", ".join(author.name for author in paper.authors),
                        "year": paper.published.year if paper.published else None,
                        "published_date": paper.published.date().isoformat() if paper.published else None,
                        "abstract": paper.summary,
                        "content": paper.summary,
                        "source_name": "arXiv",
                        "source_id": paper.entry_id.rsplit("/", 1)[-1] if paper.entry_id else None,
                        "arxiv_id": paper.entry_id.rsplit("/", 1)[-1] if paper.entry_id else None,
                        "url": paper.entry_id,
                        "primary_category": paper.primary_category,
                        "domain": domain,
                        "method": method,
                        "math_topic": math_topic,
                    }
                )

            return results
        except Exception:
            return []

    @staticmethod
    def _autotag(text: str) -> tuple[str | None, str | None, str | None]:
        """Tag method, math topic, and domain using keyword heuristics."""
        method = next((v for k, v in METHOD_KEYWORDS.items() if k in text), None)
        math_topic = next((v for k, v in MATH_KEYWORDS.items() if k in text), None)
        domain = next((v for k, v in DOMAIN_KEYWORDS.items() if k in text), None)
        return method, math_topic, domain
