# PortaSQL (Portfolio Edition)

A local-first ETL + knowledge retrieval system that turns heterogeneous data into queryable SQL and supports natural-language exploration through CLI and web UI.

> This repository is a portfolio version of the project for technical evaluation and interview review. Some production components, internal configurations, and core retrieval logic are intentionally omitted. Full implementation can be presented privately upon request.

## Why This Project

PortaSQL demonstrates practical data engineering + application design in one workflow:
- API-style ingestion
- schema normalization
- SQLite persistence
- query tooling (SQL + natural language)
- runnable UX via CLI and local web UI

## Features (Public Demo)

- Modular connector interface (`BaseConnector`) with pluggable sources
- End-to-end ETL pipeline (`fetch -> transform -> store`)
- Unified SQLite schema with metadata fields
- Interactive CLI for fetch/search/stats/ask
- Local web dashboard for demo workflows
- Natural-language query path with:
  - external LLM mode (Anthropic, when key is provided)
  - fallback local demo mode (no API key required)
- Minimal local demo dataset for reproducible runs

## Architecture Overview

High-level flow:

1. Connectors fetch records (demo connector included)
2. ETL normalizes records into one document schema
3. Data is inserted into local SQLite (duplicate-safe)
4. CLI/UI retrieval tools query and summarize results

See detailed docs:
- [Architecture](docs/architecture.md)
- [Demo Guide](docs/demo.md)
- [Security Notes](docs/security-notes.md)

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp config/config.example.yaml config/config.yaml
```

Run CLI:

```bash
python src/main.py
```

Or one-line launcher:

```bash
./PortaSQL start
```

Run local web UI:

```bash
./PortaSQL ui
```

## CLI Usage Examples

```text
> fetch
> fetch --source demo
> fetch --query "transformer"
> search transformer
> stats
> ask How many transformer papers are in the database?
```

## Screenshots

Place screenshots in `assets/` and reference them here.

- CLI demo: `assets/cli-demo.png`
- Web UI demo: `assets/web-ui-demo.png`

## Demo Limitations (Intentional)

This public version is intentionally constrained:
- production retrieval/ranking logic is simplified
- production config/deployment details are removed
- external API credentials are not included
- private datasets and internal endpoints are not public

## Tech Stack

- Python 3.10+
- SQLite
- PyYAML
- requests
- arxiv (optional source)
- anthropic (optional LLM mode)
- pytest / pytest-mock

## Local Setup Notes

Environment variables (optional):

```bash
cp .env.example .env
# then export values manually or with your preferred dotenv workflow
```

`ANTHROPIC_API_KEY` enables higher-quality NL answers. Without it, `ask` still works in a limited local demo mode.

## Public vs Private Implementation

This repository is not an open-source production release.
It is a portfolio-safe implementation designed to show architecture, coding style, testing approach, and system design decisions without exposing all proprietary details.

For interview loops, the fuller private implementation (including additional retrieval logic and production configuration patterns) can be shared live upon request.

## Rights

See [RIGHTS.md](RIGHTS.md). All rights reserved.
