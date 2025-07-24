from functools import cached_property
from typing import TYPE_CHECKING, Any, Optional

from pydantic import BaseModel, ConfigDict
from typing_extensions import Self


class DagsterModel(BaseModel):
    """Standardizes on Pydantic settings that are stricter than the default.
    - Frozen, to avoid complexity caused by mutation.
    - extra=forbid, to avoid bugs caused by accidentally constructing with the wrong arguments.
    - arbitrary_types_allowed, to allow non-model class params to be validated with isinstance.
    - Avoid pydantic reading a cached property class as part of the schema.
    """

    if TYPE_CHECKING:
        # without this, the type checker does not understand the constructor kwargs on subclasses
        def __init__(self, **data: Any) -> None: ...

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        arbitrary_types_allowed=True,
        ignored_types=(cached_property,),
    )

    def model_copy(self, *, update: Optional[dict[str, Any]] = None) -> Self:  # pyright: ignore[reportIncompatibleMethodOverride]
        return super().model_copy(update=update)

    @classmethod
    def model_construct(cls, **kwargs: Any) -> Self:  # pyright: ignore[reportIncompatibleMethodOverride]
        return super().model_construct(**kwargs)
