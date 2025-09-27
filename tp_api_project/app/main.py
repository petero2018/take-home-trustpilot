from typing import Annotated, Any

from fastapi import Depends, FastAPI, Query, Request, status
from fastapi.responses import JSONResponse, StreamingResponse

from . import queries
from .exceptions import DataAccessError, RecordNotFoundError
from .logging_config import get_logger
from .schemas import (
    BusinessReviewsQuery,
    ErrorResponse,
    HealthResponse,
    UserReviewsQuery,
)
from .utils import stream_csv

app = FastAPI(title="Trustpilot Take-Home API")
logger = get_logger(__name__)


def _business_query_params(
    business_id: Annotated[str, Query(min_length=1)] ,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> BusinessReviewsQuery:
    return BusinessReviewsQuery.model_validate(
        {"business_id": business_id, "limit": limit, "offset": offset}
    )


def _user_query_params(
    user_id: Annotated[str, Query(min_length=1)],
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> UserReviewsQuery:
    return UserReviewsQuery.model_validate(
        {"user_id": user_id, "limit": limit, "offset": offset}
    )


def _error_payload(message: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    return ErrorResponse(detail=message, context=context).model_dump(exclude_none=True)


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
    params: Annotated[BusinessReviewsQuery, Depends(_business_query_params)]
) -> StreamingResponse:
    rows, header = queries.get_reviews_by_business(
        params.business_id, params.limit, params.offset
    )
    return StreamingResponse(stream_csv(rows, header), media_type="text/csv")


@app.get("/reviews/by-user")
def reviews_by_user(
    params: Annotated[UserReviewsQuery, Depends(_user_query_params)]
) -> StreamingResponse:
    rows, header = queries.get_reviews_by_user(
        params.user_id, params.limit, params.offset
    )
    return StreamingResponse(stream_csv(rows, header), media_type="text/csv")


@app.get("/users/{user_id}")
def user_info(user_id: str) -> StreamingResponse:
    rows, header = queries.get_user_info(user_id)
    return StreamingResponse(stream_csv(rows, header), media_type="text/csv")


@app.get("/healthz", response_model=HealthResponse)
def healthcheck() -> HealthResponse:
    return HealthResponse(status="ok")
