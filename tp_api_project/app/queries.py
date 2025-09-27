from typing import Any, List, Tuple

import duckdb

from .db import get_connection, qualify_table
from .exceptions import DataAccessError, RecordNotFoundError
from .logging_config import get_logger

Row = Tuple[Any, ...]
QueryResult = Tuple[List[Row], List[str]]

logger = get_logger(__name__)


def get_reviews_by_business(
    business_id: str, limit: int = 100, offset: int = 0
) -> QueryResult:
    params = [business_id, limit, offset]
    with get_connection() as con:
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
            rows = result.fetchall()
            header = [d[0] for d in result.description]
        except duckdb.Error as exc:
            logger.exception(
                "Failed to fetch reviews by business",
                extra={"context": {"business_id": business_id}},
            )
            raise DataAccessError(
                "Unable to retrieve reviews for the requested business.",
                context={"business_id": business_id},
            ) from exc
    if not rows:
        context = {"business_id": business_id}
        logger.info("No reviews found for business", extra={"context": context})
        raise RecordNotFoundError(
            "No reviews were found for the requested business.",
            context=context,
        )
    return rows, header


def get_reviews_by_user(user_id: str, limit: int = 100, offset: int = 0) -> QueryResult:
    params = [user_id, limit, offset]
    with get_connection() as con:
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
            rows = result.fetchall()
            header = [d[0] for d in result.description]
        except duckdb.Error as exc:
            logger.exception(
                "Failed to fetch reviews by user",
                extra={"context": {"user_id": user_id}},
            )
            raise DataAccessError(
                "Unable to retrieve reviews for the requested user.",
                context={"user_id": user_id},
            ) from exc
    if not rows:
        context = {"user_id": user_id}
        logger.info("No reviews found for user", extra={"context": context})
        raise RecordNotFoundError(
            "No reviews were found for the requested user.",
            context=context,
        )
    return rows, header


def get_user_info(user_id: str) -> QueryResult:
    params = [user_id]
    with get_connection() as con:
        table_ref = qualify_table(con, "crt_tp_reviews")
        sql = f"""
        select distinct reviewer_id, reviewer_name, email_address, reviewer_country
        from {table_ref}
        where reviewer_id = ?
        """
        try:
            result = con.execute(sql, params)
            rows = result.fetchall()
            header = [d[0] for d in result.description]
        except duckdb.Error as exc:
            logger.exception(
                "Failed to fetch user information",
                extra={"context": {"user_id": user_id}},
            )
            raise DataAccessError(
                "Unable to retrieve user information.",
                context={"user_id": user_id},
            ) from exc
    if not rows:
        context = {"user_id": user_id}
        logger.info("No user information found", extra={"context": context})
        raise RecordNotFoundError(
            "No user information was found for the requested user.",
            context=context,
        )
    return rows, header
