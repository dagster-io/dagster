import sys
import traceback
from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import GenericAlias
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Callable,
    Generic,
    Literal,
    Optional,
    TypeVar,
    Union,
    get_args,
    get_origin,
)

from dagster import _check as check
from pydantic import BaseModel, ConfigDict
from typing_extensions import TypeAlias

from dagster_components.resolved.errors import ResolutionException

try:
    # this type only exists in python 3.10+
    from types import UnionType  # type: ignore
except ImportError:
    UnionType = Union

if TYPE_CHECKING:
    from dagster_components.resolved.context import ResolutionContext


class ResolvableModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


TModel = TypeVar("TModel", bound=ResolvableModel)


def get_model_type(
    resolved_from_type: type["ResolvedFrom"],
) -> type[ResolvableModel]:
    """Returns the first generic type argument (TModel) of the ResolvedFrom subclass at runtime."""
    check.param_invariant(
        issubclass(resolved_from_type, ResolvedFrom),
        "resolvable_from_type",
    )
    check.param_invariant(
        hasattr(resolved_from_type, "__orig_bases__"),
        "resolvable_from_type",
    )
    for base in resolved_from_type.__orig_bases__:  # type: ignore
        # Check if this base originates from ResolvedFrom
        origin = getattr(base, "__origin__", None)
        if origin is ResolvedFrom:
            type_args = get_args(base)
            if not type_args:
                raise ValueError("ResolvedFrom base found but no generic type arguments present")
            return type_args[0]

    raise ValueError("No generic type arguments found in ResolvedFrom subclass")


def get_resolved_kwargs_types(resolved_kwargs_type: type["ResolvedKwargs"]):
    """Returns the generic type arguments (TModel, TObject) of a ResolvedKwargs subclass at runtime."""
    check.param_invariant(
        issubclass(resolved_kwargs_type, ResolvedKwargs),
        "resolved_kwargs_type",
    )
    check.param_invariant(
        hasattr(resolved_kwargs_type, "__orig_bases__"),
        "resolved_kwargs_type",
    )
    for base in resolved_kwargs_type.__orig_bases__:  # type: ignore
        # Check if this base originates from ResolvedFrom
        origin = getattr(base, "__origin__", None)
        if origin is ResolvedKwargs:
            type_args = get_args(base)
            if not type_args:
                raise ValueError("ResolvedKwargs base found but no generic type arguments present")
            if len(type_args) != 2:
                raise ValueError(
                    f"ResolvedKwargs base found but has incorrect number of type arguments, expected 2 got {len(type_args)}"
                )
            return type_args

    raise ValueError("No generic type arguments found in ResolvedKwargs subclass")


T = TypeVar("T")


class ResolvedFrom(Generic[TModel], ABC):
    """Class which defines a type that can be resolved from the associated ResolvableModel."""


class ResolvedKwargs(Generic[TModel, T], ABC):
    """For cases where you can not inherit from ResolvedFrom on the desired target type,
    ResolvedKwargs allows you to define an object which will be resolved from its associated
    ResolvableModel and then passed unpacked as kwargs to create the target type.
    """


class _ModelResolver(Generic[T], ABC):
    @abstractmethod
    def resolve_from_model(self, context: "ResolutionContext", model: ResolvableModel) -> T: ...

    def from_seq(self, context: "ResolutionContext", model: Sequence[TModel]) -> Sequence[T]:
        return [
            self.resolve_from_model(context.at_path(idx), item) for idx, item in enumerate(model)
        ]

    def from_optional(self, context: "ResolutionContext", model: Optional[TModel]) -> Optional[T]:
        return self.resolve_from_model(context, model) if model else None

    def from_optional_seq(
        self, context: "ResolutionContext", model: Optional[Sequence[TModel]]
    ) -> Optional[Sequence[T]]:
        return self.from_seq(context, model) if model else None

    @abstractmethod
    def get_model_type(self) -> type[ResolvableModel]: ...


@dataclass(frozen=True)
class _KwargsResolver(_ModelResolver[T]):
    target_type: type[T]
    kwargs_type: type["ResolvedKwargs"]

    def resolve_from_model(self, context: "ResolutionContext", model: ResolvableModel) -> T:
        return resolve_model_using_kwargs_cls(
            model=model,
            kwargs_cls=self.kwargs_type,
            context=context,
            target_type=self.target_type,
        )

    def get_model_type(self):
        return get_resolved_kwargs_types(self.kwargs_type)[0]


@dataclass(frozen=True)
class _DirectResolver(_ModelResolver[ResolvedFrom]):
    target_type: type[ResolvedFrom]

    def resolve_from_model(
        self, context: "ResolutionContext", model: ResolvableModel
    ) -> ResolvedFrom:
        return resolve_model(
            model=model,
            resolvable_type=self.target_type,
            context=context,
        )

    def get_model_type(self):
        return get_model_type(self.target_type)


@dataclass
class ParentFn:
    callable: Callable[["ResolutionContext", Any], Any]


@dataclass
class AttrWithContextFn:
    callable: Callable[["ResolutionContext", Any], Any]


@dataclass(frozen=True)
class _AutoResolve:
    via: Optional[type[ResolvedKwargs]] = None


class _ExpectedInjection: ...


def _safe_is_subclass(obj, cls: type) -> bool:
    return (
        isinstance(obj, type)
        and not isinstance(obj, GenericAlias)  # prevent exceptions on 3.9
        and issubclass(obj, cls)
    )


def _is_implicitly_resolved_type(annotation):
    if annotation in (int, float, str, bool, Any, type(None)):
        return True

    if _safe_is_subclass(annotation, ResolvableModel):
        return True

    origin = get_origin(annotation)
    args = get_args(annotation)

    if origin in (Union, UnionType, list, Sequence, tuple, dict, Mapping) and all(
        _is_implicitly_resolved_type(arg) for arg in args
    ):
        return True

    if origin is Annotated and any(isinstance(arg, _ExpectedInjection) for arg in args):
        return True

    if origin is Literal and all(_is_implicitly_resolved_type(type(arg)) for arg in args):
        return True

    return False


def _get_resolver(
    annotation: type,
    top_level_auto_resolve: Optional[_AutoResolve],
) -> Optional[_ModelResolver]:
    if top_level_auto_resolve:
        if (
            top_level_auto_resolve.via
            and annotation is get_resolved_kwargs_types(top_level_auto_resolve.via)[1]
        ):
            return _KwargsResolver(
                kwargs_type=top_level_auto_resolve.via,
                target_type=annotation,
            )
        if _safe_is_subclass(annotation, ResolvedFrom):
            return _DirectResolver(annotation)

    origin = get_origin(annotation)
    if origin is not Annotated:
        return None

    args = get_args(annotation)
    auto_resolve = next((arg for arg in args if isinstance(arg, _AutoResolve)), None)
    if not auto_resolve:
        return None

    if auto_resolve.via:
        return _KwargsResolver(kwargs_type=auto_resolve.via, target_type=args[0])

    resolved_from_cls = args[0]
    if not _safe_is_subclass(resolved_from_cls, ResolvedFrom):
        check.failed("Can only annotate ResolvedFrom types with ResolveModel()")
    return _DirectResolver(resolved_from_cls)


def derive_field_resolver(annotation: Any, field_name: str) -> "Resolver":
    if _is_implicitly_resolved_type(annotation):
        return Resolver(_recurse)

    origin = get_origin(annotation)
    args = get_args(annotation)

    top_level_auto_resolve = None
    if origin is Annotated:
        resolver = next((arg for arg in args if isinstance(arg, Resolver)), None)
        if resolver:
            return resolver

        top_level_auto_resolve = next((arg for arg in args if isinstance(arg, _AutoResolve)), None)
        resolver = _get_resolver(args[0], top_level_auto_resolve)
        if resolver:
            return Resolver(
                resolver.resolve_from_model,
                model_field_type=resolver.get_model_type(),
            )

        origin = get_origin(args[0])
        args = get_args(args[0])

    if origin in (Union, UnionType) and len(args) == 2:
        left_t, right_t = args
        if right_t is type(None):
            resolver = _get_resolver(left_t, top_level_auto_resolve)
            if resolver:
                return Resolver(
                    resolver.from_optional,
                    model_field_type=Optional[resolver.get_model_type()],
                )

            elif get_origin(left_t) in (Sequence, tuple, list):
                resolver = _get_resolver(get_args(left_t)[0], top_level_auto_resolve)
                if resolver:
                    return Resolver(
                        resolver.from_optional_seq,
                        model_field_type=Optional[list[resolver.get_model_type()]],
                    )

    elif origin in (Sequence, tuple, list):
        resolver = _get_resolver(args[0], top_level_auto_resolve)

        if resolver:
            return Resolver(
                resolver.from_seq,
                model_field_type=list[resolver.get_model_type()],
            )

    raise ResolutionException(
        f"Could not derive resolver for annotation {field_name}: {annotation}.\n"
        "Field types are expected to be:\n"
        "* serializable types such as str, float, int, bool, list, etc\n"
        "* ResolvableModel\n"
        "* Annotated with an appropriate Resolver."
    )


def _recurse(context: "ResolutionContext", field_value):
    return context.resolve_value(field_value)


class Resolver:
    """Contains information on how to resolve a field from a ResolvableModel."""

    def __init__(
        self,
        fn: Union[ParentFn, AttrWithContextFn, Callable[["ResolutionContext", Any], Any]],
        model_field_name: Optional[str] = None,
        model_field_type: Optional[type] = None,
    ):
        """Resolve this field by invoking the function which will receive the corresponding field value
        from the model.
        """
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

        self.model_field_name = model_field_name
        self.model_field_type = model_field_type

        super().__init__()

    @staticmethod
    def from_annotation():
        """Resolve this field to the (potentially nested) ResolvedFrom type via its associated ResolvableModel."""
        return _AutoResolve()

    @staticmethod
    def from_resolved_kwargs(kwargs_cls: type[ResolvedKwargs]):
        """Resolve this field to the (potentially nested) target type of the ResolvedKwargs via its associated ResolvableModel."""
        return _AutoResolve(via=kwargs_cls)

    @staticmethod
    def from_template_injection(via: Optional[type[ResolvedKwargs]] = None):
        """The complex type at this field must be template injected using an appropriate scope."""
        return _ExpectedInjection()

    @staticmethod
    def from_model(fn: Callable[["ResolutionContext", Any], Any], **kwargs):
        """Resolve this field by invoking the function which will receive the entire parent ResolvableModel."""
        return Resolver(ParentFn(fn), **kwargs)

    @staticmethod
    def default(**kwargs):
        """Default recursive resolution."""
        return Resolver(_recurse, **kwargs)

    def execute(
        self,
        context: "ResolutionContext",
        model: ResolvableModel,
        field_name: str,
    ) -> Any:
        from dagster_components.resolved.context import ResolutionException

        try:
            if isinstance(self.fn, ParentFn):
                return self.fn.callable(context, model)
            elif isinstance(self.fn, AttrWithContextFn):
                field_name = self.model_field_name or field_name
                attr = getattr(model, field_name)
                context = context.at_path(field_name)
                return self.fn.callable(context, attr)
        except ResolutionException:
            raise  # already processed
        except Exception:
            raise context.build_resolve_fn_exc(
                traceback.format_exception(*sys.exc_info()),
                field_name=field_name,
                model=model,
            ) from None

        raise ValueError(f"Unsupported Resolver type: {self.fn}")


ResolvedType: TypeAlias = Union[type[ResolvedKwargs], type[ResolvedFrom]]


def get_annotation_field_resolvers(kwargs_cls: ResolvedType) -> dict[str, Resolver]:
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
        field_name: derive_field_resolver(annotation, field_name)
        for field_name, annotation in annotations.items()
    }


def resolve_fields(
    model: ResolvableModel,
    kwargs_cls: Union[type[ResolvedFrom], type[ResolvedKwargs]],
    context: "ResolutionContext",
) -> Mapping[str, Any]:
    """Returns a mapping of field names to resolved values for those fields."""
    return {
        field_name: resolver.execute(context=context, model=model, field_name=field_name)
        for field_name, resolver in get_annotation_field_resolvers(kwargs_cls).items()
    }


TResolvedFrom = TypeVar("TResolvedFrom", bound=ResolvedFrom)


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
    kwargs_cls: Union[type[ResolvedFrom], type[ResolvedKwargs]],
    context: "ResolutionContext",
    target_type: type[T],
) -> T:
    # In the future we will do an explicit validation of alignment, but for now raise a marginally better error.
    check.inst_param(
        model,
        "model",
        ResolvableModel,
        "Ensure ResolveFrom field type annotations align with the corresponding ResolvableModel.",
    )
    return target_type(**resolve_fields(model, kwargs_cls, context))
