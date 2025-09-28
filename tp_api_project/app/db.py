"""Connection pooling and DuckDB helpers for the Trustpilot API."""

import threading
from contextlib import contextmanager
from queue import Empty, Queue
from typing import Dict, Iterator, Optional

import duckdb
from duckdb import DuckDBPyConnection

from .config import get_settings
from .exceptions import DataAccessError


class DuckDBConnectionPool:
    """A lightweight thread-safe pool that recycles DuckDB connections."""

    def __init__(
        self,
        database_path: str,
        read_only: bool,
        schema: str | None,
        max_size: int,
        timeout: float,
    ) -> None:
        """Capture configuration and seed the internal state."""
        self._database_path = database_path
        self._read_only = read_only
        self._schema = (schema or "").strip() or None
        self._queue: Queue[DuckDBPyConnection] = Queue(maxsize=max_size)
        self._timeout = timeout
        self._lock = threading.Lock()
        self._active_connections = 0

    def _initialize_connection(self) -> DuckDBPyConnection:
        """Open a new DuckDB connection respecting the configured schema."""
        connection = duckdb.connect(
            self._database_path,
            read_only=self._read_only,
        )
        if self._schema:
            sanitized_schema = self._schema.replace("'", "''")
            connection.execute(f"SET schema '{sanitized_schema}'")
        return connection

    @contextmanager
    def acquire(self) -> Iterator[DuckDBPyConnection]:
        """Yield a pooled connection, blocking up to the configured timeout."""
        connection: Optional[DuckDBPyConnection] = None
        try:
            try:
                connection = self._queue.get_nowait()
            except Empty:
                with self._lock:
                    if self._active_connections < self._queue.maxsize:
                        connection = self._initialize_connection()
                        self._active_connections += 1
                    else:
                        try:
                            connection = self._queue.get(timeout=self._timeout)
                        except Empty as exc:
                            raise DataAccessError(
                                "No database connections are available. Please try again shortly.",
                                context={"timeout": self._timeout},
                                status_code=503,
                            ) from exc
            yield connection
        finally:
            if connection is None:
                return
            # DuckDB connections do not expose a "closed" flag, so we optimistically
            # recycle the handle. If the user closed it manually we drop it instead of
            # returning it to the pool.
            is_closed = getattr(connection, "is_closed", None)
            if callable(is_closed) and is_closed():
                with self._lock:
                    self._active_connections = max(0, self._active_connections - 1)
                return
            self._queue.put(connection)


_TABLE_SCHEMA_CACHE: Dict[str, Optional[str]] = {}
_POOL_CACHE: Dict[tuple, DuckDBConnectionPool] = {}
_POOL_LOCK = threading.Lock()


def _quote_identifier(identifier: str) -> str:
    """Return a DuckDB-safe quoted identifier."""
    return f'"{identifier.replace("\"", "\"\"")}"'


@contextmanager
def get_connection() -> Iterator[DuckDBPyConnection]:
    """Obtain a pooled DuckDB connection based on application settings."""
    settings = get_settings()
    if settings.database_backend != "duckdb":
        raise NotImplementedError(f"Unsupported database backend '{settings.database_backend}'.")

    cache_key = (
        settings.duckdb_path,
        settings.duckdb_read_only,
        settings.duckdb_schema,
        settings.connection_pool_size,
        settings.connection_pool_timeout,
    )

    with _POOL_LOCK:
        pool = _POOL_CACHE.get(cache_key)
        if pool is None:
            pool = DuckDBConnectionPool(
                database_path=settings.duckdb_path,
                read_only=settings.duckdb_read_only,
                schema=settings.duckdb_schema,
                max_size=settings.connection_pool_size,
                timeout=settings.connection_pool_timeout,
            )
            _POOL_CACHE[cache_key] = pool

    with pool.acquire() as connection:
        yield connection


def qualify_table(connection: DuckDBPyConnection, table_name: str) -> str:
    """Return a table reference qualified with the appropriate schema."""
    settings = get_settings()
    if settings.duckdb_schema:
        return f"{_quote_identifier(settings.duckdb_schema)}.{_quote_identifier(table_name)}"

    cache_key = (settings.duckdb_path, table_name)
    if cache_key not in _TABLE_SCHEMA_CACHE:
        row = connection.execute(
            "select table_schema from information_schema.tables where table_name = ? order by table_schema limit 1",
            [table_name],
        ).fetchone()
        schema = row[0] if row and row[0] else None
        _TABLE_SCHEMA_CACHE[cache_key] = schema

    schema = _TABLE_SCHEMA_CACHE[cache_key]
    if schema:
        return f"{_quote_identifier(schema)}.{_quote_identifier(table_name)}"
    return _quote_identifier(table_name)
