import inspect
import sys
import traceback
from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum, auto
from functools import partial
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
from pydantic import BaseModel, ConfigDict, Field, PydanticSchemaGenerationError, create_model
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


def get_resolved_kwargs_target_type(resolved_kwargs_type: type["ResolvedKwargs"]):
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
            return type_args[1]

    raise ValueError("No generic type arguments found in ResolvedKwargs subclass")


T = TypeVar("T")


class ResolvedFrom(Generic[TModel], ABC):
    """Class which defines a type that can be resolved from the associated ResolvableModel."""


class ResolvedKwargs(Generic[TModel, T], ABC):
    """For cases where you can not inherit from ResolvedFrom on the desired target type,
    ResolvedKwargs allows you to define an object which will be resolved from its associated
    ResolvableModel and then passed unpacked as kwargs to create the target type.
    """


class _TypeContainer(Enum):
    SEQUENCE = auto()
    OPTIONAL = auto()


@dataclass(frozen=True)
class _ModelResolver(Generic[T], ABC):
    target_type: type[T]

    @abstractmethod
    def resolve_from_model(self, context: "ResolutionContext", model: ResolvableModel) -> T: ...

    def from_type_container_path(
        self,
        context: "ResolutionContext",
        value: Any,
        container_path: Sequence[_TypeContainer],
    ) -> Any:
        if not container_path:
            return self.resolve_from_model(context, value)

        container = container_path[0]
        inner_path = container_path[1:]
        if container is _TypeContainer.OPTIONAL:
            return (
                self.from_type_container_path(context, value, inner_path)
                if value is not None
                else None
            )
        elif container is _TypeContainer.SEQUENCE:
            return [
                self.from_type_container_path(context.at_path(idx), i, inner_path)
                for idx, i in enumerate(value)
            ]

        check.assert_never(f"unhandled type container enum {container}")


@dataclass(frozen=True)
class _KwargsResolver(_ModelResolver[T]):
    kwargs_type: type["ResolvedKwargs"]

    def resolve_from_model(self, context: "ResolutionContext", model: ResolvableModel) -> T:
        return resolve_model_using_kwargs_cls(
            model=model,
            kwargs_cls=self.kwargs_type,
            context=context,
            target_type=self.target_type,
        )


@dataclass(frozen=True)
class _DirectResolver(_ModelResolver[ResolvedFrom]):
    def resolve_from_model(
        self, context: "ResolutionContext", model: ResolvableModel
    ) -> ResolvedFrom:
        return resolve_model(
            model=model,
            resolvable_type=self.target_type,
            context=context,
        )


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
        if top_level_auto_resolve.via and annotation is get_resolved_kwargs_target_type(
            top_level_auto_resolve.via
        ):
            return _KwargsResolver(
                kwargs_type=top_level_auto_resolve.via,
                target_type=annotation,
            )
        if _safe_is_subclass(annotation, ResolvedFrom) or _safe_is_subclass(annotation, Resolved):
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
        check.failed("Can only annotate ResolvedFrom types with Resolver.from_annotation()")

    return _DirectResolver(resolved_from_cls)


def _recurse(context: "ResolutionContext", field_value):
    return context.resolve_value(field_value)


def _field_error_msg(field_name: str, annotation: Any) -> str:
    return (
        f"Could not derive resolver for annotation {field_name}: {annotation}.\n"
        "Field types are expected to be:\n"
        "* serializable types such as str, float, int, bool, list, etc\n"
        "* ResolvableModel\n"
        "* Annotated with an appropriate Resolver."
    )


def derive_field_resolver(annotation: Any, field_name: str) -> "Resolver":
    if _is_implicitly_resolved_type(annotation):
        return Resolver(_recurse)

    origin = get_origin(annotation)
    args = get_args(annotation)

    if origin is Annotated:
        resolver = next((arg for arg in args if isinstance(arg, Resolver)), None)
        if resolver:
            return resolver

    res = _get_model_resolution(annotation)
    if res:
        return Resolver(partial(res[0].from_type_container_path, container_path=res[1]))

    check.failed(_field_error_msg(field_name, annotation))


def _get_model_resolution(
    annotation: Any,
) -> Optional[tuple[_ModelResolver, Sequence[_TypeContainer]]]:
    origin = get_origin(annotation)
    args = get_args(annotation)

    top_level_auto_resolve = None
    if origin is Annotated:
        top_level_auto_resolve = next((arg for arg in args if isinstance(arg, _AutoResolve)), None)
        resolver = _get_resolver(args[0], top_level_auto_resolve)
        if resolver:
            return (resolver, [])

        origin = get_origin(args[0])
        args = get_args(args[0])

    if origin in (Union, UnionType) and len(args) == 2:
        left_t, right_t = args
        if right_t is type(None):
            resolver = _get_resolver(left_t, top_level_auto_resolve)
            if resolver:
                return (resolver, [_TypeContainer.OPTIONAL])

            elif get_origin(left_t) in (Sequence, tuple, list):
                resolver = _get_resolver(get_args(left_t)[0], top_level_auto_resolve)
                if resolver:
                    return resolver, [_TypeContainer.OPTIONAL, _TypeContainer.SEQUENCE]

    elif origin in (Sequence, tuple, list):
        resolver = _get_resolver(args[0], top_level_auto_resolve)

        if resolver:
            return (resolver, [_TypeContainer.SEQUENCE])

    return None


class Resolver:
    """Contains information on how to resolve a field from a ResolvableModel."""

    def __init__(
        self,
        fn: Union[ParentFn, AttrWithContextFn, Callable[["ResolutionContext", Any], Any]],
    ):
        """Resolve this field by invoking the function which will receive the corresponding field value from the parent ResolvableModel."""
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
    def from_model(fn: Callable[["ResolutionContext", Any], Any]):
        """Resolve this field by invoking the function which will receive the entire parent ResolvableModel."""
        return Resolver(ParentFn(fn))

    def execute(
        self,
        context: "ResolutionContext",
        model: ResolvableModel,
        field_name: str,
    ) -> Any:
        try:
            if isinstance(self.fn, ParentFn):
                return self.fn.callable(context, model)
            elif isinstance(self.fn, AttrWithContextFn):
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


ResolvedType: TypeAlias = Union[type[ResolvedKwargs], type[ResolvedFrom], type["Resolved"]]


def _get_init_kwargs(target_type: ResolvedType):
    if target_type.__init__ is object.__init__:
        return None

    sig = inspect.signature(target_type.__init__)
    fields = {}

    skipped_self = False
    for name, param in sig.parameters.items():
        if not skipped_self:
            skipped_self = True
            continue

        if param.kind == param.POSITIONAL_ONLY:
            raise ResolutionException(
                f"Invalid Resolved type {target_type}: __init__ contains positional only parameter."
            )
        if param.annotation == param.empty:
            raise ResolutionException(
                f"Invalid Resolved type {target_type}: __init__ parameter {name} has no type hint."
            )
        if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
            continue

        fields[name] = param.annotation
    return fields


def get_annotations(resolved_type: ResolvedType):
    if is_dataclass(resolved_type):
        return {f.name: f.type for f in fields(resolved_type)}
    elif _safe_is_subclass(resolved_type, ResolvedKwargs) or _safe_is_subclass(
        resolved_type, BaseModel
    ):
        annotations = {}
        # Walk through all base classes in MRO
        for base in reversed(resolved_type.__mro__):
            # Get annotations from current base class if they exist
            base_annotations = getattr(base, "__annotations__", {})
            # Update annotations dict with any new annotations found
            # Later bases don't override earlier ones due to how update works
            annotations.update(base_annotations)
        return annotations
    elif init_kwargs := _get_init_kwargs(resolved_type):
        return init_kwargs
    else:
        raise ResolutionException(
            f"Invalid Resolved type {resolved_type} could not determine fields, expected:\n"
            "* @dataclass\n"
            "* class with non empty __init__\n"
        )


def get_annotation_field_resolvers(
    kwargs_cls: ResolvedType,
) -> dict[str, Resolver]:
    return {
        field_name: derive_field_resolver(annotation, field_name)
        for field_name, annotation in get_annotations(kwargs_cls).items()
    }


def resolve_fields(
    model: ResolvableModel,
    kwargs_cls: ResolvedType,
    context: "ResolutionContext",
) -> Mapping[str, Any]:
    """Returns a mapping of field names to resolved values for those fields."""
    return {
        field_name: resolver.execute(context=context, model=model, field_name=field_name)
        for field_name, resolver in get_annotation_field_resolvers(kwargs_cls).items()
    }


TResolved = TypeVar("TResolved", bound=Union[ResolvedFrom, "Resolved"])


def resolve_model(
    model: ResolvableModel,
    resolvable_type: type[TResolved],
    context: "ResolutionContext",
) -> TResolved:
    return resolve_model_using_kwargs_cls(
        model=model,
        kwargs_cls=resolvable_type,
        context=context,
        target_type=resolvable_type,
    )


def resolve_model_using_kwargs_cls(
    model: ResolvableModel,
    kwargs_cls: ResolvedType,
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


class Resolved: ...


_DERIVED_MODEL_REGISTRY = {}


def derive_model_type(
    target_type: type[Resolved],
) -> type[ResolvableModel]:
    if target_type not in _DERIVED_MODEL_REGISTRY:
        name = f"{target_type.__name__}ResolvableModel"

        model_fields: dict[
            str, Any
        ] = {}  # use Any to appease type checker when **-ing in to create_model

        for name, annotation in get_annotations(target_type).items():
            if _is_implicitly_resolved_type(annotation):
                field_type = annotation
            elif res := _get_model_resolution(annotation):
                ttype = res[0].target_type
                if _safe_is_subclass(ttype, ResolvedFrom):
                    model_type = get_model_type(ttype)
                elif _safe_is_subclass(ttype, Resolved):
                    model_type = derive_model_type(ttype)
                else:
                    check.failed(f"unexpected target type {ttype}")

                # wrap the model type in appropriate containers
                field_type = model_type
                for container in reversed(res[1]):
                    if container is _TypeContainer.OPTIONAL:
                        field_type = Optional[field_type]
                    elif container is _TypeContainer.SEQUENCE:
                        # use tuple instead of Sequence for perf
                        field_type = tuple[field_type]
                    else:
                        check.assert_never(f"missing _TypeContainer enum handling {container}")
            else:
                raise ResolutionException(
                    f"Unable to derive ResolvableModel for {target_type}\n"
                    f"{_field_error_msg(name, annotation)}"
                )

            model_fields[name] = (
                field_type,
                Field(),
            )

        try:
            _DERIVED_MODEL_REGISTRY[target_type] = create_model(
                name,
                __base__=ResolvableModel,
                **model_fields,
            )
        except PydanticSchemaGenerationError as e:
            raise ResolutionException(f"Unable to derive ResolvableModel for {target_type}") from e

    return _DERIVED_MODEL_REGISTRY[target_type]
