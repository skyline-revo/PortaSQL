# llm-knowledge-retrieval

I've been curious about how LLMs can interact with structured databases - especially for domains where accuracy matters more than creativity. But I didn't want to build something that only works with one data source.

This project is a modular pipeline that lets you:
1. Connect to any API (arXiv, OpenAlex, NewsAPI, or add your own)
2. Define what topics you want to collect in a simple config file
3. Fetch and store data automatically (ETL pipeline)
4. Query everything using plain English (Text-to-SQL via Claude)
5. Expose it all via MCP so AI agents can access your knowledge base

Adding a new data source is just writing one connector class that implements the BaseConnector interface. The rest of the pipeline handles it automatically.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp config.yaml.example config.yaml
```

Set your Anthropic API key:

```bash
export ANTHROPIC_API_KEY="your_key_here"
```

## Quick Start

```bash
python src/main.py
```

Then run:
- `fetch`
- `ask Which papers about transformers were published in 2024?`
- `stats`
- `ui` (starts local web app at `http://127.0.0.1:8080`)

### One-Line Launcher

You can start the project with one command (no manual `cd` or `source` needed):

```bash
"/Users/rextang/Desktop/ETL Pipeline/llm-knowledge-retrieval/PortaSQL" start
```

Other commands:

```bash
"/Users/rextang/Desktop/ETL Pipeline/llm-knowledge-retrieval/PortaSQL" ui
"/Users/rextang/Desktop/ETL Pipeline/llm-knowledge-retrieval/PortaSQL" test
```

## Adding a New Connector

1. Create a file in `src/connectors/` (example: `myapi_connector.py`).
2. Implement a class that inherits from `BaseConnector`.
3. Implement:
   - `fetch(query: str, max_results: int) -> list[dict]`
   - `get_source_name() -> str`
4. Return documents with at least:
   - `title`, `authors`, `date/published_date`, `abstract/content`, `source_name`, `source_id`, `url`
5. Add a new source entry to `config.yaml` using `connector: "myapi"`.

No ETL code changes are required.

## Configuration

Use `config.yaml`:

- `project_name`: project label
- `database_path`: sqlite file path
- `llm_model`: Anthropic model name
- `polite_email`: optional for OpenAlex polite pool
- `sources[]`:
  - `name`
  - `connector`
  - `queries`
  - `max_results_per_query`
  - `api_key` (only for key-based APIs)

## Architecture Diagram (ASCII)

```text
          +-------------------+
          |    config.yaml    |
          +---------+---------+
                    |
                    v
+-------------------+-------------------+
|            ETL Orchestrator           |
| (dynamic connector loading + tagging) |
+---------+---------------+-------------+
          |               |
          v               v
   +------+-----+   +-----+------+
   | Connectors |   | Transform   |
   | arXiv      |   | normalize   |
   | OpenAlex   |   | autotag     |
   | NewsAPI    |   +-----+------+
   +------+-----+         |
          |               v
          +--------> +----+-----+
                     | SQLite DB |
                     +----+-----+
                          |
          +---------------+---------------+
          |                               |
          v                               v
 +--------+---------+             +-------+--------+
 | NL -> SQL (LLM)  |             | MCP JSON-RPC   |
 | Claude + safety  |             | tools/query    |
 +------------------+             +----------------+
```

## Example Session

```text
$ python src/main.py
Welcome to LLM Knowledge Retrieval System

> fetch
Fetching from ML Papers from arXiv: "machine learning" ... 50 records
Done! Total inserted this run: 128 documents.

> ask Which papers about transformers were published in 2024?
SQL: SELECT title, authors, year FROM documents WHERE title LIKE '%transformer%' AND year = 2024
Found 12 rows.

> search quantum
1. Quantum Transformers - A. Author (2024) [arxiv]
```

## Running Tests

```bash
pytest tests/ -v
```

Integration tests are marked with `@pytest.mark.integration` and are skipped unless enabled:

```bash
RUN_INTEGRATION=1 NEWSAPI_KEY=... pytest tests/ -v -m integration
```

## Future Work

- User access control
- Vector search
- Rich web UI with auth and dashboards
- Scheduled fetching (cron)
- Support for streaming APIs
