from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Callable,
    Generic,
    Optional,
    TypeVar,
    get_args,
    get_origin,
)

from dagster._core.errors import DagsterInvalidDefinitionError
from pydantic import BaseModel, ConfigDict

from dagster_components.core.schema.metadata import FieldInfo

if TYPE_CHECKING:
    from dagster_components.core.schema.context import ResolutionContext


T = TypeVar("T")


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
        resolved_type = next(iter(generic_args))
        return resolved_type if isinstance(resolved_type, type) else None

    def _get_field_resolvers(self, target_type: type) -> Mapping[str, "FieldResolver"]:
        return {
            # extract field resolvers from annotations if possible, otherwise extract from the schema type
            **(
                _get_annotation_field_resolvers(target_type)
                or _get_annotation_field_resolvers(self.__class__)
            )
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
            field_name: resolver.fn(context, self)
            for field_name, resolver in self._get_field_resolvers(target_type).items()
        }

    def resolve_as(self, target_type: type[T], context: "ResolutionContext") -> T:
        return target_type(**self.resolve_fields(target_type, context))

    def resolve(self, context: "ResolutionContext") -> T:
        return self.resolve_as(self._resolved_type, context)


class FieldResolver(FieldInfo):
    """Contains information on how to resolve this field from a ResolvableSchema."""

    def __init__(self, fn: Callable[["ResolutionContext", Any], Any]):
        self.fn = fn
        super().__init__()

    @staticmethod
    def from_annotation(annotation: Any, field_name: str) -> "FieldResolver":
        if get_origin(annotation) is Annotated:
            args = get_args(annotation)
            resolver = next((arg for arg in args if isinstance(arg, FieldResolver)), None)
            if resolver:
                return resolver
        return FieldResolver(
            lambda context, schema: context.resolve_value(getattr(schema, field_name))
        )


def _get_annotation_field_resolvers(cls: type) -> dict[str, FieldResolver]:
    if issubclass(cls, BaseModel):
        # neither pydantic's Field.annotation nor Field.rebuild_annotation() actually
        # return the original annotation, so we have to walk the mro to get them
        annotations = {}
        for field_name in cls.model_fields:
            for base in cls.__mro__:
                if field_name in getattr(base, "__annotations__", {}):
                    annotations[field_name] = base.__annotations__[field_name]
                    break
        return {
            field_name: FieldResolver.from_annotation(annotation, field_name)
            for field_name, annotation in annotations.items()
        }
    elif is_dataclass(cls):
        return {
            field.name: FieldResolver.from_annotation(field.type, field.name)
            for field in fields(cls)
        }
    else:
        return {}
