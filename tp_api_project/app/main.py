from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
from . import queries
from .utils import stream_csv

app = FastAPI(title="Trustpilot Take-Home API")

@app.get("/reviews/by-business")
def reviews_by_business(
    business_id: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> StreamingResponse:
    rows, header = queries.get_reviews_by_business(business_id, limit, offset)
    return StreamingResponse(stream_csv(rows, header), media_type="text/csv")

@app.get("/reviews/by-user")
def reviews_by_user(
    user_id: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> StreamingResponse:
    rows, header = queries.get_reviews_by_user(user_id, limit, offset)
    return StreamingResponse(stream_csv(rows, header), media_type="text/csv")

@app.get("/users/{user_id}")
def user_info(user_id: str) -> StreamingResponse:
    rows, header = queries.get_user_info(user_id)
    return StreamingResponse(stream_csv(rows, header), media_type="text/csv")

@app.get("/healthz")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
