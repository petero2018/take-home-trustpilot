import duckdb
from duckdb import DuckDBPyConnection
from typing import Dict, Optional

from .config import get_settings


def get_connection() -> DuckDBPyConnection:
    settings = get_settings()
    connection = duckdb.connect(settings.duckdb_path, read_only=settings.duckdb_read_only)
    schema = (settings.duckdb_schema or "").strip()
    if schema:
        sanitized_schema = schema.replace("'", "''")
        connection.execute(f"SET schema '{sanitized_schema}'")
    return connection


_TABLE_SCHEMA_CACHE: Dict[str, Optional[str]] = {}


def _quote_identifier(identifier: str) -> str:
    return f'"{identifier.replace("\"", "\"\"")}"'


def qualify_table(connection: DuckDBPyConnection, table_name: str) -> str:
    settings = get_settings()
    if settings.duckdb_schema:
        return f"{_quote_identifier(settings.duckdb_schema)}.{_quote_identifier(table_name)}"

    if table_name not in _TABLE_SCHEMA_CACHE:
        row = connection.execute(
            "select table_schema from information_schema.tables where table_name = ? order by table_schema limit 1",
            [table_name],
        ).fetchone()
        schema = row[0] if row and row[0] else None
        _TABLE_SCHEMA_CACHE[table_name] = schema

    schema = _TABLE_SCHEMA_CACHE[table_name]
    if schema:
        return f"{_quote_identifier(schema)}.{_quote_identifier(table_name)}"
    return _quote_identifier(table_name)
