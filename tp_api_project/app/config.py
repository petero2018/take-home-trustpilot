import os
from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

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


def _to_int(value: str | None, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _to_float(value: str | None, default: float) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


class Settings(BaseModel):
    environment: Literal["dev", "prod"]
    duckdb_path: str
    duckdb_read_only: bool
    duckdb_schema: str | None
    database_backend: str = "duckdb"
    connection_pool_size: int = Field(default=5, ge=1)
    connection_pool_timeout: float = Field(default=5.0, gt=0)

    model_config = ConfigDict(frozen=True)


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
    duckdb_schema = raw_schema.strip() if raw_schema and raw_schema.strip() else None
    if duckdb_schema is None:
        duckdb_schema = _DEFAULT_SCHEMAS.get(environment)

    raw_backend = os.getenv("TP_API_DB_BACKEND")
    database_backend = (
        raw_backend.strip().lower() if raw_backend and raw_backend.strip() else "duckdb"
    )

    pool_size = max(1, _to_int(os.getenv("TP_API_DB_POOL_SIZE"), 5))
    pool_timeout = max(0.1, _to_float(os.getenv("TP_API_DB_POOL_TIMEOUT"), 5.0))

    return Settings(
        environment=environment,
        duckdb_path=duckdb_path,
        duckdb_read_only=duckdb_read_only,
        duckdb_schema=duckdb_schema,
        database_backend=database_backend,
        connection_pool_size=pool_size,
        connection_pool_timeout=pool_timeout,
    )
