"""Non-network unit tests for web UI module."""

from __future__ import annotations

from config import AppConfig, SourceConfig
from web_ui import INDEX_HTML, save_result_locally


def test_index_html_contains_core_sections() -> None:
    """UI page includes expected workflow sections."""
    assert "Fetch Data" in INDEX_HTML
    assert "Ask a Question" in INDEX_HTML
    assert "Search Titles" in INDEX_HTML
    assert "Save Results Locally" in INDEX_HTML
    assert "/api/fetch" in INDEX_HTML
    assert "/api/ask" in INDEX_HTML


def test_save_result_locally_writes_file(tmp_path) -> None:
    """Saving results writes to data/saved_results with returned path."""
    cfg = AppConfig(
        project_name="x",
        database_path=str(tmp_path / "research.db"),
        llm_model="claude",
        sources=[SourceConfig(name="A", connector="arxiv", queries=["ml"], max_results_per_query=10)],
        polite_email=None,
    )

    saved = save_result_locally(cfg, slot="ask", content={"answer": "hello"}, filename="ask_result.json")
    out_path = tmp_path / "saved_results" / "ask_result.json"

    assert saved["saved_path"] == str(out_path)
    assert out_path.exists()
    assert "hello" in out_path.read_text(encoding="utf-8")
