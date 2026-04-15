"""Interactive CLI entrypoint."""

from __future__ import annotations

import shlex
import subprocess
from pathlib import Path

from config import get_project_root, load_config
from database import execute_query, get_schema_info, get_stats, init_db
from etl import run_etl
from nl2sql import NL2SQLService
from web_ui import run_web_ui


WELCOME = """Welcome to LLM Knowledge Retrieval System

Commands:
  fetch                    - Run ETL pipeline (fetch data from all configured sources)
  fetch --source arxiv     - Fetch from specific source only
  fetch --query \"robotics\" - Ad-hoc fetch with custom query
  ask <question>           - Ask a question in natural language
  search <keyword>         - Quick keyword search across titles
  stats                    - Show database statistics
  sources                  - Show configured data sources
  schema                   - Show database schema
  config                   - Open config.yaml for editing
  ui                       - Start local web UI at http://127.0.0.1:8080
  quit                     - Exit
"""


def _parse_fetch_args(command: str) -> tuple[list[str] | None, str | None]:
    """Parse fetch command options."""
    tokens = shlex.split(command)
    source_filter: list[str] = []
    ad_hoc_query: str | None = None

    i = 1
    while i < len(tokens):
        token = tokens[i]
        if token == "--source" and i + 1 < len(tokens):
            source_filter.append(tokens[i + 1].lower())
            i += 2
            continue
        if token == "--query" and i + 1 < len(tokens):
            ad_hoc_query = tokens[i + 1]
            i += 2
            continue
        i += 1

    return (source_filter or None), ad_hoc_query


def _open_config() -> None:
    """Open config.yaml in the user's preferred editor if available."""
    path = get_project_root() / "config.yaml"
    if not path.exists():
        print("Config does not exist yet. Run any command once to auto-generate from example.")
        return

    editor = None
    for env_name in ("VISUAL", "EDITOR"):
        candidate = __import__("os").environ.get(env_name)
        if candidate:
            editor = candidate
            break

    if editor:
        try:
            subprocess.run([editor, str(path)], check=False)
            return
        except Exception:
            pass

    print(f"Edit this file manually: {path}")


def run_cli() -> None:
    """Run interactive CLI loop."""
    print(WELCOME)

    config = load_config()
    init_db(config.database_path)
    nl2sql = NL2SQLService(db_path=config.database_path, model=config.llm_model)

    while True:
        try:
            command = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            return

        if not command:
            continue

        if command == "quit":
            print("Goodbye.")
            return

        if command.startswith("fetch"):
            source_filter, ad_hoc_query = _parse_fetch_args(command)
            summary = run_etl(config, source_filter=source_filter, ad_hoc_query=ad_hoc_query, verbose=True)
            print(f"Done! Total inserted this run: {summary['inserted_total']} documents.")
            continue

        if command.startswith("ask "):
            question = command[4:].strip()
            result = nl2sql.ask(question)
            if result.sql_query:
                print(f"SQL: {result.sql_query}")
            print(result.natural_language_answer)
            continue

        if command.startswith("search "):
            keyword = command[7:].strip().replace("'", "''")
            sql = (
                "SELECT title, authors, year, source_type FROM documents "
                f"WHERE title LIKE '%{keyword}%' ORDER BY year DESC LIMIT 20"
            )
            rows = execute_query(config.database_path, sql)
            if not rows:
                print("No matches found.")
            else:
                for idx, row in enumerate(rows, start=1):
                    print(f"{idx}. {row.get('title')} - {row.get('authors')} ({row.get('year')}) [{row.get('source_type')}]")
            continue

        if command == "stats":
            print(get_stats(config.database_path))
            continue

        if command == "sources":
            for s in config.sources:
                print(f"- {s.name} ({s.connector}): {', '.join(s.queries)}")
            continue

        if command == "schema":
            print(get_schema_info(config.database_path))
            continue

        if command == "config":
            _open_config()
            continue

        if command == "ui":
            run_web_ui()
            continue

        print("Unknown command. Try: fetch, ask, search, stats, sources, schema, config, ui, quit")


if __name__ == "__main__":
    run_cli()
