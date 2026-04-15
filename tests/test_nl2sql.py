"""NL2SQL tests with mocked Claude client."""

from __future__ import annotations

from database import init_db, insert_document
from nl2sql import NL2SQLService


class FakeText:
    """Fake Anthropic content block."""

    def __init__(self, text: str) -> None:
        self.type = "text"
        self.text = text


class FakeResponse:
    """Fake Anthropic response."""

    def __init__(self, text: str) -> None:
        self.content = [FakeText(text)]


class FakeMessages:
    """Configurable mocked messages API."""

    def __init__(self, outputs: list[str]) -> None:
        self.outputs = outputs
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return FakeResponse(self.outputs.pop(0))


class FakeClient:
    """Fake Anthropic client wrapper."""

    def __init__(self, outputs: list[str]) -> None:
        self.messages = FakeMessages(outputs)


def _seed_db(path: str) -> None:
    init_db(path)
    insert_document(
        path,
        {
            "source_type": "arxiv",
            "source_id": "1",
            "title": "Transformer paper",
            "authors": "Alice",
            "year": 2024,
            "published_date": "2024-01-01",
            "content": "A transformer paper",
            "url": "https://example.com",
            "domain": "nlp",
            "method": "transformer",
            "math_topic": "optimization",
            "extra_metadata": {},
        },
    )


def test_schema_included_in_prompt(tmp_path) -> None:
    """Schema text is included in SQL system prompt."""
    db = str(tmp_path / "db.sqlite")
    _seed_db(db)
    svc = NL2SQLService(db_path=db, model="claude", client=FakeClient(["SELECT * FROM documents", "ok"]))
    prompt = svc._build_sql_system_prompt()
    assert "documents table columns" in prompt
    assert "source_type" in prompt


def test_dangerous_sql_rejected(tmp_path) -> None:
    """Dangerous generated SQL gets blocked."""
    db = str(tmp_path / "db.sqlite")
    _seed_db(db)
    svc = NL2SQLService(db_path=db, model="claude", client=FakeClient(["DROP TABLE documents"]))
    result = svc.ask("drop?")
    assert "couldn't execute" in result.natural_language_answer.lower()


def test_sql_extraction_strips_fences() -> None:
    """Fence extraction removes markdown wrapper."""
    sql = NL2SQLService.extract_sql("```sql\nSELECT * FROM documents;\n```")
    assert sql == "SELECT * FROM documents"


def test_empty_results_message(tmp_path) -> None:
    """Empty query response is user-friendly."""
    db = str(tmp_path / "db.sqlite")
    _seed_db(db)
    svc = NL2SQLService(db_path=db, model="claude", client=FakeClient(["SELECT * FROM documents WHERE year=1900"]))
    result = svc.ask("anything in 1900?")
    assert "no matching results" in result.natural_language_answer.lower()
