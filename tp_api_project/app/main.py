from fastapi import FastAPI, Query, Request, status
from fastapi.responses import JSONResponse, StreamingResponse

from . import queries
from .exceptions import DataAccessError, RecordNotFoundError
from .logging_config import get_logger
from .utils import stream_csv

app = FastAPI(title="Trustpilot Take-Home API")
logger = get_logger(__name__)


def _error_payload(message: str, context: dict | None = None) -> dict:
    payload = {"detail": message}
    if context:
        payload["context"] = context
    return payload


@app.exception_handler(RecordNotFoundError)
async def handle_not_found(
    request: Request, exc: RecordNotFoundError
) -> JSONResponse:
    context = dict(exc.context or {})
    context.setdefault("path", str(request.url))
    logger.info("No records found", extra={"context": context})
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=_error_payload(exc.message, context=context),
    )


@app.exception_handler(DataAccessError)
async def handle_data_access_error(
    request: Request, exc: DataAccessError
) -> JSONResponse:
    context = dict(exc.context or {})
    context.setdefault("path", str(request.url))
    logger.error(
        "Database operation failed", exc_info=exc, extra={"context": context}
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_payload(exc.message, context=context),
    )


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
