from collections.abc import Sequence
from typing import Generic, TypeVar

from pydantic import BaseModel, computed_field

T_co = TypeVar("T_co", covariant=True)


class DgApiList(BaseModel, Generic[T_co]):
    items: Sequence[T_co]

    @computed_field
    @property
    def total(self) -> int:
        return len(self.items)


class DgApiTruncatedList(BaseModel, Generic[T_co]):
    items: Sequence[T_co]
    total: int


class DgApiPaginatedList(BaseModel, Generic[T_co]):
    items: Sequence[T_co]
    cursor: str | None = None
    has_more: bool = False
