"""Connector unit and integration tests."""

from __future__ import annotations

import os

import pytest

from connectors.arxiv_connector import ArxivConnector
from connectors.base import BaseConnector
from connectors.newsapi_connector import NewsapiConnector
from connectors.openalex_connector import OpenAlexConnector


class DummyConnector(BaseConnector):
    """Concrete test connector for interface checks."""

    def fetch(self, query: str, max_results: int) -> list[dict]:
        return []

    def get_source_name(self) -> str:
        return "dummy"


def test_base_connector_interface_enforced() -> None:
    """Ensure abstract interface requires methods."""

    class BadConnector(BaseConnector):
        pass

    with pytest.raises(TypeError):
        BadConnector({})  # type: ignore[abstract]

    assert DummyConnector({}).get_source_name() == "dummy"


def test_arxiv_connector_fields(mocker: pytest_mock.MockerFixture) -> None:
    """arXiv connector returns expected keys."""
    fake_paper = mocker.Mock()
    fake_paper.title = "Transformer optimization"
    fake_paper.summary = "A paper about optimization and language models"
    fake_paper.authors = [mocker.Mock(name="Alice")]
    fake_paper.authors[0].name = "Alice"
    fake_paper.published = mocker.Mock()
    fake_paper.published.year = 2024
    fake_paper.published.date.return_value.isoformat.return_value = "2024-01-01"
    fake_paper.entry_id = "http://arxiv.org/abs/1234.5678"
    fake_paper.primary_category = "cs.LG"

    client = mocker.Mock()
    client.results.return_value = [fake_paper]
    mocker.patch("connectors.arxiv_connector.arxiv.Client", return_value=client)

    connector = ArxivConnector({"name": "x", "connector": "arxiv"})
    rows = connector.fetch("ml", 1)
    assert len(rows) == 1
    assert {"title", "authors", "year", "published_date", "abstract", "arxiv_id", "url", "primary_category"}.issubset(
        rows[0].keys()
    )


def test_openalex_connector_fields(mocker: pytest_mock.MockerFixture) -> None:
    """OpenAlex connector returns expected keys."""
    mock_resp = mocker.Mock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {
        "results": [
            {
                "display_name": "Test Work",
                "authorships": [{"author": {"display_name": "Bob"}}],
                "publication_year": 2023,
                "publication_date": "2023-02-01",
                "abstract_inverted_index": {"hello": [0], "world": [1]},
                "doi": "https://doi.org/10.1000/test",
                "id": "https://openalex.org/W1",
                "primary_location": {"landing_page_url": "https://example.org/paper"},
                "cited_by_count": 10,
                "concepts": [{"display_name": "AI"}],
            }
        ]
    }
    mocker.patch("connectors.openalex_connector.requests.get", return_value=mock_resp)

    connector = OpenAlexConnector({"name": "x", "connector": "openalex"})
    rows = connector.fetch("ai", 1)
    assert len(rows) == 1
    assert {"title", "authors", "year", "abstract", "doi", "url", "cited_by_count", "topics"}.issubset(rows[0].keys())


def test_newsapi_connector_fields(mocker: pytest_mock.MockerFixture) -> None:
    """NewsAPI connector returns expected keys."""
    mock_resp = mocker.Mock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {
        "articles": [
            {
                "title": "AI in healthcare",
                "author": "Jane",
                "publishedAt": "2025-01-01T00:00:00Z",
                "description": "desc",
                "content": "content",
                "url": "https://news.test/1",
                "source": {"name": "Tech Daily"},
            }
        ]
    }
    mocker.patch("connectors.newsapi_connector.requests.get", return_value=mock_resp)

    connector = NewsapiConnector({"name": "x", "connector": "newsapi", "api_key": "k"})
    rows = connector.fetch("ai", 1)
    assert len(rows) == 1
    assert {"title", "author", "published_date", "description", "source_name", "url"}.issubset(rows[0].keys())


def test_connector_api_errors_graceful(mocker: pytest_mock.MockerFixture) -> None:
    """Connectors should return empty list on API failures."""
    mocker.patch("connectors.openalex_connector.requests.get", side_effect=RuntimeError("boom"))
    assert OpenAlexConnector({"name": "x", "connector": "openalex"}).fetch("q", 1) == []


@pytest.mark.integration
def test_arxiv_integration() -> None:
    """Optional arXiv integration test."""
    if os.getenv("RUN_INTEGRATION") != "1":
        pytest.skip("Set RUN_INTEGRATION=1 to run integration tests")
    rows = ArxivConnector({"name": "x", "connector": "arxiv"}).fetch("machine learning", 1)
    assert isinstance(rows, list)


@pytest.mark.integration
def test_openalex_integration() -> None:
    """Optional OpenAlex integration test."""
    if os.getenv("RUN_INTEGRATION") != "1":
        pytest.skip("Set RUN_INTEGRATION=1 to run integration tests")
    rows = OpenAlexConnector({"name": "x", "connector": "openalex"}).fetch("machine learning", 1)
    assert isinstance(rows, list)


@pytest.mark.integration
def test_newsapi_integration() -> None:
    """Optional NewsAPI integration test."""
    key = os.getenv("NEWSAPI_KEY")
    if os.getenv("RUN_INTEGRATION") != "1" or not key:
        pytest.skip("Set RUN_INTEGRATION=1 and NEWSAPI_KEY to run integration tests")
    rows = NewsapiConnector({"name": "x", "connector": "newsapi", "api_key": key}).fetch("ai", 1)
    assert isinstance(rows, list)
