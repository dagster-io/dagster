from collections.abc import Mapping, Set
from typing import TYPE_CHECKING, Any, Callable, ClassVar, Generic, Optional, TypeVar

from dagster._record import record
from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    from dagster_components.core.schema.context import ResolutionContext

FIELD_RESOLVER_PREFIX = "resolve_"

T_ResolverType = TypeVar("T_ResolverType", bound=type["Resolver"])
T_ResolvableModel = TypeVar("T_ResolvableModel", bound="ResolvableModel")

T = TypeVar("T")
T_ResolveAs = TypeVar("T_ResolveAs")


@record
class _ResolverData:
    """Container for configuration of a Resolver that is set when using the @resolver decorator."""

    resolved_type: Optional[type]
    exclude_fields: Set[str]

    def fields(self, model: "ResolvableModel", resolver: "Resolver") -> Set[str]:
        model_fields = set(model.model_fields.keys())
        resolver_fields = {
            attr[len(FIELD_RESOLVER_PREFIX) :]
            for attr in dir(resolver)
            if attr.startswith(FIELD_RESOLVER_PREFIX)
        }
        return (model_fields | resolver_fields) - self.exclude_fields - {"as"}


class Resolver(Generic[T_ResolvableModel]):
    """A Resolver is a class that can convert data contained within a ResolvableModel into an
    arbitrary output type.

    Methods on the Resolver class should be named `resolve_{fieldname}` and should return the
    resolved value for that field.


    Usage:

        .. code-block:: python

            class MyModel(ResolvableModel):
                str_val: str
                int_val: int

            class TargetType:
                def __init__(self, str_val: str, int_val_doubled: int): ...

            @resolver(
                fromtype=MyModel, totype=TargetType, exclude_fields={"int_val"}
            )
            class MyModelResolver(Resolver):
                def resolve_int_val_doubled(self, context: ResolutionContext) -> int:
                    return self.model.int_val * 2

    """

    __resolver_data__: ClassVar[_ResolverData] = _ResolverData(
        resolved_type=None, exclude_fields=set()
    )

    def __init__(self, model: T_ResolvableModel):
        self.model: T_ResolvableModel = model

    def _resolve_field(self, context: "ResolutionContext", field: str) -> Any:
        field_resolver = getattr(self, f"resolve_{field}", None)
        if field_resolver is not None:
            return field_resolver(context)
        else:
            return context.resolve_value(getattr(self.model, field))

    def get_resolved_fields(self, context: "ResolutionContext") -> Mapping[str, Any]:
        """Returns a mapping of field names to resolved values for those fields."""
        return {
            field: self._resolve_field(context, field)
            for field in self.__resolver_data__.fields(self.model, self)
        }

    def resolve_as(self, as_type: type[T_ResolveAs], context: "ResolutionContext") -> T_ResolveAs:
        """Returns an instance of `as_type` instantiated with the resolved data contained within
        this Resolver's model.
        """
        return as_type(**self.get_resolved_fields(context))

    def resolve(self, context: "ResolutionContext") -> Any:
        resolved_type = self.__resolver_data__.resolved_type or self.model.__class__
        return self.resolve_as(resolved_type, context)


class ResolvableModel(BaseModel, Generic[T]):
    __dagster_resolver__: ClassVar[type[Resolver]] = Resolver

    model_config = ConfigDict(extra="forbid")

    @property
    def _resolver(self) -> Resolver:
        return self.__dagster_resolver__(self)

    def resolve_as(self, as_type: type[T_ResolveAs], context: "ResolutionContext") -> T_ResolveAs:
        return self._resolver.resolve_as(as_type, context)

    def resolve(self, context: "ResolutionContext") -> T:
        return self._resolver.resolve(context)


def resolver(
    *,
    fromtype: type[ResolvableModel],
    totype: Optional[type] = None,
    exclude_fields: Optional[Set[str]] = None,
) -> Callable[[T_ResolverType], T_ResolverType]:
    def inner(resolver_type: T_ResolverType) -> T_ResolverType:
        resolver_type.__resolver_data__ = _ResolverData(
            resolved_type=totype, exclude_fields=exclude_fields or set()
        )
        fromtype.__dagster_resolver__ = resolver_type
        return resolver_type

    return inner
