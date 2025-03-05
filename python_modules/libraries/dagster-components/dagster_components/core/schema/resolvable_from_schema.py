from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from typing import TYPE_CHECKING, Annotated, Any, Callable, Generic, TypeVar, get_args, get_origin

from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    from dagster_components.core.schema.context import ResolutionContext


class DSLSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


TSchema = TypeVar("TSchema", bound=DSLSchema)


class ResolvableFromSchema(Generic[TSchema]): ...


class DSLFieldResolver:
    """Contains information on how to resolve this field from a DSLSchema."""

    def __init__(self, fn: Callable[["ResolutionContext", Any], Any]):
        self.fn = fn
        super().__init__()

    @staticmethod
    def from_parent(fn: Callable[["ResolutionContext", Any], Any]):
        return DSLFieldResolver(fn)

    @staticmethod
    def from_annotation(annotation: Any, field_name: str) -> "DSLFieldResolver":
        if get_origin(annotation) is Annotated:
            args = get_args(annotation)
            resolver = next((arg for arg in args if isinstance(arg, DSLFieldResolver)), None)
            if resolver:
                return resolver
        return DSLFieldResolver(
            lambda context, schema: context.resolve_value(getattr(schema, field_name))
        )


def get_annotation_field_resolvers(cls: type) -> dict[str, DSLFieldResolver]:
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
            field_name: DSLFieldResolver.from_annotation(annotation, field_name)
            for field_name, annotation in annotations.items()
        }
    elif is_dataclass(cls):
        return {
            field.name: DSLFieldResolver.from_annotation(field.type, field.name)
            for field in fields(cls)
        }
    else:
        return {}


def resolve_fields(
    schema: DSLSchema, target_type: type, context: "ResolutionContext"
) -> Mapping[str, Any]:
    """Returns a mapping of field names to resolved values for those fields."""
    return {
        field_name: resolver.fn(context, schema)
        for field_name, resolver in get_annotation_field_resolvers(target_type).items()
    }


TResolvableFromSchema = TypeVar("TResolvableFromSchema", bound=ResolvableFromSchema)


def resolve_schema_to_resolvable(
    schema: DSLSchema,
    resolvable_from_schema_type: type[TResolvableFromSchema],
    context: "ResolutionContext",
) -> TResolvableFromSchema:
    return resolvable_from_schema_type(
        **resolve_fields(schema, resolvable_from_schema_type, context)
    )
