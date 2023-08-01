import inspect
from dataclasses import dataclass
from typing import Callable, Optional, TypeVar, Union, overload

from typing_extensions import Annotated, Final, TypeAlias

from dagster import _check as check
from dagster._core.decorator_utils import (
    Decoratable,
    apply_pre_call_decorator,
    is_resource_def,
)
from dagster._utils.backcompat import (
    deprecation_warning,
    experimental_warning,
)

# For the time being, Annotatable objects are the same as decoratable ones. It
# is possible we might want to change this in the future if we want to annotate
# non-callables like constants.
Annotatable: TypeAlias = Decoratable

T_Annotatable = TypeVar("T_Annotatable", bound=Annotatable)

# ########################
# ##### PUBLIC
# ########################

_PUBLIC_ATTR_NAME: Final[str] = "_is_public"


def public(obj: T_Annotatable) -> T_Annotatable:
    """Mark a method on a public class as public. This distinguishes the method from "internal"
    methods, which are methods that are public in the Python sense of being non-underscored, but
    not intended for user access. Only `public` methods of a class are rendered in the docs.
    """
    target = _get_annotation_target(obj)
    setattr(target, _PUBLIC_ATTR_NAME, True)
    return obj


def is_public(obj: Annotatable) -> bool:
    target = _get_annotation_target(obj)
    return hasattr(target, _PUBLIC_ATTR_NAME) and getattr(target, _PUBLIC_ATTR_NAME)


# Use `PublicAttr` to annotate public attributes on `NamedTuple`:
#
# from dagster._annotations import PublicAttr
#
# class Foo(NamedTuple("_Foo", [("bar", PublicAttr[int])])):
#     ...

T = TypeVar("T")

PUBLIC: Final[str] = "public"

PublicAttr: TypeAlias = Annotated[T, PUBLIC]


# ########################
# ##### DEPRECATED
# ########################


_DEPRECATED_ATTR_NAME: Final[str] = "_deprecated"


@dataclass
class DeprecatedInfo:
    breaking_version: str
    additional_warn_text: Optional[str] = None
    subject: Optional[str] = None


@overload
def deprecated(
    __obj: T_Annotatable,
    *,
    breaking_version: str,
    additional_warn_text: Optional[str] = ...,
    subject: Optional[str] = ...,
    emit_runtime_warning: bool = ...,
) -> T_Annotatable:
    ...


@overload
def deprecated(
    __obj: None = ...,
    *,
    breaking_version: str,
    additional_warn_text: Optional[str] = ...,
    subject: Optional[str] = ...,
    emit_runtime_warning: bool = ...,
) -> Callable[[T_Annotatable], T_Annotatable]:
    ...


def deprecated(
    __obj: Optional[T_Annotatable] = None,
    *,
    breaking_version: str,
    additional_warn_text: Optional[str] = None,
    subject: Optional[str] = None,
    emit_runtime_warning: bool = True,
) -> Union[T_Annotatable, Callable[[T_Annotatable], T_Annotatable]]:
    """Mark an object as deprecated. This appends some metadata to the object that causes it to be
    rendered with a "deprecated" tag and associated warning in the docs.

    If `emit_runtime_warning` is True, a warning will also be emitted when the function is called,
    having the same text as is displayed in the docs. For consistency between docs and runtime
    warnings, this decorator is preferred to manual calls to `deprecation_warning`.

    Args:
        breaking_version (str): The version at which the deprecated function will be removed.
        additional_warn_text (Optional[str]): Additional text to display after the deprecation warning.
            Typically this should suggest a newer API.
        subject (Optional[str]): The subject of the deprecation warning. Defaults to a string
            representation of the decorated object. This is useful when marking usage of
            a deprecated API inside an otherwise non-deprecated function, so
            that it can be easily cleaned up later. It should only be used with
            `emit_runtime_warning=False`, as we don't want to warn users when a
            deprecated API is used internally.
        emit_runtime_warning (bool): Whether to emit a warning when the function is called.

    Usage:

        .. code-block:: python

            @deprecated(breaking_version="2.0", additional_warn_text="Use my_new_function instead")
            def my_deprecated_function(my_arg):
                ...

            @deprecated(breaking_version="2.0", additional_warn_text="Use MyNewClass instead")
            class MyDeprecatedClass:
                ...

            @deprecated(breaking_version="2.0", subject="some_deprecated_function", emit_runtime_warning=False)
            def not_deprecated_function():
                ...
                some_deprecated_function()
                ...
    """
    if __obj is None:
        return lambda obj: deprecated(
            obj,
            emit_runtime_warning=emit_runtime_warning,
            breaking_version=breaking_version,
            additional_warn_text=additional_warn_text,
        )
    else:
        target = _get_annotation_target(__obj)
        setattr(
            target,
            _DEPRECATED_ATTR_NAME,
            DeprecatedInfo(breaking_version, additional_warn_text, subject),
        )

        if emit_runtime_warning:
            warning_fn = lambda: deprecation_warning(
                subject or _get_subject(__obj),
                breaking_version=breaking_version,
                additional_warn_text=additional_warn_text,
                stacklevel=_get_warning_stacklevel(__obj),
            )
            return apply_pre_call_decorator(__obj, warning_fn)
        else:
            return __obj


def is_deprecated(obj: Annotatable) -> bool:
    target = _get_annotation_target(obj)
    return hasattr(target, _DEPRECATED_ATTR_NAME)


def get_deprecated_info(obj: Annotatable) -> DeprecatedInfo:
    target = _get_annotation_target(obj)
    return getattr(target, _DEPRECATED_ATTR_NAME)


# ########################
# ##### EXPERIMENTAL
# ########################

_EXPERIMENTAL_ATTR_NAME: Final[str] = "_experimental"


@dataclass
class ExperimentalInfo:
    additional_warn_text: Optional[str] = None
    subject: Optional[str] = None


@overload
def experimental(
    __obj: T_Annotatable,
    *,
    additional_warn_text: Optional[str] = ...,
    subject: Optional[str] = ...,
    emit_runtime_warning: bool = ...,
) -> T_Annotatable:
    ...


@overload
def experimental(
    __obj: None = ...,
    *,
    additional_warn_text: Optional[str] = ...,
    subject: Optional[str] = ...,
    emit_runtime_warning: bool = ...,
) -> Callable[[T_Annotatable], T_Annotatable]:
    ...


def experimental(
    __obj: Optional[T_Annotatable] = None,
    *,
    additional_warn_text: Optional[str] = None,
    subject: Optional[str] = None,
    emit_runtime_warning: bool = True,
) -> Union[T_Annotatable, Callable[[T_Annotatable], T_Annotatable]]:
    """Mark an object as experimental. This appends some metadata to the object that causes it
    to be rendered with an "experimental" tag and associated warning in the docs.

    If `emit_runtime_warning` is True, a warning will also be emitted when the function is called,
    having the same text as is displayed in the docs. For consistency between docs and runtime
    warnings, this decorator is preferred to manual calls to `experimental_warning`.

    Args:
        additional_warn_text (str): Additional text to display after the experimental warning.
        emit_runtime_warning (bool): Whether to emit a warning when the function is called.
        subject (Optional[str]): The subject of the experimental warning. Defaults to a string
            representation of the decorated object. This is useful when marking usage of
            an experimental API inside an otherwise non-deprecated function, so
            that it can be easily cleaned up later. It should only be used with
            `emit_runtime_warning=False`, as we don't want to warn users when an
            experimental API is used internally.

    Usage:

        .. code-block:: python

            @experimental
            def my_experimental_function(my_arg):
                do_stuff()

            @experimental
            class MyExperimentalClass:
                pass
    """
    if __obj is None:
        return lambda obj: experimental(
            obj,
            emit_runtime_warning=emit_runtime_warning,
            additional_warn_text=additional_warn_text,
        )
    else:
        target = _get_annotation_target(__obj)
        setattr(target, _EXPERIMENTAL_ATTR_NAME, ExperimentalInfo(additional_warn_text, subject))

        if emit_runtime_warning:
            warning_fn = lambda: experimental_warning(
                subject or _get_subject(__obj),
                stacklevel=_get_warning_stacklevel(__obj),
            )
            return apply_pre_call_decorator(__obj, warning_fn)
        else:
            return __obj


def is_experimental(obj: Annotatable) -> bool:
    target = _get_annotation_target(obj)
    return hasattr(target, _EXPERIMENTAL_ATTR_NAME) and getattr(target, _EXPERIMENTAL_ATTR_NAME)


def get_experimental_info(obj: Annotatable) -> ExperimentalInfo:
    target = _get_annotation_target(obj)
    return getattr(target, _EXPERIMENTAL_ATTR_NAME)


# ########################
# ##### HELPERS
# ########################


def copy_annotations(dest: Annotatable, src: Annotatable) -> None:
    """Copy all Dagster annotations from one object to another object."""
    dest_target = _get_annotation_target(dest)
    src_target = _get_annotation_target(src)
    if hasattr(src_target, _DEPRECATED_ATTR_NAME):
        setattr(dest_target, _DEPRECATED_ATTR_NAME, getattr(src_target, _DEPRECATED_ATTR_NAME))
    if hasattr(src_target, _PUBLIC_ATTR_NAME):
        setattr(dest_target, _PUBLIC_ATTR_NAME, getattr(src_target, _PUBLIC_ATTR_NAME))
    if hasattr(src_target, _EXPERIMENTAL_ATTR_NAME):
        setattr(dest_target, _EXPERIMENTAL_ATTR_NAME, getattr(src_target, _EXPERIMENTAL_ATTR_NAME))


def _get_annotation_target(obj: Annotatable) -> object:
    """Given an object to be annotated, return the underlying object that will actually store the annotations.
    This is necessary because not all objects are mutable, and so can't be annotated directly.
    """
    if isinstance(obj, property):
        return obj.fget
    elif isinstance(obj, (staticmethod, classmethod)):
        return obj.__func__
    else:
        return obj


def _get_subject(obj: Annotatable) -> str:
    """Get the string representation of an annotated object that will appear in
    annotation-generated warnings about the object.
    """
    if isinstance(obj, type):
        return f"Class `{obj.__qualname__}`"
    elif isinstance(obj, property):
        return f"Property `{obj.fget.__qualname__ if obj.fget else obj}`"
    # classmethod and staticmethod don't themselves get a `__qualname__` attr until Python 3.10.
    elif isinstance(obj, classmethod):
        return f"Class method `{_get_annotation_target(obj).__qualname__}`"  # type: ignore
    elif isinstance(obj, staticmethod):
        return f"Static method `{_get_annotation_target(obj).__qualname__}`"  # type: ignore
    elif inspect.isfunction(obj):
        return f"Function `{obj.__qualname__}`"
    elif is_resource_def(obj):
        return f"Dagster resource `{obj.__qualname__}`"  # type: ignore  # (bad stubs)
    else:
        check.failed(f"Unexpected object type: {type(obj)}")


def _get_warning_stacklevel(obj: Annotatable):
    """Get the stacklevel to use for warnings that are attached to a target via decorator.

    The goal is to have the warning point to the line where the function in the
    underlying object is actually invoked. This isn't straightforward
    because some objects have complicated logic in between `__call__` and
    the site at which a wrapped function containing the warning is actually
    called. Can be determined through trial and error.
    """
    if is_resource_def(obj):
        return 6
    else:
        return 4
