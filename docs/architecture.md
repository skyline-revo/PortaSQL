# Architecture

## End-to-End Flow

1. **Fetch**
   - Connector classes provide source-specific fetching logic.
   - Public demo includes a local `demo` connector and optional external connector examples.

2. **Transform**
   - ETL normalizes source records into a unified internal document schema.
   - Lightweight tagging heuristics map method/domain/math_topic fields.

3. **Store**
   - Normalized records are inserted into SQLite (`documents` table).
   - Duplicate protection is enforced via `UNIQUE(source_type, source_id)`.

4. **Retrieve**
   - SQL query helpers support safe read-only selection.
   - NL query path maps natural language to SQL:
     - LLM-backed mode when API key is configured
     - deterministic fallback mode for demo-only runs

## Major Components

- `src/connectors/`:
  - `base.py` defines connector interface
  - `demo_connector.py` provides public local dataset ingestion
  - additional connectors illustrate extensibility
- `src/etl.py`: orchestrates fetch/transform/load
- `src/database.py`: schema + DB helper methods
- `src/nl2sql.py`: NL -> SQL workflow with safety constraints
- `src/main.py`: interactive CLI
- `src/web_ui.py`: lightweight local UI + JSON endpoints

## SQL Storage Concept

A single `documents` table stores shared fields:
- source identity (`source_type`, `source_id`)
- bibliographic metadata (`title`, `authors`, `year`, `published_date`)
- searchable content (`content`)
- enrichment (`domain`, `method`, `math_topic`)
- source-specific payload (`extra_metadata` JSON)

This keeps querying simple while still allowing source-specific details.

## CLI and UI Interaction

Both surfaces use the same ETL/database services:
- CLI supports explicit command-driven workflows.
- UI wraps the same operations with local HTTP endpoints and a browser dashboard.

This keeps behavior consistent while showcasing two user experiences over one backend.
