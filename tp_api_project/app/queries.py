from typing import Any, List, Tuple

from .db import get_connection, qualify_table

Row = Tuple[Any, ...]
QueryResult = Tuple[List[Row], List[str]]


def get_reviews_by_business(
    business_id: str, limit: int = 100, offset: int = 0
) -> QueryResult:
    con = get_connection()
    table_ref = qualify_table(con, "crt_tp_reviews")
    sql = f"""
    select *
    from {table_ref}
    where business_id = ?
    order by review_date desc
    limit ? offset ?
    """
    return (
        con.execute(sql, [business_id, limit, offset]).fetchall(),
        [d[0] for d in con.description],
    )


def get_reviews_by_user(user_id: str, limit: int = 100, offset: int = 0) -> QueryResult:
    con = get_connection()
    table_ref = qualify_table(con, "crt_tp_reviews")
    sql = f"""
    select *
    from {table_ref}
    where reviewer_id = ?
    order by review_date desc
    limit ? offset ?
    """
    return (
        con.execute(sql, [user_id, limit, offset]).fetchall(),
        [d[0] for d in con.description],
    )


def get_user_info(user_id: str) -> QueryResult:
    con = get_connection()
    table_ref = qualify_table(con, "crt_tp_reviews")
    sql = f"""
    select distinct reviewer_id, reviewer_name, email_address, reviewer_country
    from {table_ref}
    where reviewer_id = ?
    """
    return (
        con.execute(sql, [user_id]).fetchall(),
        [d[0] for d in con.description],
    )
