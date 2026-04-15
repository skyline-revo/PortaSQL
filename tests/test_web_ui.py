"""Web UI behavior tests that avoid binding network sockets in restricted environments."""

from __future__ import annotations

from web_ui import INDEX_HTML


def test_web_ui_page_contains_expected_api_endpoints() -> None:
    """The HTML includes client calls for the core API endpoints."""
    assert "/api/fetch" in INDEX_HTML
    assert "/api/ask" in INDEX_HTML
    assert "/api/search" in INDEX_HTML
    assert "/api/stats" in INDEX_HTML
    assert "/api/sources" in INDEX_HTML
    assert "/api/schema" in INDEX_HTML
    assert "/api/save-result" in INDEX_HTML
