from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields, is_dataclass
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Callable,
    Generic,
    Optional,
    TypeVar,
    Union,
    get_args,
    get_origin,
)

from dagster import _check as check
from pydantic import BaseModel, ConfigDict
from typing_extensions import Self, TypeAlias

from dagster_components.core.schema.base import ResolvableSchema

if TYPE_CHECKING:
    from dagster_components.core.schema.context import ResolutionContext


class DSLSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


EitherSchema: TypeAlias = Union[ResolvableSchema, DSLSchema]

TSchema = TypeVar("TSchema", bound=EitherSchema)


# switch to this once we have eliminated ResolvableSchema
# TSchema = TypeVar("TSchema", bound=DSLSchema)
def get_schema_type(resolvable_from_schema_type: type["ResolvableFromSchema"]) -> type[DSLSchema]:
    """Returns the first generic type argument (TSchema) of the ResolvableFromSchema instance at runtime."""
    check.param_invariant(
        issubclass(resolvable_from_schema_type, ResolvableFromSchema),
        "resolvable_from_schema_type",
    )
    check.param_invariant(
        hasattr(resolvable_from_schema_type, "__orig_bases__"),
        "resolvable_from_schema_type",
    )
    for base in resolvable_from_schema_type.__orig_bases__:  # type: ignore
        # Check if this base originates from ResolvableFromSchema
        origin = getattr(base, "__origin__", None)
        if origin is ResolvableFromSchema:
            type_args = get_args(base)
            if not type_args:
                raise ValueError(
                    "ResolvableFromSchema base found but no generic type arguments present"
                )
            return type_args[0]

    raise ValueError("No generic type arguments found in ResolvableFromSchema subclass")


T = TypeVar("T")


class ResolutionResolverFn(Generic[T]):
    def __init__(self, target_type: type[T], spec_type: type["ResolutionSpec"]):
        self.target_type = target_type
        self.spec_type = spec_type

    def from_schema(self, context: "ResolutionContext", schema: EitherSchema) -> T:
        return resolve_schema_using_spec(
            schema=schema,
            resolution_spec=self.spec_type,
            context=context,
            target_type=self.target_type,
        )

    def from_seq(self, context: "ResolutionContext", schema: Sequence[TSchema]) -> Sequence[T]:
        return [self.from_schema(context, item) for item in schema]

    def from_optional(self, context: "ResolutionContext", schema: Optional[TSchema]) -> Optional[T]:
        return self.from_schema(context, schema) if schema else None

    def from_optional_seq(
        self, context: "ResolutionContext", schema: Optional[Sequence[TSchema]]
    ) -> Optional[Sequence[T]]:
        return self.from_seq(context, schema) if schema else None


class ResolutionSpec(Generic[TSchema]):
    @classmethod
    def resolver_fn(cls, target_type: type) -> ResolutionResolverFn:
        return ResolutionResolverFn(target_type=target_type, spec_type=cls)


class ResolvableFromSchema(ResolutionSpec[TSchema]):
    @classmethod
    def from_schema(cls, context: "ResolutionContext", schema: TSchema) -> Self:
        return resolve_schema_to_resolvable(schema=schema, resolvable_type=cls, context=context)

    @classmethod
    def from_optional(
        cls, context: "ResolutionContext", schema: Optional[TSchema]
    ) -> Optional[Self]:
        return cls.from_schema(context, schema) if schema else None

    @classmethod
    def from_seq(cls, context: "ResolutionContext", schema: Sequence[TSchema]) -> Sequence[Self]:
        return [cls.from_schema(context, item) for item in schema]

    @classmethod
    def from_optional_seq(
        cls, context: "ResolutionContext", schema: Optional[Sequence[TSchema]]
    ) -> Optional[Sequence[Self]]:
        return cls.from_seq(context, schema) if schema else None


@dataclass
class ParentFn:
    callable: Callable[["ResolutionContext", Any], Any]


@dataclass
class AttrWithContextFn:
    callable: Callable[["ResolutionContext", Any], Any]


class DSLFieldResolver:
    """Contains information on how to resolve this field from a DSLSchema."""

    def __init__(
        self, fn: Union[ParentFn, AttrWithContextFn, Callable[["ResolutionContext", Any], Any]]
    ):
        if not isinstance(fn, (ParentFn, AttrWithContextFn)):
            if not callable(fn):
                check.param_invariant(
                    callable(fn),
                    "fn",
                    f"must be callable if not ParentFn or AttrWithContextFn. Got {fn}",
                )
            self.fn = AttrWithContextFn(fn)
        else:
            self.fn = fn
        super().__init__()

    @staticmethod
    def from_parent(fn: Callable[["ResolutionContext", Any], Any]):
        return DSLFieldResolver(ParentFn(fn))

    @staticmethod
    def from_spec(spec: type[ResolutionSpec], target_type: type):
        return DSLFieldResolver.from_parent(
            lambda context, schema: resolve_schema_using_spec(
                schema=schema,
                resolution_spec=spec,
                context=context,
                target_type=target_type,
            )
        )

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
        elif isinstance(self.fn, AttrWithContextFn):
            attr = getattr(schema, field_name)
            return self.fn.callable(context, attr)
        else:
            raise ValueError(f"Unsupported DSLFieldResolver type: {self.fn}")


TResolutionSpec = TypeVar("TResolutionSpec", bound=ResolutionSpec)


def get_annotation_field_resolvers(cls: type[TResolutionSpec]) -> dict[str, DSLFieldResolver]:
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
        # Handle vanilla Python classes with type annotations
        annotations = getattr(cls, "__annotations__", {})
        return {
            field_name: DSLFieldResolver.from_annotation(annotation, field_name)
            for field_name, annotation in annotations.items()
        }


TResolvableFromSchema = TypeVar("TResolvableFromSchema", bound=ResolvableFromSchema)


def resolve_fields(
    schema: EitherSchema,
    resolution_spec: type,
    context: "ResolutionContext",
) -> Mapping[str, Any]:
    """Returns a mapping of field names to resolved values for those fields."""
    return {
        field_name: resolver.execute(context=context, schema=schema, field_name=field_name)
        for field_name, resolver in get_annotation_field_resolvers(resolution_spec).items()
    }


T = TypeVar("T")


def resolve_schema_to_resolvable(
    schema: EitherSchema,
    resolvable_type: type[TResolvableFromSchema],
    context: "ResolutionContext",
) -> TResolvableFromSchema:
    return resolve_schema_using_spec(
        schema=schema,
        resolution_spec=resolvable_type,
        context=context,
        target_type=resolvable_type,
    )


def resolve_schema_using_spec(
    schema: EitherSchema,
    resolution_spec: type[TResolutionSpec],
    context: "ResolutionContext",
    target_type: type[T],
) -> T:
    return target_type(**resolve_fields(schema, resolution_spec, context))
