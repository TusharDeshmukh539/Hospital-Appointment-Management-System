from typing import Annotated, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, StringConstraints


T = TypeVar("T")

SortOrder = Literal["asc", "desc"]

PersonName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=2, max_length=100)
]

PHONE_PATTERN = r"^\+?[0-9]{10,13}$"


class RequestModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ResponseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int


def make_page(items: list, total: int, page: int, size: int) -> dict:
    return {"items": items, "total": total, "page": page, "size": size}