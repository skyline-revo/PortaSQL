"""Configuration loading and validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import shutil

import yaml


@dataclass(slots=True)
class SourceConfig:
    """Typed source configuration."""

    name: str
    connector: str
    queries: list[str]
    max_results_per_query: int
    api_key: str | None = None
    polite_email: str | None = None


@dataclass(slots=True)
class AppConfig:
    """Top-level application configuration."""

    project_name: str
    database_path: str
    llm_model: str
    sources: list[SourceConfig]
    polite_email: str | None = None


def get_project_root() -> Path:
    """Return project root from src package location."""
    return Path(__file__).resolve().parent.parent


def load_raw_config(config_path: str | None = None) -> dict[str, Any]:
    """Load raw config dict from YAML and ensure existence."""
    root = get_project_root()
    path = Path(config_path) if config_path else root / "config.yaml"
    example = root / "config.yaml.example"

    if not path.exists():
        if not example.exists():
            raise FileNotFoundError("config.yaml and config.yaml.example are both missing")
        shutil.copy(example, path)
        raise FileNotFoundError(f"Created {path}. Please edit it and re-run.")

    with path.open("r", encoding="utf-8") as f:
        loaded = yaml.safe_load(f) or {}
    if not isinstance(loaded, dict):
        raise ValueError("config.yaml must contain a YAML object")
    return loaded


def validate_config(raw: dict[str, Any]) -> AppConfig:
    """Validate and parse raw config into typed dataclasses."""
    required = ["project_name", "database_path", "llm_model", "sources"]
    missing = [k for k in required if k not in raw]
    if missing:
        raise ValueError(f"Missing required config fields: {', '.join(missing)}")

    if not isinstance(raw["sources"], list) or not raw["sources"]:
        raise ValueError("sources must be a non-empty list")

    sources: list[SourceConfig] = []
    for i, source in enumerate(raw["sources"]):
        if not isinstance(source, dict):
            raise ValueError(f"sources[{i}] must be an object")

        for field in ["name", "connector", "queries", "max_results_per_query"]:
            if field not in source:
                raise ValueError(f"sources[{i}] missing required field '{field}'")

        if not isinstance(source["queries"], list) or not source["queries"]:
            raise ValueError(f"sources[{i}].queries must be a non-empty list")

        sources.append(
            SourceConfig(
                name=str(source["name"]),
                connector=str(source["connector"]).lower(),
                queries=[str(q) for q in source["queries"]],
                max_results_per_query=int(source["max_results_per_query"]),
                api_key=source.get("api_key"),
                polite_email=source.get("polite_email"),
            )
        )

    return AppConfig(
        project_name=str(raw["project_name"]),
        database_path=str(raw["database_path"]),
        llm_model=str(raw["llm_model"]),
        polite_email=raw.get("polite_email"),
        sources=sources,
    )


def load_config(config_path: str | None = None) -> AppConfig:
    """Load and validate app config from YAML."""
    return validate_config(load_raw_config(config_path))
