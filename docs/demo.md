# Demo Guide

## What the Public Demo Shows

- Connector-based ingestion
- ETL normalization pipeline
- SQLite persistence
- Querying via CLI and local web UI
- Basic natural language querying (with and without API key)

## Fastest Demo Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp config/config.example.yaml config/config.yaml
./PortaSQL start
```

In CLI:

```text
fetch
stats
search transformer
ask How many records do we have?
```

## UI Demo

```bash
./PortaSQL ui
```

Open `http://127.0.0.1:8080` and run:
1. Fetch Data
2. Refresh Stats
3. Search Titles
4. Ask a Question

## Demo Dataset

Bundled data is located at:
- `demo/sample_documents.json`

It is intentionally small and deterministic for repeatable evaluation.

## Notes for Interviewers

This public demo prioritizes clarity and runnable architecture.
Several production-specific optimizations and internal logic paths are intentionally withheld from the public repository.
