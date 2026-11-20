from dataclasses import dataclass

from fastapi import Query


@dataclass
class Pagination:
    page: int
    size: int


def get_pagination(
    page: int = Query(1, ge=1, description="Page number, starting at 1"),
    size: int = Query(10, ge=1, le=100, description="Items per page (max 100)"),
) -> Pagination:
    """Reads ?page= and ?size= from the URL and validates them."""
    return Pagination(page=page, size=size)
