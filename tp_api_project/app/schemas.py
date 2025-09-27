from typing import Any, Dict

from pydantic import BaseModel, ConfigDict, Field


class BusinessReviewsQuery(BaseModel):
    business_id: str = Field(..., min_length=1, description="Trustpilot business identifier")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of rows to return")
    offset: int = Field(0, ge=0, description="Row offset for pagination")

    model_config = ConfigDict(extra="forbid")


class UserReviewsQuery(BaseModel):
    user_id: str = Field(..., min_length=1, description="Trustpilot reviewer identifier")
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)

    model_config = ConfigDict(extra="forbid")


class ErrorResponse(BaseModel):
    detail: str
    context: Dict[str, Any] | None = None

    model_config = ConfigDict(extra="forbid")


class HealthResponse(BaseModel):
    status: str = Field(..., pattern="^(ok|fail)$", description="Service status indicator")

    model_config = ConfigDict(extra="forbid")
