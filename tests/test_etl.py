"""ETL tests with mocked connectors."""

from __future__ import annotations

from config import AppConfig, SourceConfig
from etl import normalize_record, run_etl


class MockConnector:
    """Mock connector returning deterministic rows."""

    def __init__(self, source_config, global_config) -> None:
        self.source_config = source_config

    def fetch(self, query: str, max_results: int):
        return [
            {
                "title": f"Transformer optimization for {query}",
                "authors": "A. Author",
                "year": 2024,
                "published_date": "2024-01-01",
                "abstract": "language model optimization",
                "source_id": f"{query}-id",
                "url": f"https://example.com/{query}",
            }
        ]


def _config(db_path: str) -> AppConfig:
    return AppConfig(
        project_name="x",
        database_path=db_path,
        llm_model="claude-sonnet-4-20250514",
        polite_email=None,
        sources=[
            SourceConfig(
                name="A", connector="arxiv", queries=["nlp"], max_results_per_query=5
            ),
            SourceConfig(
                name="B", connector="openalex", queries=["vision"], max_results_per_query=5
            ),
        ],
    )


def test_transform_autotags_method() -> None:
    """Normalize assigns method tag."""
    row = normalize_record("arxiv", {"title": "Transformer models", "content": "x", "source_id": "1"})
    assert row["method"] == "transformer"


def test_transform_autotags_math_topic() -> None:
    """Normalize assigns math topic tag."""
    row = normalize_record("arxiv", {"title": "Convex optimization", "content": "x", "source_id": "1"})
    assert row["math_topic"] == "optimization"


def test_transform_maps_domain() -> None:
    """Normalize assigns domain tag."""
    row = normalize_record("arxiv", {"title": "Vision transformers", "content": "image", "source_id": "1"})
    assert row["domain"] == "computer vision"


def test_etl_with_mocked_connectors(tmp_path, mocker) -> None:
    """ETL runs end-to-end with mocked dynamic connector loading."""
    cfg = _config(str(tmp_path / "test.db"))
    mocker.patch("etl.load_connector_class", return_value=MockConnector)

    summary = run_etl(cfg, verbose=False)
    assert summary["inserted_total"] == 2
    assert summary["records_per_source"]["arxiv"] == 1


def test_source_filter_works(tmp_path, mocker) -> None:
    """--source-like filtering only runs selected source."""
    cfg = _config(str(tmp_path / "test.db"))
    mocker.patch("etl.load_connector_class", return_value=MockConnector)

    summary = run_etl(cfg, source_filter=["arxiv"], verbose=False)
    assert summary["inserted_total"] == 1
    assert summary["sources_used"] == ["arxiv"]


def test_ad_hoc_query_works(tmp_path, mocker) -> None:
    """--query-like ad hoc query overrides source queries."""
    cfg = _config(str(tmp_path / "test.db"))
    mocker.patch("etl.load_connector_class", return_value=MockConnector)

    summary = run_etl(cfg, source_filter=["arxiv"], ad_hoc_query="robotics", verbose=False)
    assert summary["inserted_total"] == 1
