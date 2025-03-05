from collections.abc import Mapping
from dataclasses import dataclass, fields, is_dataclass
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Callable,
    Generic,
    TypeVar,
    Union,
    get_args,
    get_origin,
)

from pydantic import BaseModel, ConfigDict
from typing_extensions import TypeAlias

from dagster_components.core.schema.base import ResolvableSchema

if TYPE_CHECKING:
    from dagster_components.core.schema.context import ResolutionContext


class DSLSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


EitherSchema: TypeAlias = Union[ResolvableSchema, DSLSchema]

TSchema = TypeVar("TSchema", bound=EitherSchema)
# switch to this once we have eliminated ResolvableSchema
# TSchema = TypeVar("TSchema", bound=DSLSchema)


class ResolvableFromSchema(Generic[TSchema]): ...


@dataclass
class ParentFn:
    callable: Callable[["ResolutionContext", Any], Any]


@dataclass
class PropNoContextFn:
    callable: Callable[[Any], Any]


class DSLFieldResolver:
    """Contains information on how to resolve this field from a DSLSchema."""

    def __init__(self, fn: Union[ParentFn, PropNoContextFn, Callable[[Any], Any]]):
        self.fn = fn if isinstance(fn, (ParentFn, PropNoContextFn)) else PropNoContextFn(fn)
        super().__init__()

    @staticmethod
    def from_parent(fn: Callable[["ResolutionContext", Any], Any]):
        return DSLFieldResolver(ParentFn(fn))

    @staticmethod
    def from_annotation(annotation: Any, field_name: str) -> "DSLFieldResolver":
        if get_origin(annotation) is Annotated:
            args = get_args(annotation)
            resolver = next((arg for arg in args if isinstance(arg, DSLFieldResolver)), None)
            if resolver:
                return resolver
        return DSLFieldResolver.from_parent(
            lambda context, schema: context.resolve_value(getattr(schema, field_name))
        )

    def execute(self, context: "ResolutionContext", schema: EitherSchema, field_name: str) -> Any:
        if isinstance(self.fn, ParentFn):
            return self.fn.callable(context, schema)
        elif isinstance(self.fn, PropNoContextFn):
            attr = getattr(schema, field_name)
            return self.fn.callable(attr)
        else:
            raise ValueError(f"Unsupported DSLFieldResolver type: {self.fn}")


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
    schema: EitherSchema,
    target_type: type,
    context: "ResolutionContext",
) -> Mapping[str, Any]:
    """Returns a mapping of field names to resolved values for those fields."""
    return {
        field_name: resolver.execute(context=context, schema=schema, field_name=field_name)
        for field_name, resolver in get_annotation_field_resolvers(target_type).items()
    }


TResolvableFromSchema = TypeVar("TResolvableFromSchema", bound=ResolvableFromSchema)


def resolve_schema_to_resolvable(
    schema: EitherSchema,
    resolvable_from_schema_type: type[TResolvableFromSchema],
    context: "ResolutionContext",
) -> TResolvableFromSchema:
    return resolvable_from_schema_type(
        **resolve_fields(schema, resolvable_from_schema_type, context)
    )
