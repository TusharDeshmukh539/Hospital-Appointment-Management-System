"""Schemas for specialities."""
from typing import Annotated

from pydantic import StringConstraints

from app.schemas.common import RequestModel, ResponseModel

SpecialityName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=100)]


class SpecialityCreate(RequestModel):
    name: SpecialityName


class SpecialityUpdate(RequestModel):
    name: SpecialityName


class SpecialityOut(ResponseModel):
    id: int
    name: str