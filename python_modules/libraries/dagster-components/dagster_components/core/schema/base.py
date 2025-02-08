from collections.abc import Mapping, Set
from typing import TYPE_CHECKING, Any, Callable, ClassVar, Generic, Optional, TypeVar

from dagster._record import record
from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    from dagster_components.core.schema.context import ResolutionContext

FIELD_RESOLVER_PREFIX = "resolve_"

T_ResolveAs = TypeVar("T_ResolveAs")
T_ResolverType = TypeVar("T_ResolverType", bound=type["Resolver"])
T_ComponentSchema = TypeVar("T_ComponentSchema", bound="ComponentSchema")


@record
class _ResolverData:
    """Container for configuration of a Resolver that is set when using the @resolver decorator."""

    resolved_type: Optional[type]
    exclude_fields: Set[str]

    def fields(self, schema: "ComponentSchema", resolver: "Resolver") -> Set[str]:
        model_fields = set(schema.model_fields.keys())
        resolver_fields = {
            attr[len(FIELD_RESOLVER_PREFIX) :]
            for attr in dir(resolver)
            if attr.startswith(FIELD_RESOLVER_PREFIX)
        }
        return (model_fields | resolver_fields) - self.exclude_fields - {"as"}


class Resolver(Generic[T_ComponentSchema]):
    """A Resolver is a class that can convert data contained within a ComponentSchema into an
    arbitrary output type.

    Methods on the Resolver class should be named `resolve_{fieldname}` and should return the
    resolved value for that field.


    Usage:

        .. code-block:: python

            class MyModel(ComponentSchema):
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

    def __init__(self, schema: T_ComponentSchema):
        self.schema: T_ComponentSchema = schema

    def _resolve_field(self, context: "ResolutionContext", field: str) -> Any:
        field_resolver = getattr(self, f"resolve_{field}", None)
        if field_resolver is not None:
            return field_resolver(context)
        else:
            return context.resolve_value(getattr(self.schema, field))

    def get_resolved_fields(self, context: "ResolutionContext") -> Mapping[str, Any]:
        """Returns a mapping of field names to resolved values for those fields."""
        return {
            field: self._resolve_field(context, field)
            for field in self.__resolver_data__.fields(self.schema, self)
        }

    def resolve_as(self, as_type: type[T_ResolveAs], context: "ResolutionContext") -> T_ResolveAs:
        """Returns an instance of `as_type` instantiated with the resolved data contained within
        this Resolver's schema.
        """
        return as_type(**self.get_resolved_fields(context))

    def resolve(self, context: "ResolutionContext") -> Any:
        resolved_type = self.__resolver_data__.resolved_type or self.schema.__class__
        return self.resolve_as(resolved_type, context)


class ComponentSchema(BaseModel):
    __dagster_resolver__: ClassVar[Optional[type[Resolver]]] = None

    model_config = ConfigDict(extra="forbid")


def set_resolver_type_of_schema(
    schema_type: type[ComponentSchema], resolver_type: type[Resolver]
) -> None:
    schema_type.__dagster_resolver__ = resolver_type


def get_resolver_type_of_schema(schema_type: type[ComponentSchema]) -> type[Resolver]:
    return schema_type.__dagster_resolver__ or Resolver


def resolver(
    *,
    fromtype: type[ComponentSchema],
    totype: Optional[type] = None,
    exclude_fields: Optional[Set[str]] = None,
) -> Callable[[T_ResolverType], T_ResolverType]:
    def inner(resolver_type: T_ResolverType) -> T_ResolverType:
        resolver_type.__resolver_data__ = _ResolverData(
            resolved_type=totype, exclude_fields=exclude_fields or set()
        )
        set_resolver_type_of_schema(fromtype, resolver_type)
        return resolver_type

    return inner
