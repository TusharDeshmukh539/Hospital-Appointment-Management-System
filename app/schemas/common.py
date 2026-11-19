"""Building blocks shared by all schemas."""
from typing import Annotated, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, StringConstraints

T = TypeVar("T")

SortOrder = Literal["asc", "desc"]


class RequestModel(BaseModel):
    """Base class for all request bodies.

    extra="forbid" -> sending a field we do not know about gives a 422 error
    instead of being silently ignored.
    """

    model_config = ConfigDict(extra="forbid")


class ResponseModel(BaseModel):
    """Base class for responses. from_attributes lets Pydantic read ORM objects."""

    model_config = ConfigDict(from_attributes=True)


class Page(BaseModel, Generic[T]):
    """Standard wrapper for every list endpoint (pagination + total count)."""

    items: list[T]
    total: int  # total number of matching records (not just this page)
    page: int
    size: int


def make_page(items: list, total: int, page: int, size: int) -> dict:
    """Small helper that builds the dictionary for a Page response."""
    return {"items": items, "total": total, "page": page, "size": size}


# A name-like string: spaces at both ends are removed, length 2..100.
PersonName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=100)]

# Phone: optional "+" followed by 7-15 digits.
PHONE_PATTERN = r"^\+?[0-9]{7,15}$"
