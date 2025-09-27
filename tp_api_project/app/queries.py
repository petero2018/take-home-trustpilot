from .db import get_connection

def get_reviews_by_business(business_id: str, limit: int = 100, offset: int = 0):
    sql = """
    select *
    from crt_tp_reviews
    where business_id = ?
    order by review_date desc
    limit ? offset ?
    """
    con = get_connection()
    return con.execute(sql, [business_id, limit, offset]).fetchall(), [d[0] for d in con.description]

def get_reviews_by_user(user_id: str, limit: int = 100, offset: int = 0):
    sql = """
    select *
    from crt_tp_reviews
    where reviewer_id = ?
    order by review_date desc
    limit ? offset ?
    """
    con = get_connection()
    return con.execute(sql, [user_id, limit, offset]).fetchall(), [d[0] for d in con.description]

def get_user_info(user_id: str):
    sql = """
    select distinct reviewer_id, reviewer_name, email_address, reviewer_country
    from crt_tp_reviews
    where reviewer_id = ?
    """
    con = get_connection()
    return con.execute(sql, [user_id]).fetchall(), [d[0] for d in con.description]