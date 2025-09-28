"""Database access helpers that back the FastAPI review endpoints."""

from contextlib import ExitStack
from typing import Any, Iterable, Iterator, List, Tuple

import duckdb

from .db import get_connection, qualify_table
from .exceptions import DataAccessError, RecordNotFoundError
from .logging_config import get_logger

Row = Tuple[Any, ...]
QueryResult = Tuple[Iterable[Row], List[str]]

_STREAM_BATCH_SIZE = 1024

logger = get_logger(__name__)


def _row_iterator(
    result: duckdb.DuckDBPyRelation, stack: ExitStack, first_batch: list[Row]
) -> Iterator[Row]:
    """Yield rows from a DuckDB cursor while keeping the connection alive."""

    def iterator() -> Iterator[Row]:
        try:
            batch = first_batch
            while batch:
                for row in batch:
                    yield row
                batch = result.fetchmany(_STREAM_BATCH_SIZE)
        finally:
            stack.close()

    return iterator()


def get_reviews_by_business(business_id: str, limit: int = 100, offset: int = 0) -> QueryResult:
    """Fetch reviews for a business ordered by most recent first."""
    params = [business_id, limit, offset]
    stack = ExitStack()
    con = stack.enter_context(get_connection())
    table_ref = qualify_table(con, "crt_tp_reviews")
    sql = f"""
    select *
    from {table_ref}
    where business_id = ?
    order by review_date desc
    limit ? offset ?
    """
    try:
        result = con.execute(sql, params)
        header = [d[0] for d in result.description]
    except duckdb.Error as exc:
        stack.close()
        logger.exception(
            "Failed to fetch reviews by business",
            extra={"context": {"business_id": business_id}},
        )
        raise DataAccessError(
            "Unable to retrieve reviews for the requested business.",
            context={"business_id": business_id},
        ) from exc
    first_batch = result.fetchmany(_STREAM_BATCH_SIZE)
    if not first_batch:
        stack.close()
        context = {"business_id": business_id}
        logger.info("No reviews found for business", extra={"context": context})
        raise RecordNotFoundError(
            "No reviews were found for the requested business.",
            context=context,
        )
    rows = _row_iterator(result, stack, first_batch)
    return rows, header


def get_reviews_by_user(user_id: str, limit: int = 100, offset: int = 0) -> QueryResult:
    """Fetch reviews authored by a single user ordered by most recent first."""
    params = [user_id, limit, offset]
    stack = ExitStack()
    con = stack.enter_context(get_connection())
    table_ref = qualify_table(con, "crt_tp_reviews")
    sql = f"""
    select *
    from {table_ref}
    where reviewer_id = ?
    order by review_date desc
    limit ? offset ?
    """
    try:
        result = con.execute(sql, params)
        header = [d[0] for d in result.description]
    except duckdb.Error as exc:
        stack.close()
        logger.exception(
            "Failed to fetch reviews by user",
            extra={"context": {"user_id": user_id}},
        )
        raise DataAccessError(
            "Unable to retrieve reviews for the requested user.",
            context={"user_id": user_id},
        ) from exc
    first_batch = result.fetchmany(_STREAM_BATCH_SIZE)
    if not first_batch:
        stack.close()
        context = {"user_id": user_id}
        logger.info("No reviews found for user", extra={"context": context})
        raise RecordNotFoundError(
            "No reviews were found for the requested user.",
            context=context,
        )
    rows = _row_iterator(result, stack, first_batch)
    return rows, header


def get_user_info(user_id: str) -> QueryResult:
    """Fetch distinct reviewer metadata for the requested user."""
    params = [user_id]
    stack = ExitStack()
    con = stack.enter_context(get_connection())
    table_ref = qualify_table(con, "crt_tp_reviews")
    sql = f"""
    select distinct reviewer_id, reviewer_name, email_address, reviewer_country
    from {table_ref}
    where reviewer_id = ?
    """
    try:
        result = con.execute(sql, params)
        header = [d[0] for d in result.description]
    except duckdb.Error as exc:
        stack.close()
        logger.exception(
            "Failed to fetch user information",
            extra={"context": {"user_id": user_id}},
        )
        raise DataAccessError(
            "Unable to retrieve user information.",
            context={"user_id": user_id},
        ) from exc
    first_batch = result.fetchmany(_STREAM_BATCH_SIZE)
    if not first_batch:
        stack.close()
        context = {"user_id": user_id}
        logger.info("No user information found", extra={"context": context})
        raise RecordNotFoundError(
            "No user information was found for the requested user.",
            context=context,
        )
    rows = _row_iterator(result, stack, first_batch)
    return rows, header
