from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from typing import TYPE_CHECKING, Any, Callable, Generic, Optional, TypeVar

from dagster._annotations import _get_annotation_target
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._record import record
from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    from dagster_components.core.schema.context import ResolutionContext

FIELD_RESOLVER_ATTR = "__field_resolver__"

T = TypeVar("T")


def _get_default_field_resolver(field_name: str):
    def _resolver(context: "ResolutionContext", schema: "ResolvableSchema"):
        return context.resolve_value(getattr(schema, field_name))

    return _resolver


class ResolvableSchema(BaseModel, Generic[T]):
    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    def _get_resolved_type(self) -> Optional[type]:
        generic_base = next(
            base for base in self.__class__.__bases__ if issubclass(base, ResolvableSchema)
        )
        generic_args = generic_base.__pydantic_generic_metadata__["args"]
        if len(generic_args) == 0:
            # if no generic type is specified, resolve back to the base type
            return self.__class__
        elif len(generic_args) > 1:
            raise DagsterInvalidDefinitionError(
                f"Expected at most one generic argument for type: `{self.__class__}`"
            )
        resolved_type = generic_args[0]
        return resolved_type if isinstance(resolved_type, type) else None

    def _get_implicit_field_resolvers(self, target_type: type) -> Mapping[str, "FieldResolverInfo"]:
        # extract target field names directly from the target type if possible
        if issubclass(target_type, BaseModel):
            field_names = target_type.model_fields.keys()
        elif is_dataclass(target_type):
            field_names = [field.name for field in fields(target_type)]
        else:
            # assume field names in target type align with field names in the schema
            field_names = self.model_fields.keys()
        return {
            field_name: FieldResolverInfo(
                field_name=field_name, fn=_get_default_field_resolver(field_name)
            )
            for field_name in field_names
        }

    def _get_field_resolvers(self, target_type: type) -> Mapping[str, "FieldResolverInfo"]:
        return {
            **self._get_implicit_field_resolvers(target_type),
            **_get_explicit_field_resolvers(self.FieldResolvers),
            **_get_explicit_field_resolvers(target_type),
        }

    @property
    def _resolved_type(self) -> type:
        resolved_type = self._get_resolved_type()
        if resolved_type is None:
            raise DagsterInvalidDefinitionError(
                f"Could not extract resolved type instance from `{self.__class__}`. "
                "This can happen when using a ForwardRef when defining your ResolvableModel "
                '(`ResolvableModel["SomeType"]`). Consider using a concrete type or calling '
                "`resolve_as` instead."
            )
        return resolved_type

    def resolve_fields(self, target_type: type, context: "ResolutionContext") -> Mapping[str, Any]:
        """Returns a mapping of field names to resolved values for those fields."""
        return {
            field_name: resolver_info.fn(self, context)
            for field_name, resolver_info in self._get_field_resolvers(target_type).items()
        }

    def resolve_as(self, target_type: type[T], context: "ResolutionContext") -> T:
        return target_type(**self.resolve_fields(target_type, context))

    def resolve(self, context: "ResolutionContext") -> T:
        return self.resolve_as(self._resolved_type, context)

    class FieldResolvers: ...


@record
class FieldResolverInfo:
    field_name: str
    fn: Callable[["ResolutionContext", ResolvableSchema], Any]


FieldResolverArgs = ["ResolutionContext", ResolvableSchema]


def field_resolver(field_name: str) -> Any:
    def decorator(
        fn: Callable[["ResolutionContext", ResolvableSchema], T],
    ) -> Callable[["ResolutionContext", ResolvableSchema], T]:
        setattr(
            _get_annotation_target(fn),
            FIELD_RESOLVER_ATTR,
            FieldResolverInfo(field_name=field_name, fn=fn),
        )
        return fn

    return decorator


def _get_field_resolver_info(obj: Any) -> Optional[FieldResolverInfo]:
    return getattr(_get_annotation_target(obj), FIELD_RESOLVER_ATTR, None)


def _get_explicit_field_resolvers(cls: type) -> dict[str, FieldResolverInfo]:
    resolvers = {}
    for attr_name in dir(cls):
        info = _get_field_resolver_info(getattr(cls, attr_name))
        if isinstance(info, FieldResolverInfo):
            resolvers[info.field_name] = info
    return resolvers
