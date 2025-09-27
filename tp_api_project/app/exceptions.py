from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(slots=True)
class DataAccessError(Exception):
    """Raised when the API cannot complete a database operation."""

    message: str
    context: Mapping[str, Any] | None = None
    status_code: int = 500

    def __post_init__(self) -> None:
        Exception.__init__(self, self.message)

    def __str__(self) -> str:  # pragma: no cover
        return self.message


@dataclass(slots=True)
class RecordNotFoundError(DataAccessError):
    """Raised when no rows match the supplied filters."""

    status_code: int = 404
