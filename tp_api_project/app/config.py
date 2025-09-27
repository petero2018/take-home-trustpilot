from dataclasses import dataclass
from functools import lru_cache
import os
from typing import Literal

_DEFAULT_DB_PATHS: dict[str, str] = {
    "dev": "../data/dev.duckdb",
    "prod": "../data/prod.duckdb",
}

_DEFAULT_SCHEMAS: dict[str, str | None] = {
    "dev": None,
    "prod": None,
}


def _to_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


@dataclass(frozen=True)
class Settings:
    environment: Literal["dev", "prod"]
    duckdb_path: str
    duckdb_read_only: bool
    duckdb_schema: str | None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    environment = os.getenv("TP_API_ENV", "prod").strip().lower() or "prod"
    if environment not in ("dev", "prod"):
        environment = "prod"

    duckdb_path = (
        os.getenv("TP_API_DUCKDB_PATH")
        or os.getenv("DUCKDB_PATH")
        or _DEFAULT_DB_PATHS.get(environment, _DEFAULT_DB_PATHS["prod"])
    )

    duckdb_read_only = _to_bool(
        os.getenv("TP_API_DUCKDB_READ_ONLY"),
        default=(environment == "prod"),
    )

    raw_schema = os.getenv("TP_API_DUCKDB_SCHEMA")
    duckdb_schema = (
        raw_schema.strip() if raw_schema and raw_schema.strip() else None
    )
    if duckdb_schema is None:
        duckdb_schema = _DEFAULT_SCHEMAS.get(environment)

    return Settings(
        environment=environment,
        duckdb_path=duckdb_path,
        duckdb_read_only=duckdb_read_only,
        duckdb_schema=duckdb_schema,
    )
