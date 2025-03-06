from collections.abc import Mapping, Sequence
from dataclasses import dataclass
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
from typing_extensions import Self

if TYPE_CHECKING:
    from dagster_components.core.schema.context import ResolutionContext


class ResolvableModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


TSchema = TypeVar("TSchema", bound=ResolvableModel)


def get_schema_type(
    resolvable_from_schema_type: type["ResolvedFrom"],
) -> type[ResolvableModel]:
    """Returns the first generic type argument (TSchema) of the ResolvableFromSchema instance at runtime."""
    check.param_invariant(
        issubclass(resolvable_from_schema_type, ResolvedFrom),
        "resolvable_from_schema_type",
    )
    check.param_invariant(
        hasattr(resolvable_from_schema_type, "__orig_bases__"),
        "resolvable_from_schema_type",
    )
    for base in resolvable_from_schema_type.__orig_bases__:  # type: ignore
        # Check if this base originates from ResolvableFromSchema
        origin = getattr(base, "__origin__", None)
        if origin is ResolvedFrom:
            type_args = get_args(base)
            if not type_args:
                raise ValueError(
                    "ResolvableFromSchema base found but no generic type arguments present"
                )
            return type_args[0]

    raise ValueError("No generic type arguments found in ResolvableFromSchema subclass")


T = TypeVar("T")


class ResolutionResolverFn(Generic[T]):
    def __init__(self, target_type: type[T], spec_type: type["ResolvedKwargs"]):
        self.target_type = target_type
        self.spec_type = spec_type

    def from_schema(self, context: "ResolutionContext", schema: ResolvableModel) -> T:
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


class ResolvedKwargs(Generic[TSchema]):
    @classmethod
    def resolver_fn(cls, target_type: type) -> ResolutionResolverFn:
        return ResolutionResolverFn(target_type=target_type, spec_type=cls)


class ResolvedFrom(ResolvedKwargs[TSchema]):
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
        return [cls.from_schema(context.at_path(idx), item) for idx, item in enumerate(schema)]

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


class FieldResolver:
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
    def from_model(fn: Callable[["ResolutionContext", Any], Any]):
        return FieldResolver(ParentFn(fn))

    @staticmethod
    def from_spec(spec: type[ResolvedKwargs], target_type: type):
        return FieldResolver.from_model(
            lambda context, schema: resolve_schema_using_spec(
                schema=schema,
                resolution_spec=spec,
                context=context,
                target_type=target_type,
            )
        )

    @staticmethod
    def from_annotation(annotation: Any, field_name: str) -> "FieldResolver":
        if get_origin(annotation) is Annotated:
            args = get_args(annotation)
            resolver = next((arg for arg in args if isinstance(arg, FieldResolver)), None)
            if resolver:
                return resolver

            check.failed(f"Could not find resolver on annotation {field_name}")

        return FieldResolver.from_model(
            lambda context, schema: context.resolve_value(getattr(schema, field_name))
        )

    def execute(
        self, context: "ResolutionContext", schema: ResolvableModel, field_name: str
    ) -> Any:
        if isinstance(self.fn, ParentFn):
            return self.fn.callable(context, schema)
        elif isinstance(self.fn, AttrWithContextFn):
            attr = getattr(schema, field_name)
            return self.fn.callable(context.at_path(field_name), attr)
        else:
            raise ValueError(f"Unsupported DSLFieldResolver type: {self.fn}")


TResolutionSpec = TypeVar("TResolutionSpec", bound=ResolvedKwargs)


def get_annotation_field_resolvers(cls: type[TResolutionSpec]) -> dict[str, FieldResolver]:
    # Collect annotations from all base classes in MRO
    annotations = {}

    # Walk through all base classes in MRO
    for base in reversed(cls.__mro__):
        # Get annotations from current base class if they exist
        base_annotations = getattr(base, "__annotations__", {})
        # Update annotations dict with any new annotations found
        # Later bases don't override earlier ones due to how update works
        annotations.update(base_annotations)

    return {
        field_name: FieldResolver.from_annotation(annotation, field_name)
        for field_name, annotation in annotations.items()
    }


TResolvableFromSchema = TypeVar("TResolvableFromSchema", bound=ResolvedFrom)


def resolve_fields(
    schema: ResolvableModel,
    resolution_spec: type[TResolutionSpec],
    context: "ResolutionContext",
) -> Mapping[str, Any]:
    """Returns a mapping of field names to resolved values for those fields."""
    return {
        field_name: resolver.execute(
            context=context.at_path(field_name), schema=schema, field_name=field_name
        )
        for field_name, resolver in get_annotation_field_resolvers(resolution_spec).items()
    }


T = TypeVar("T")


def resolve_schema_to_resolvable(
    schema: ResolvableModel,
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
    schema: ResolvableModel,
    resolution_spec: type[TResolutionSpec],
    context: "ResolutionContext",
    target_type: type[T],
) -> T:
    return target_type(**resolve_fields(schema, resolution_spec, context))
