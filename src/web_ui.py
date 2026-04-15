"""Simple local web UI for the knowledge retrieval system."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import re
from typing import Any
from urllib.parse import parse_qs, urlparse

from config import AppConfig, load_config
from database import execute_query, get_schema_info, get_stats, init_db
from etl import run_etl
from nl2sql import NL2SQLService


INDEX_HTML = """<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width,initial-scale=1\" />
  <title>LLM Knowledge Retrieval</title>
  <style>
    :root {
      --bg: #f6f8f3;
      --bg-2: #e8efe3;
      --ink: #1e2a1f;
      --muted: #5a6b5f;
      --card: rgba(255, 255, 255, 0.82);
      --line: #d8e2d3;
      --primary: #0f766e;
      --primary-2: #14532d;
      --accent: #b45309;
      --success: #166534;
      --error: #9f1239;
      --mono: "IBM Plex Mono", "SFMono-Regular", Menlo, Consolas, monospace;
      --sans: "Avenir Next", "Manrope", "Trebuchet MS", "Segoe UI", sans-serif;
      --radius: 16px;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      color: var(--ink);
      font-family: var(--sans);
      background:
        radial-gradient(circle at 8% 5%, #d7ede8 0%, transparent 38%),
        radial-gradient(circle at 89% 16%, #f8e4c6 0%, transparent 32%),
        linear-gradient(160deg, var(--bg), var(--bg-2));
      min-height: 100vh;
    }
    .orb {
      position: fixed;
      width: 260px;
      height: 260px;
      border-radius: 50%;
      filter: blur(55px);
      opacity: 0.35;
      pointer-events: none;
      animation: drift 15s ease-in-out infinite alternate;
    }
    .orb.one { background: #22c55e; top: -70px; right: -90px; }
    .orb.two { background: #f59e0b; bottom: -90px; left: -80px; animation-delay: 1.2s; }
    .wrap {
      max-width: 1220px;
      margin: 0 auto;
      padding: 26px 18px 40px;
      position: relative;
      z-index: 2;
    }
    .hero {
      border: 1px solid var(--line);
      border-radius: calc(var(--radius) + 4px);
      padding: 22px 20px;
      background: linear-gradient(130deg, rgba(255,255,255,0.88), rgba(245,249,241,0.75));
      backdrop-filter: blur(8px);
      box-shadow: 0 14px 28px rgba(22, 35, 17, 0.08);
      animation: rise 0.48s ease-out;
    }
    .eyebrow {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      border: 1px solid #caddd0;
      border-radius: 999px;
      padding: 5px 10px;
      background: rgba(233, 247, 240, 0.78);
      font-size: 0.75rem;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: #116149;
      font-weight: 700;
    }
    h1 {
      margin: 12px 0 6px;
      font-size: clamp(1.6rem, 3.8vw, 2.45rem);
      line-height: 1.08;
      letter-spacing: -0.02em;
    }
    .subtitle {
      margin: 0;
      color: var(--muted);
      max-width: 760px;
      line-height: 1.5;
    }
    .kpis {
      margin-top: 14px;
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
      gap: 10px;
    }
    .kpi {
      border: 1px solid var(--line);
      background: #ffffff;
      border-radius: 12px;
      padding: 10px 11px;
    }
    .kpi .label {
      font-size: 0.76rem;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.08em;
      font-weight: 700;
    }
    .kpi .value {
      margin-top: 6px;
      font-size: 1.22rem;
      font-weight: 800;
      line-height: 1;
    }
    .grid {
      margin-top: 16px;
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
      gap: 14px;
      align-items: start;
    }
    .col {
      display: flex;
      flex-direction: column;
      gap: 14px;
    }
    .card {
      border-radius: var(--radius);
      border: 1px solid var(--line);
      background: var(--card);
      backdrop-filter: blur(8px);
      box-shadow: 0 10px 24px rgba(18, 32, 25, 0.07);
      padding: 14px;
      animation: rise 0.38s ease-out;
    }
    .card h2 {
      margin: 0 0 10px;
      font-size: 1rem;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .chip {
      font-size: 0.7rem;
      border: 1px solid #d6e3dd;
      padding: 2px 8px;
      border-radius: 999px;
      color: #385146;
      background: #eef5f1;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      font-weight: 700;
    }
    label {
      display: block;
      margin: 0 0 5px;
      font-size: 0.82rem;
      color: var(--muted);
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    input, select, textarea, button {
      width: 100%;
      border-radius: 11px;
      font: inherit;
      margin-bottom: 9px;
      border: 1px solid var(--line);
    }
    input, select, textarea {
      padding: 10px 11px;
      background: rgba(255, 255, 255, 0.97);
    }
    textarea { min-height: 95px; resize: vertical; }
    input:focus, select:focus, textarea:focus {
      outline: 2px solid rgba(15, 118, 110, 0.22);
      border-color: var(--primary);
    }
    button {
      border: none;
      padding: 11px 14px;
      color: #ffffff;
      cursor: pointer;
      font-weight: 800;
      letter-spacing: 0.01em;
      background: linear-gradient(130deg, var(--primary), var(--primary-2));
      box-shadow: 0 9px 18px rgba(10, 94, 86, 0.26);
      transition: transform 0.18s ease, box-shadow 0.18s ease;
    }
    button:hover {
      transform: translateY(-1px);
      box-shadow: 0 13px 22px rgba(10, 94, 86, 0.3);
    }
    button:active { transform: translateY(0); }
    .status {
      min-height: 18px;
      font-size: 0.82rem;
      color: var(--success);
      font-weight: 700;
      margin-bottom: 7px;
    }
    .status.error { color: var(--error); }
    .output {
      margin: 0;
      padding: 10px;
      border: 1px solid var(--line);
      border-radius: 11px;
      background: #fbfdf9;
      min-height: 96px;
      max-height: 230px;
      overflow: auto;
      font-family: var(--mono);
      font-size: 0.82rem;
      line-height: 1.45;
      white-space: pre-wrap;
      word-break: break-word;
    }
    @media (max-width: 920px) {
      .grid { grid-template-columns: 1fr; }
    }
    @keyframes rise {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }
    @keyframes drift {
      from { transform: translateY(0px) translateX(0px); }
      to { transform: translateY(16px) translateX(12px); }
    }
  </style>
</head>
<body>
  <div class=\"orb one\"></div>
  <div class=\"orb two\"></div>
  <div class=\"wrap\">
    <section class=\"hero\">
      <div class=\"eyebrow\">Research Intelligence Desk</div>
      <h1>LLM Knowledge Retrieval</h1>
      <p class=\"subtitle\">A faster way to run ETL, inspect your database, and ask natural language questions against your collected sources.</p>
      <div class=\"kpis\">
        <div class=\"kpi\"><div class=\"label\">Database</div><div id=\"kpi-db\" class=\"value\">-</div></div>
        <div class=\"kpi\"><div class=\"label\">Total Docs</div><div id=\"kpi-total\" class=\"value\">-</div></div>
        <div class=\"kpi\"><div class=\"label\">Top Source</div><div id=\"kpi-source\" class=\"value\">-</div></div>
        <div class=\"kpi\"><div class=\"label\">Top Domain</div><div id=\"kpi-domain\" class=\"value\">-</div></div>
      </div>
    </section>

    <div class=\"grid\">
      <div class=\"col\">
        <section class=\"card\">
          <h2>Fetch Data <span class=\"chip\">ETL</span></h2>
          <label for=\"source\">Source Filter</label>
          <input id=\"source\" placeholder=\"arxiv\" />
          <label for=\"query\">Ad-hoc Query</label>
          <input id=\"query\" placeholder=\"quantum computing\" />
          <button onclick=\"runFetch()\">Run ETL</button>
          <div id=\"fetch-status\" class=\"status\"></div>
          <pre id=\"fetch-output\" class=\"output\">No run yet.</pre>
        </section>

        <section class=\"card\">
          <h2>Ask a Question <span class=\"chip\">NL2SQL</span></h2>
          <textarea id=\"ask\" placeholder=\"Which transformer papers were published in 2024?\"></textarea>
          <button onclick=\"runAsk()\">Ask</button>
          <pre id=\"ask-output\" class=\"output\">No question yet.</pre>
        </section>

        <section class=\"card\">
          <h2>Search Titles <span class=\"chip\">Query</span></h2>
          <input id=\"keyword\" placeholder=\"transformer\" />
          <button onclick=\"runSearch()\">Search</button>
          <pre id=\"search-output\" class=\"output\">No search yet.</pre>
        </section>

        <section id=\"sources-card\" class=\"card\">
          <h2>Sources <span class=\"chip\">Config</span></h2>
          <button onclick=\"loadSources()\">Load Sources</button>
          <pre id=\"sources-output\" class=\"output\">No sources loaded.</pre>
        </section>
      </div>

      <div class=\"col\">
        <section class=\"card\">
          <h2>Schema <span class=\"chip\">SQLite</span></h2>
          <button onclick=\"loadSchema()\">Show Schema</button>
          <pre id=\"schema-output\" class=\"output\">Schema not loaded.</pre>
        </section>

        <section class=\"card\">
          <h2>Save Results Locally <span class=\"chip\">Export</span></h2>
          <label for=\"save-slot\">Result Block</label>
          <select id=\"save-slot\">
            <option value=\"fetch\">Fetch Output</option>
            <option value=\"ask\">Ask Output</option>
            <option value=\"search\">Search Output</option>
            <option value=\"stats\">Stats Output</option>
            <option value=\"sources\">Sources Output</option>
            <option value=\"schema\">Schema Output</option>
          </select>
          <label for=\"save-filename\">Filename (.json or .txt)</label>
          <input id=\"save-filename\" placeholder=\"ask_result.json\" />
          <button onclick=\"saveResultLocally()\">Save to Local File</button>
          <div id=\"save-status\" class=\"status\"></div>
          <pre id=\"save-output\" class=\"output\">No file saved yet.</pre>
        </section>

        <section id=\"stats-card\" class=\"card\">
          <h2>Stats <span class=\"chip\">Overview</span></h2>
          <button onclick=\"loadStats()\">Refresh Stats</button>
          <pre id=\"stats-output\" class=\"output\">No stats yet.</pre>
        </section>
      </div>
    </div>
  </div>

  <script>
    const latestResults = {
      fetch: null,
      ask: null,
      search: null,
      stats: null,
      sources: null,
      schema: null
    };

    function setStatus(id, message, isError) {
      const el = document.getElementById(id);
      el.textContent = message || '';
      el.classList.toggle('error', !!isError);
    }

    function pretty(data) {
      if (typeof data === 'string') return data;
      return JSON.stringify(data, null, 2);
    }

    async function jsonFetch(url, options) {
      const response = await fetch(url, options);
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || 'Request failed');
      }
      return data;
    }

    function updateKpis(stats) {
      const source = (stats.by_source && stats.by_source[0]) ? stats.by_source[0].source_type : '-';
      const domain = (stats.by_domain && stats.by_domain[0]) ? stats.by_domain[0].domain : '-';
      document.getElementById('kpi-db').textContent = 'SQLite';
      document.getElementById('kpi-total').textContent = String(stats.total_documents ?? '-');
      document.getElementById('kpi-source').textContent = source;
      document.getElementById('kpi-domain').textContent = domain;
    }

    function syncStatsPanelToSources() {
      const statsCard = document.getElementById('stats-card');
      const sourcesCard = document.getElementById('sources-card');
      const statsOutput = document.getElementById('stats-output');
      if (!statsCard || !sourcesCard || !statsOutput) return;

      statsOutput.style.minHeight = '96px';
      const statsRect = statsCard.getBoundingClientRect();
      const sourcesRect = sourcesCard.getBoundingClientRect();
      const delta = Math.round(sourcesRect.bottom - statsRect.bottom);

      if (delta > 0) {
        const base = 96;
        statsOutput.style.minHeight = (base + delta) + 'px';
      }
    }

    async function runFetch() {
      const source = document.getElementById('source').value.trim();
      const query = document.getElementById('query').value.trim();
      setStatus('fetch-status', 'Running ETL...', false);
      try {
        const data = await jsonFetch('/api/fetch', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ source, query })
        });
        setStatus('fetch-status', 'Fetch complete.', false);
        latestResults.fetch = data;
        document.getElementById('fetch-output').textContent = pretty(data);
        await loadStats();
      } catch (err) {
        setStatus('fetch-status', String(err), true);
        document.getElementById('fetch-output').textContent = String(err);
      }
    }

    async function runAsk() {
      const question = document.getElementById('ask').value.trim();
      if (!question) return;
      try {
        const data = await jsonFetch('/api/ask', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question })
        });
        latestResults.ask = data;
        document.getElementById('ask-output').textContent = pretty(data);
      } catch (err) {
        document.getElementById('ask-output').textContent = String(err);
      }
    }

    async function runSearch() {
      const keyword = document.getElementById('keyword').value.trim();
      if (!keyword) return;
      try {
        const data = await jsonFetch('/api/search?keyword=' + encodeURIComponent(keyword));
        latestResults.search = data;
        document.getElementById('search-output').textContent = pretty(data);
      } catch (err) {
        document.getElementById('search-output').textContent = String(err);
      }
    }

    async function loadStats() {
      try {
        const data = await jsonFetch('/api/stats');
        latestResults.stats = data;
        document.getElementById('stats-output').textContent = pretty(data);
        updateKpis(data);
        syncStatsPanelToSources();
      } catch (err) {
        document.getElementById('stats-output').textContent = String(err);
        syncStatsPanelToSources();
      }
    }

    async function loadSources() {
      try {
        const data = await jsonFetch('/api/sources');
        latestResults.sources = data;
        document.getElementById('sources-output').textContent = pretty(data);
        syncStatsPanelToSources();
      } catch (err) {
        document.getElementById('sources-output').textContent = String(err);
        syncStatsPanelToSources();
      }
    }

    async function loadSchema() {
      try {
        const data = await jsonFetch('/api/schema');
        latestResults.schema = data.schema;
        document.getElementById('schema-output').textContent = data.schema;
      } catch (err) {
        document.getElementById('schema-output').textContent = String(err);
      }
    }

    async function saveResultLocally() {
      const slot = document.getElementById('save-slot').value;
      const filename = document.getElementById('save-filename').value.trim();
      const content = latestResults[slot];
      if (content === null || content === undefined) {
        setStatus('save-status', 'Run that section first so there is data to save.', true);
        return;
      }

      setStatus('save-status', 'Saving file...', false);
      try {
        const data = await jsonFetch('/api/save-result', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ slot, filename, content })
        });
        setStatus('save-status', 'Saved successfully.', false);
        document.getElementById('save-output').textContent = pretty(data);
      } catch (err) {
        setStatus('save-status', String(err), true);
        document.getElementById('save-output').textContent = String(err);
      }
    }

    loadStats();
    loadSources();
    window.addEventListener('resize', syncStatsPanelToSources);
  </script>
</body>
</html>
"""

SAFE_FILENAME_RE = re.compile(r"^[A-Za-z0-9._-]+$")


def save_result_locally(
    app_config: AppConfig,
    slot: str,
    content: Any,
    filename: str | None = None,
) -> dict[str, str]:
    """Save UI result payload to the local filesystem under data/saved_results."""
    cleaned_slot = slot.strip().lower() or "result"
    if not SAFE_FILENAME_RE.match(cleaned_slot):
        raise ValueError("Invalid result slot name")

    target_name = (filename or f"{cleaned_slot}_result.json").strip()
    if not SAFE_FILENAME_RE.match(target_name):
        raise ValueError("Filename can only contain letters, numbers, dot, underscore, and hyphen")

    ext = Path(target_name).suffix.lower()
    if ext not in {".json", ".txt"}:
        raise ValueError("Filename must end with .json or .txt")

    db_parent = Path(app_config.database_path).expanduser().resolve().parent
    save_dir = db_parent / "saved_results"
    save_dir.mkdir(parents=True, exist_ok=True)
    target_path = save_dir / target_name

    if ext == ".txt":
        body = content if isinstance(content, str) else json.dumps(content, ensure_ascii=True, indent=2)
    else:
        body = json.dumps(content, ensure_ascii=True, indent=2)

    target_path.write_text(body, encoding="utf-8")
    return {"saved_path": str(target_path), "slot": cleaned_slot}


class UIHandler(BaseHTTPRequestHandler):
    """HTTP request handler for UI and JSON API endpoints."""

    server: "KnowledgeUIHTTPServer"

    def do_GET(self) -> None:  # noqa: N802
        """Handle GET requests."""
        parsed = urlparse(self.path)

        if parsed.path == "/":
            self._send_html(INDEX_HTML)
            return

        if parsed.path == "/api/stats":
            self._send_json(get_stats(self.server.app_config.database_path))
            return

        if parsed.path == "/api/sources":
            self._send_json(
                [
                    {
                        "name": s.name,
                        "connector": s.connector,
                        "queries": s.queries,
                        "max_results_per_query": s.max_results_per_query,
                    }
                    for s in self.server.app_config.sources
                ]
            )
            return

        if parsed.path == "/api/schema":
            self._send_json({"schema": get_schema_info(self.server.app_config.database_path)})
            return

        if parsed.path == "/api/search":
            params = parse_qs(parsed.query)
            keyword = (params.get("keyword", [""])[0]).strip()
            if not keyword:
                self._send_error_json(400, "keyword is required")
                return
            escaped = keyword.replace("'", "''")
            sql = (
                "SELECT id, title, authors, year, source_type, url FROM documents "
                f"WHERE title LIKE '%{escaped}%' ORDER BY year DESC, id DESC LIMIT 50"
            )
            self._send_json(execute_query(self.server.app_config.database_path, sql))
            return

        self._send_error_json(404, "not found")

    def do_POST(self) -> None:  # noqa: N802
        """Handle POST requests."""
        payload = self._read_json_body()
        if payload is None:
            self._send_error_json(400, "invalid JSON body")
            return

        if self.path == "/api/fetch":
            source = str(payload.get("source", "")).strip().lower()
            ad_hoc_query = str(payload.get("query", "")).strip() or None
            source_filter = [source] if source else None
            summary = run_etl(
                self.server.app_config,
                source_filter=source_filter,
                ad_hoc_query=ad_hoc_query,
                verbose=False,
            )
            self._send_json(summary)
            return

        if self.path == "/api/ask":
            question = str(payload.get("question", "")).strip()
            if not question:
                self._send_error_json(400, "question is required")
                return

            result = self.server.nl2sql.ask(question)
            self._send_json(
                {
                    "question": result.question,
                    "sql_query": result.sql_query,
                    "raw_results": result.raw_results,
                    "natural_language_answer": result.natural_language_answer,
                }
            )
            return

        if self.path == "/api/save-result":
            slot = str(payload.get("slot", "")).strip()
            if not slot:
                self._send_error_json(400, "slot is required")
                return
            content = payload.get("content")
            if content is None:
                self._send_error_json(400, "content is required")
                return
            filename = payload.get("filename")
            try:
                saved = save_result_locally(self.server.app_config, slot=slot, content=content, filename=filename)
            except ValueError as exc:
                self._send_error_json(400, str(exc))
                return
            self._send_json(saved)
            return

        self._send_error_json(404, "not found")

    def log_message(self, fmt: str, *args: Any) -> None:
        """Keep output clean by suppressing default request logs."""
        return

    def _read_json_body(self) -> dict[str, Any] | None:
        """Read and parse JSON payload from request body."""
        try:
            size = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return None

        raw = self.rfile.read(size) if size > 0 else b"{}"
        try:
            loaded = json.loads(raw.decode("utf-8"))
        except Exception:
            return None

        return loaded if isinstance(loaded, dict) else None

    def _send_json(self, payload: Any, status: int = 200) -> None:
        """Write JSON response."""
        body = json.dumps(payload, ensure_ascii=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html: str, status: int = 200) -> None:
        """Write HTML response."""
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_error_json(self, status: int, message: str) -> None:
        """Write JSON error response."""
        self._send_json({"error": message}, status=status)


class KnowledgeUIHTTPServer(ThreadingHTTPServer):
    """HTTP server carrying shared app context for handlers."""

    def __init__(self, server_address: tuple[str, int], handler: type[BaseHTTPRequestHandler], app_config: AppConfig) -> None:
        """Store config and service objects for requests."""
        super().__init__(server_address, handler)
        self.app_config = app_config
        self.nl2sql = NL2SQLService(db_path=app_config.database_path, model=app_config.llm_model)


def run_web_ui(host: str = "127.0.0.1", port: int = 8080, config_path: str | None = None) -> None:
    """Start the local web UI server."""
    app_config = load_config(config_path)
    init_db(app_config.database_path)

    server = KnowledgeUIHTTPServer((host, port), UIHandler, app_config)
    print(f"Web UI running at http://{host}:{port}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping web UI.")
    finally:
        server.server_close()


if __name__ == "__main__":
    run_web_ui()
