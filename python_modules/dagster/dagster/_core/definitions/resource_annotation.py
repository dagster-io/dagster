from abc import ABC
from collections.abc import Sequence
from inspect import Parameter
from typing import Annotated, Any, TypeVar, Union, get_args, get_origin

from dagster_shared.record import record
from dagster_shared.seven import is_subclass

from dagster._core.decorator_utils import get_function_params, get_type_hints
from dagster._core.definitions.resource_definition import ResourceDefinition


def get_resource_args(fn) -> Sequence[Parameter]:
    type_annotations = get_type_hints(fn)
    return [
        param
        for param in get_function_params(fn)
        if _is_resource_annotation(type_annotations.get(param.name))
    ]


RESOURCE_PARAM_METADATA = "resource_param"


class TreatAsResourceParam(ABC):
    """Marker class for types that can be used as a parameter on an annotated
    function like `@asset`. Any type marked with this class does not require
    a ResourceParam when used on an asset.

    Example:
        class YourClass(TreatAsResourceParam):
            ...

        @asset
        def an_asset(your_class: YourClass):
            ...
    """


def _is_resource_annotation(annotation: type[Any] | None) -> bool:
    from dagster._config.pythonic_config import ConfigurableResourceFactory

    if isinstance(annotation, type) and (
        is_subclass(annotation, ResourceDefinition)
        or is_subclass(annotation, ConfigurableResourceFactory)
        or is_subclass(annotation, TreatAsResourceParam)
    ):
        return True

    return hasattr(annotation, "__metadata__") and getattr(annotation, "__metadata__") == (
        RESOURCE_PARAM_METADATA,
    )


def _resolve_annotation_for_type_check(annotation: Any) -> type | None:
    """Extracts the concrete checkable type from a resource parameter annotation.

    Returns ``None`` when the annotation cannot support a meaningful ``isinstance``
    check — for example, legacy ``ResourceDefinition``, unions with multiple
    non-``None`` members, or non-type objects such as plain strings.

    Handles:
    - ``ConfigurableResource`` / ``ConfigurableResourceFactory`` subclasses → as-is
    - ``TreatAsResourceParam`` subclasses → as-is
    - ``ResourceParam[T]`` / ``Annotated[T, ...]`` → unwrap, recurse on ``T``
    - ``Optional[T]`` / ``Union[T, None]`` → unwrap to ``T``, recurse
    - ``Union[A, B, ...]`` (multiple non-``None`` members) → ``None`` (ambiguous)
    - Bare ``ResourceDefinition`` (non-configurable, legacy) → ``None`` (too abstract)
    """
    from dagster._config.pythonic_config import ConfigurableResourceFactory

    # Unwrap Annotated[T, ...] and ResourceParam[T] = Annotated[T, "resource_param"]
    if get_origin(annotation) is Annotated:
        return _resolve_annotation_for_type_check(get_args(annotation)[0])

    # Handle Optional[T] == Union[T, None] and bare Union types
    if get_origin(annotation) is Union:
        non_none = [a for a in get_args(annotation) if a is not type(None)]
        if len(non_none) == 1:
            return _resolve_annotation_for_type_check(non_none[0])
        return None  # Union[A, B, ...] — ambiguous, skip check

    if not isinstance(annotation, type):
        return None

    # Skip bare ResourceDefinition (non-configurable legacy style) — too abstract
    # to perform a meaningful isinstance check against the user-provided resource.
    if is_subclass(annotation, ResourceDefinition) and not is_subclass(
        annotation, ConfigurableResourceFactory
    ):
        return None

    if is_subclass(annotation, ConfigurableResourceFactory):
        # Only validate when the resource injects *itself* into user code.
        # ConfigurableResource subclasses that override create_resource may inject
        # an arbitrary value (not the resource object), so skip the check for those.
        if not _injects_self(annotation):
            return None
        return annotation

    if is_subclass(annotation, TreatAsResourceParam):
        return annotation

    return None


def _injects_self(annotation: type) -> bool:
    """Returns True when the ConfigurableResource subclass does NOT override create_resource.

    When create_resource is not overridden, the resource object itself (an instance of the
    annotation class) is injected into user code, making isinstance validation meaningful.
    When create_resource IS overridden, the injected value may be any type, so we skip.
    """
    from dagster._config.pythonic_config import ConfigurableResource

    for cls in annotation.__mro__:
        if "create_resource" in cls.__dict__:
            return cls is ConfigurableResource
    return True


@record
class ResourceArgSpec:
    """Bundles a resource parameter name with its resolved annotation type.

    Used to carry type information from the function signature through to the
    resource injection site in :func:`invoke_compute_fn`, enabling
    ``isinstance`` validation *before* user code runs.

    ``annotation`` is ``None`` when the annotation cannot be meaningfully
    validated (e.g. legacy ``ResourceDefinition``, a ``Union`` with multiple
    non-``None`` members).
    """

    name: str
    annotation: type | None = None


def get_resource_arg_specs(fn) -> Sequence[ResourceArgSpec]:
    """Returns a :class:`ResourceArgSpec` for each resource-annotated parameter on ``fn``.

    Replaces the ``{name: name}`` identity-dict pattern with a typed record
    that also carries the resolved annotation, enabling ``isinstance``
    validation at injection time.
    """
    type_annotations = get_type_hints(fn)
    specs = []
    for param in get_function_params(fn):
        annotation = type_annotations.get(param.name)
        if not _is_resource_annotation(annotation):
            continue
        specs.append(
            ResourceArgSpec(
                name=param.name,
                annotation=_resolve_annotation_for_type_check(annotation),
            )
        )
    return specs


T = TypeVar("T")
ResourceParam = Annotated[T, RESOURCE_PARAM_METADATA]
