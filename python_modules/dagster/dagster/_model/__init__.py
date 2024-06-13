from functools import cached_property
from typing import TYPE_CHECKING, Any, Dict, Hashable, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, PrivateAttr
from typing_extensions import Annotated, Self, TypeAlias

# decorator based models public API
from .decorator import (
    IHaveNew as IHaveNew,
    LegacyNamedTupleMixin as LegacyNamedTupleMixin,
    as_dict as as_dict,
    copy as copy,
    dagster_model as dagster_model,
    dagster_model_custom as dagster_model_custom,
    has_generated_new as has_generated_new,
    is_dagster_model as is_dagster_model,
)
from .pydantic_compat_layer import USING_PYDANTIC_2

if USING_PYDANTIC_2:
    from pydantic import InstanceOf as InstanceOf  # type: ignore
else:
    # fallback to a no-op on pydantic 1 as there is no equivalent
    AnyType = TypeVar("AnyType")
    InstanceOf: TypeAlias = Annotated[AnyType, ...]


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

    if TYPE_CHECKING:
        # without this, the type checker does not understand the constructor kwargs on subclasses
        def __init__(self, **data: Any) -> None: ...

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
