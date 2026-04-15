"""Base connector interface for external APIs."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseConnector(ABC):
    """Abstract base class for all API connectors."""

    def __init__(self, source_config: dict[str, Any], global_config: dict[str, Any] | None = None) -> None:
        """Initialize connector with source-specific and global configuration."""
        self.source_config = source_config
        self.global_config = global_config or {}

    @abstractmethod
    def fetch(self, query: str, max_results: int) -> list[dict[str, Any]]:
        """Fetch records from the underlying source for a given query."""

    @abstractmethod
    def get_source_name(self) -> str:
        """Return the canonical source type name (e.g. arxiv, openalex)."""
