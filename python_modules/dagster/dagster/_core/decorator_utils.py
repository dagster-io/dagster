import functools
import inspect
import re
import textwrap
from collections.abc import Mapping, Sequence
from inspect import Parameter, signature
from typing import (  # noqa: UP035
    TYPE_CHECKING,
    Any,
    Callable,
    ContextManager,
    Optional,
    TypeVar,
    Union,
    cast,
    get_type_hints as typing_get_type_hints,
)

from typing_extensions import Concatenate, ParamSpec, TypeAlias, TypeGuard

import dagster._check as check
from dagster._core.errors import DagsterInvalidDefinitionError

if TYPE_CHECKING:
    from dagster._core.definitions.op_definition import OpDefinition
    from dagster._core.definitions.resource_definition import ResourceDefinition

Decoratable: TypeAlias = Union[
    type, Callable, property, staticmethod, classmethod, "OpDefinition", "ResourceDefinition"
]


R = TypeVar("R")
T = TypeVar("T")
P = ParamSpec("P")
T_Callable = TypeVar("T_Callable", bound=Callable)
T_Decoratable = TypeVar("T_Decoratable", bound=Decoratable)
T_Type = TypeVar("T_Type", bound=type)


def get_valid_name_permutations(param_name: str) -> set[str]:
    """Get all underscore permutations for provided arg name."""
    return {
        "_",
        param_name,
        f"_{param_name}",
        f"{param_name}_",
    }


def _is_param_valid(param: Parameter, expected_positional: str) -> bool:
    # The "*" character indicates that we permit any name for this positional parameter.
    if expected_positional == "*":
        return True

    possible_kinds = {Parameter.POSITIONAL_OR_KEYWORD, Parameter.POSITIONAL_ONLY}

    return (
        param.name in get_valid_name_permutations(expected_positional)
        and param.kind in possible_kinds
    )


def get_function_params(fn: Callable[..., Any]) -> Sequence[Parameter]:
    return list(signature(fn).parameters.values())


def get_type_hints(fn: Callable[..., Any]) -> Mapping[str, Any]:
    if isinstance(fn, functools.partial):
        target = fn.func
    elif inspect.isfunction(fn):
        target = fn
    elif hasattr(fn, "__call__"):
        target = fn.__call__  # pyright: ignore[reportFunctionMemberAccess]
    else:
        check.failed(f"Unhandled Callable object {fn}")

    try:
        return typing_get_type_hints(target, include_extras=True)
    except NameError as e:
        match = re.search(r"'(\w+)'", str(e))
        assert match
        annotation = match[1]
        raise DagsterInvalidDefinitionError(
            f'Failed to resolve type annotation "{annotation}" in function {target.__name__}. This'
            " can occur when the parameter has a string annotation that references either: (1) a"
            " type defined in a local scope (2) a type that is defined or imported in an `if"
            " TYPE_CHECKING` block. Note that if you are including `from __future__ import"
            " annotations`, all annotations in that module are stored as strings. Suggested"
            " solutions include: (1) convert the annotation to a non-string annotation; (2) move"
            " the type referenced by the annotation out of local scope or a `TYPE_CHECKING` block."
        )


def validate_expected_params(
    params: Sequence[Parameter], expected_params: Sequence[str]
) -> Optional[str]:
    """Returns first missing positional, if any, otherwise None."""
    expected_idx = 0
    for expected_param in expected_params:
        if expected_idx >= len(params) or not _is_param_valid(params[expected_idx], expected_param):
            return expected_param
        expected_idx += 1
    return None


def is_required_param(param: Parameter) -> bool:
    return param.default == Parameter.empty


def positional_arg_name_list(params: Sequence[Parameter]) -> Sequence[str]:
    accepted_param_types = {
        Parameter.POSITIONAL_OR_KEYWORD,
        Parameter.POSITIONAL_ONLY,
    }
    return [p.name for p in params if p.kind in accepted_param_types]


def param_is_var_keyword(param: Parameter) -> bool:
    return param.kind == Parameter.VAR_KEYWORD


def format_docstring_for_description(fn: Callable[..., Any]) -> Optional[str]:
    if fn.__doc__ is not None:
        docstring = fn.__doc__
        if len(docstring) > 0 and docstring[0].isspace():
            return textwrap.dedent(docstring).strip()
        else:
            first_newline_pos = docstring.find("\n")
            if first_newline_pos == -1:
                return docstring
            else:
                return (
                    docstring[: first_newline_pos + 1]
                    + textwrap.dedent(docstring[first_newline_pos + 1 :])
                ).strip()
    else:
        return None


# Type-ignores are used throughout the codebase when this function returns False to ignore the type
# error arising from assuming
# When/if `StrictTypeGuard` is supported, we can drop `is_context_not_provided` since a False from
# `has_at_least_one_parameter` will be sufficient.
def has_at_least_one_parameter(
    fn: Union[Callable[Concatenate[T, P], R], Callable[P, R]],
) -> TypeGuard[Callable[Concatenate[T, P], R]]:
    return len(get_function_params(fn)) >= 1


def get_decorator_target(obj: Decoratable) -> Callable:
    """Given a callable to be decorated, return the underlying function.

    - If a function is passed, return it.
    - If a NamedTuple class is passed, return its __new__ method.
    - If any other class is passed, return its __init__ method.
    - If a property is passed, return its `fget`.
    - If a classmethod or staticmethod is passed, return its `__func__`.
    - If a Dagster resource is passed, return its `resource_fn`.
    - If a Dagster op is possed, return its `compute_fn`.
    """
    if isinstance(obj, property):
        assert obj.fget, "Cannot decorate property without getter"
        return obj.fget
    elif isinstance(obj, (classmethod, staticmethod)):
        return obj.__func__
    elif isinstance(obj, type):
        constructor_name = "__new__" if issubclass(obj, tuple) else "__init__"
        return getattr(obj, constructor_name)
    elif is_resource_def(obj):
        return obj._resource_fn  # noqa: SLF001
    else:
        return obj


def apply_pre_call_decorator(
    obj: T_Decoratable,
    pre_call_fn: Callable[[], None],
    condition: Optional[Callable[..., bool]] = None,
) -> T_Decoratable:
    target = get_decorator_target(obj)
    new_fn = _wrap_with_pre_call_fn(target, pre_call_fn, condition)
    return _update_decoratable(obj, new_fn)


def _wrap_with_pre_call_fn(
    fn: T_Callable,
    pre_call_fn: Callable[[], None],
    condition: Optional[Callable[..., bool]] = None,
) -> T_Callable:
    @functools.wraps(fn)
    def wrapped_with_pre_call_fn(*args, **kwargs):
        if condition is None or condition(*args, **kwargs):
            pre_call_fn()
        return fn(*args, **kwargs)

    return cast(T_Callable, wrapped_with_pre_call_fn)


def apply_context_manager_decorator(
    obj: T_Decoratable, cm: Callable[[], ContextManager[None]]
) -> T_Decoratable:
    target = get_decorator_target(obj)
    new_fn = _wrap_with_context_manager(target, cm)
    return _update_decoratable(obj, new_fn)


def _wrap_with_context_manager(
    fn: T_Callable,
    cm: Callable[[], ContextManager[None]],
) -> T_Callable:
    @functools.wraps(fn)
    def wrapped_with_context_manager_fn(*args, **kwargs):
        with cm():
            return fn(*args, **kwargs)

    return cast(T_Callable, wrapped_with_context_manager_fn)


def _update_decoratable(decoratable: T_Decoratable, new_fn: Callable[..., Any]) -> T_Decoratable:
    """Update a property with a new `fget` function.

    `property` objects are immutable, so if we want to apply a decorator to the underlying `fget`,
    we need to create a new `property` object with the updated `fget` function that preserves the
    rest of the property's attributes. We also want to make sure we copy over any special attributes
    we stored on the `fget` (since we can't and therefore don't store them on the `property`
     object).
    """
    from dagster._annotations import copy_annotations

    curr_fn = get_decorator_target(decoratable)
    new_fn = functools.update_wrapper(new_fn, curr_fn)
    if isinstance(decoratable, property):
        val = property(new_fn, decoratable.fset, decoratable.fdel, decoratable.__doc__)
        copy_annotations(val, decoratable)
    elif isinstance(decoratable, staticmethod):
        val = staticmethod(new_fn)
        copy_annotations(val, decoratable)
    elif isinstance(decoratable, classmethod):
        val = classmethod(new_fn)
        copy_annotations(val, decoratable)
    elif isinstance(decoratable, type):
        constructor_name = "__new__" if issubclass(decoratable, tuple) else "__init__"
        setattr(decoratable, constructor_name, new_fn)
        val = decoratable
    elif is_resource_def(decoratable):
        setattr(decoratable, "_resource_fn", new_fn)
        val = decoratable
    else:  # plain function
        val = new_fn

    # Pyright is unable to infer based on our checks that the return type is the same as the input
    # type.
    return cast(T_Decoratable, val)


def is_decoratable(obj: Any) -> TypeGuard[Decoratable]:
    """Return `True` if the passed object is a decoratable object."""
    return (
        isinstance(obj, type)
        or isinstance(obj, (property, staticmethod, classmethod))
        or inspect.isfunction(obj)
        or is_resource_def(obj)
    )


def is_resource_def(obj: Any) -> TypeGuard["ResourceDefinition"]:
    """Use this in place of `isinstance` when `ResourceDefinition`
    can't be imported yet (due to circular import issues).
    """
    class_names = [cls.__name__ for cls in inspect.getmro(obj.__class__)]
    return "ResourceDefinition" in class_names
