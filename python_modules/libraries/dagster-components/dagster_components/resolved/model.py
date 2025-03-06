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
    from dagster_components.resolved.context import ResolutionContext


class ResolvableModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


TModel = TypeVar("TModel", bound=ResolvableModel)


def get_model_type(
    resolved_from_type: type["ResolvedFrom"],
) -> type[ResolvableModel]:
    """Returns the first generic type argument (TSchema) of the ResolvableFromSchema instance at runtime."""
    check.param_invariant(
        issubclass(resolved_from_type, ResolvedFrom),
        "resolvable_from_type",
    )
    check.param_invariant(
        hasattr(resolved_from_type, "__orig_bases__"),
        "resolvable_from_type",
    )
    for base in resolved_from_type.__orig_bases__:  # type: ignore
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

    def from_model(self, context: "ResolutionContext", model: ResolvableModel) -> T:
        return resolve_model_using_kwargs_cls(
            model=model,
            kwargs_cls=self.spec_type,
            context=context,
            target_type=self.target_type,
        )

    def from_seq(self, context: "ResolutionContext", model: Sequence[TModel]) -> Sequence[T]:
        return [self.from_model(context, item) for item in model]

    def from_optional(self, context: "ResolutionContext", model: Optional[TModel]) -> Optional[T]:
        return self.from_model(context, model) if model else None

    def from_optional_seq(
        self, context: "ResolutionContext", model: Optional[Sequence[TModel]]
    ) -> Optional[Sequence[T]]:
        return self.from_seq(context, model) if model else None


class ResolvedKwargs(Generic[TModel]):
    @classmethod
    def resolver_fn(cls, target_type: type) -> ResolutionResolverFn:
        return ResolutionResolverFn(target_type=target_type, spec_type=cls)


class ResolvedFrom(ResolvedKwargs[TModel]):
    @classmethod
    def from_model(cls, context: "ResolutionContext", model: TModel) -> Self:
        return resolve_model(model=model, resolvable_type=cls, context=context)

    @classmethod
    def from_optional(cls, context: "ResolutionContext", model: Optional[TModel]) -> Optional[Self]:
        return cls.from_model(context, model) if model else None

    @classmethod
    def from_seq(cls, context: "ResolutionContext", model: Sequence[TModel]) -> Sequence[Self]:
        return [cls.from_model(context.at_path(idx), item) for idx, item in enumerate(model)]

    @classmethod
    def from_optional_seq(
        cls, context: "ResolutionContext", model: Optional[Sequence[TModel]]
    ) -> Optional[Sequence[Self]]:
        return cls.from_seq(context, model) if model else None


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
            lambda context, model: resolve_model_using_kwargs_cls(
                model=model,
                kwargs_cls=spec,
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
            lambda context, model: context.resolve_value(getattr(model, field_name))
        )

    def execute(self, context: "ResolutionContext", model: ResolvableModel, field_name: str) -> Any:
        if isinstance(self.fn, ParentFn):
            return self.fn.callable(context, model)
        elif isinstance(self.fn, AttrWithContextFn):
            attr = getattr(model, field_name)
            return self.fn.callable(context.at_path(field_name), attr)
        else:
            raise ValueError(f"Unsupported DSLFieldResolver type: {self.fn}")


TResolvedKwargs = TypeVar("TResolvedKwargs", bound=ResolvedKwargs)


def get_annotation_field_resolvers(kwargs_cls: type[TResolvedKwargs]) -> dict[str, FieldResolver]:
    # Collect annotations from all base classes in MRO
    annotations = {}

    # Walk through all base classes in MRO
    for base in reversed(kwargs_cls.__mro__):
        # Get annotations from current base class if they exist
        base_annotations = getattr(base, "__annotations__", {})
        # Update annotations dict with any new annotations found
        # Later bases don't override earlier ones due to how update works
        annotations.update(base_annotations)

    return {
        field_name: FieldResolver.from_annotation(annotation, field_name)
        for field_name, annotation in annotations.items()
    }


TResolvedFrom = TypeVar("TResolvedFrom", bound=ResolvedFrom)


def resolve_fields(
    model: ResolvableModel,
    kwargs_cls: type[TResolvedKwargs],
    context: "ResolutionContext",
) -> Mapping[str, Any]:
    """Returns a mapping of field names to resolved values for those fields."""
    return {
        field_name: resolver.execute(
            context=context.at_path(field_name), model=model, field_name=field_name
        )
        for field_name, resolver in get_annotation_field_resolvers(kwargs_cls).items()
    }


T = TypeVar("T")


def resolve_model(
    model: ResolvableModel,
    resolvable_type: type[TResolvedFrom],
    context: "ResolutionContext",
) -> TResolvedFrom:
    return resolve_model_using_kwargs_cls(
        model=model,
        kwargs_cls=resolvable_type,
        context=context,
        target_type=resolvable_type,
    )


def resolve_model_using_kwargs_cls(
    model: ResolvableModel,
    kwargs_cls: type[TResolvedKwargs],
    context: "ResolutionContext",
    target_type: type[T],
) -> T:
    return target_type(**resolve_fields(model, kwargs_cls, context))
