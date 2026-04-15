"""ETL pipeline orchestration."""

from __future__ import annotations

import importlib
import json
from collections import defaultdict
from dataclasses import asdict
from typing import Any

from config import AppConfig, SourceConfig, load_config
from connectors.base import BaseConnector
from database import init_db, insert_document


def load_connector_class(connector_name: str) -> type[BaseConnector]:
    """Dynamically resolve connector class from connectors package."""
    module_name = f"connectors.{connector_name}_connector"
    module = importlib.import_module(module_name)

    for value in module.__dict__.values():
        if isinstance(value, type) and issubclass(value, BaseConnector) and value is not BaseConnector:
            return value
    raise ValueError(f"No BaseConnector implementation found in {module_name}")


def _autotag(text: str) -> dict[str, str | None]:
    """Apply lightweight heuristic tagging for normalized records."""
    low = text.lower()

    method = None
    if "transformer" in low:
        method = "transformer"
    elif "diffusion" in low:
        method = "diffusion"
    elif "reinforcement learning" in low or " rl " in f" {low} ":
        method = "reinforcement learning"

    math_topic = None
    if "optimization" in low or "convex" in low:
        math_topic = "optimization"
    elif "probability" in low or "bayes" in low:
        math_topic = "probability"
    elif "linear algebra" in low:
        math_topic = "linear algebra"

    domain = None
    if "vision" in low or "image" in low:
        domain = "computer vision"
    elif "language" in low or "nlp" in low or "text" in low:
        domain = "nlp"
    elif "robot" in low:
        domain = "robotics"
    elif "quantum" in low:
        domain = "quantum computing"

    return {"method": method, "math_topic": math_topic, "domain": domain}


def normalize_record(source_type: str, record: dict[str, Any]) -> dict[str, Any]:
    """Map connector-level output into unified documents schema."""
    title = record.get("title")
    if not title:
        raise ValueError("Record missing title")

    source_id = record.get("source_id") or record.get("arxiv_id") or record.get("doi") or record.get("url")
    content = record.get("content") or record.get("abstract") or record.get("description")
    authors = record.get("authors") or record.get("author")

    tags = _autotag(f"{title} {content or ''}")

    normalized = {
        "source_type": source_type,
        "source_id": source_id,
        "title": title,
        "authors": authors,
        "year": int(record["year"]) if str(record.get("year", "")).isdigit() else None,
        "published_date": record.get("published_date"),
        "content": content,
        "url": record.get("url"),
        "domain": record.get("domain") or tags["domain"],
        "method": record.get("method") or tags["method"],
        "math_topic": record.get("math_topic") or tags["math_topic"],
        "extra_metadata": {
            k: v
            for k, v in record.items()
            if k
            not in {
                "source_type",
                "source_id",
                "title",
                "authors",
                "author",
                "year",
                "published_date",
                "content",
                "abstract",
                "description",
                "url",
                "domain",
                "method",
                "math_topic",
            }
        },
    }
    return normalized


def run_etl(
    config: AppConfig,
    source_filter: list[str] | None = None,
    ad_hoc_query: str | None = None,
    verbose: bool = True,
) -> dict[str, Any]:
    """Run full ETL process and return execution summary."""
    db_path = config.database_path
    init_db(db_path)

    selected = {
        s.connector.lower() for s in config.sources if not source_filter or s.connector.lower() in source_filter
    }
    sources = [s for s in config.sources if s.connector.lower() in selected]

    totals_by_source: dict[str, int] = defaultdict(int)
    totals_by_domain: dict[str, int] = defaultdict(int)
    inserted_total = 0

    for source in sources:
        connector_cls = load_connector_class(source.connector)
        connector = connector_cls(asdict(source), {"polite_email": config.polite_email})

        queries = [ad_hoc_query] if ad_hoc_query else source.queries
        for query in queries:
            rows = connector.fetch(query, source.max_results_per_query)
            if verbose:
                print(f'Fetching from {source.name}: "{query}" ... {len(rows)} records')

            for row in rows:
                try:
                    normalized = normalize_record(source.connector, row)
                except ValueError:
                    continue
                inserted = insert_document(db_path, normalized)
                if inserted:
                    inserted_total += 1
                    totals_by_source[source.connector] += 1
                    domain = normalized.get("domain") or "unknown"
                    totals_by_domain[domain] += 1

    summary = {
        "project_name": config.project_name,
        "database_path": db_path,
        "sources_used": sorted(list(selected)),
        "inserted_total": inserted_total,
        "records_per_source": dict(totals_by_source),
        "records_by_domain": dict(totals_by_domain),
    }

    if verbose:
        print("\nETL Summary")
        print(json.dumps(summary, indent=2, ensure_ascii=True))

    return summary


def run_etl_from_config(
    config_path: str | None = None,
    source_filter: list[str] | None = None,
    ad_hoc_query: str | None = None,
    verbose: bool = True,
) -> dict[str, Any]:
    """Load config then run ETL with optional filters."""
    config = load_config(config_path)
    return run_etl(config, source_filter=source_filter, ad_hoc_query=ad_hoc_query, verbose=verbose)
