from functools import cached_property
from typing import Any, Dict, Hashable, Optional

from pydantic import BaseModel, ConfigDict, PrivateAttr
from typing_extensions import Self

from .pydantic_compat_layer import USING_PYDANTIC_2


class DagsterModel(BaseModel):
    """Standardizes on Pydantic settings that are stricter than the default.
    - Frozen, to avoid complexity caused by mutation.
    - extra=forbid, to avoid bugs caused by accidentally constructing with the wrong arguments.
    - arbitrary_types_allowed, to allow non-model class params to be validated with isinstance.
    - Avoid pydantic reading a cached property class as part of the schema.
    """

    if not USING_PYDANTIC_2:
        # the setattr approach for cached_method works in pydantic 2 so only declare the PrivateAttr
        # in pydantic 1 as it has non trivial performance impact
        _cached_method_cache__internal__: Dict[Hashable, Any] = PrivateAttr(default_factory=dict)

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)

    if USING_PYDANTIC_2:
        model_config = ConfigDict(  # type: ignore
            extra="forbid",
            frozen=True,
            arbitrary_types_allowed=True,
            ignored_types=(cached_property,),
        )
    else:

        class Config:
            extra = "forbid"
            frozen = True
            arbitrary_types_allowed = True
            keep_untouched = (cached_property,)

    def model_copy(self, *, update: Optional[Dict[str, Any]] = None) -> Self:
        if USING_PYDANTIC_2:
            return super().model_copy(update=update)  # type: ignore
        else:
            return super().copy(update=update)

    @classmethod
    def model_construct(cls, **kwargs: Any) -> Self:
        if USING_PYDANTIC_2:
            return super().model_construct(**kwargs)  # type: ignore
        else:
            return super().construct(**kwargs)
