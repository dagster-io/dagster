import inspect
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Annotated, Any, Callable, Final, Optional, TypeVar, Union, overload

from typing_extensions import TypeAlias

from dagster import _check as check
from dagster._core.decorator_utils import (
    apply_pre_call_decorator,
    get_decorator_target,
    is_resource_def,
)
from dagster._utils.warnings import (
    beta_warning,
    deprecation_warning,
    preview_warning,
    supersession_warning,
)

# For the time being, `Annotatable` is set to `Any` even though it should be set to `Decoratable` to
# avoid choking the type checker. Choking happens because of a niche scenario where
# `ResourceDefinition`, which is part of `Decoratable`, is used as an argument to a function that
# accepts `Annotatable`. There is a certain circularity here that current versions of pyright fail
# on. It will likely be resolved by future versions of pyright, and then `Annotatable` should be set
# to `Decoratable`.
Annotatable: TypeAlias = Any

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
# ##### PREVIEW
# ########################


_PREVIEW_ATTR_NAME: Final[str] = "_preview"


@dataclass
class PreviewInfo:
    additional_warn_text: Optional[str] = None
    subject: Optional[str] = None


@overload
def preview(
    __obj: T_Annotatable,
    *,
    additional_warn_text: Optional[str] = ...,
    subject: Optional[str] = ...,
    emit_runtime_warning: bool = ...,
) -> T_Annotatable: ...


@overload
def preview(
    __obj: None = ...,
    *,
    additional_warn_text: Optional[str] = ...,
    subject: Optional[str] = ...,
    emit_runtime_warning: bool = ...,
) -> Callable[[T_Annotatable], T_Annotatable]: ...


def preview(
    __obj: Optional[T_Annotatable] = None,
    *,
    additional_warn_text: Optional[str] = None,
    subject: Optional[str] = None,
    emit_runtime_warning: bool = True,
) -> Union[T_Annotatable, Callable[[T_Annotatable], T_Annotatable]]:
    """Mark an object as preview. This appends some metadata to the object that causes it to be
    rendered with a "preview" tag and associated warning in the docs.

    If `emit_runtime_warning` is True, a warning will also be emitted when the function is called,
    having the same text as is displayed in the docs. For consistency between docs and runtime
    warnings, this decorator is preferred to manual calls to `preview_warning`.

    Args:
        additional_warn_text (Optional[str]): Additional text to display after the preview warning.
        subject (Optional[str]): The subject of the preview warning. Defaults to a string
            representation of the decorated object. This is useful when marking usage of
            a preview API inside an otherwise non-preview function, so
            that it can be easily cleaned up later. It should only be used with
            `emit_runtime_warning=False`, as we don't want to warn users when a
            preview API is used internally.
        emit_runtime_warning (bool): Whether to emit a warning when the function is called.

    Usage:

        .. code-block:: python

            @preview
            def my_preview_function(my_arg):
                ...

            @preview
            class MyPreviewClass:
                ...

            @preview(subject="some_preview_function", emit_runtime_warning=False)
            def not_preview_function():
                ...
                some_preview_function()
                ...
    """
    if __obj is None:
        return lambda obj: preview(
            obj,
            subject=subject,
            emit_runtime_warning=emit_runtime_warning,
            additional_warn_text=additional_warn_text,
        )
    else:
        target = _get_annotation_target(__obj)
        setattr(
            target,
            _PREVIEW_ATTR_NAME,
            PreviewInfo(additional_warn_text, subject),
        )

        if emit_runtime_warning:
            stack_level = _get_warning_stacklevel(__obj)
            subject = subject or _get_subject(__obj)
            warning_fn = lambda: preview_warning(
                subject,
                additional_warn_text=additional_warn_text,
                stacklevel=stack_level,
            )
            return apply_pre_call_decorator(__obj, warning_fn)
        else:
            return __obj


def is_preview(obj: Annotatable) -> bool:
    target = _get_annotation_target(obj)
    return hasattr(target, _PREVIEW_ATTR_NAME)


def get_preview_info(obj: Annotatable) -> PreviewInfo:
    target = _get_annotation_target(obj)
    return getattr(target, _PREVIEW_ATTR_NAME)


# ########################
# ##### BETA
# ########################


_BETA_ATTR_NAME: Final[str] = "_beta"


@dataclass
class BetaInfo:
    additional_warn_text: Optional[str] = None
    subject: Optional[str] = None


@overload
def beta(
    __obj: T_Annotatable,
    *,
    additional_warn_text: Optional[str] = ...,
    subject: Optional[str] = ...,
    emit_runtime_warning: bool = ...,
) -> T_Annotatable: ...


@overload
def beta(
    __obj: None = ...,
    *,
    additional_warn_text: Optional[str] = ...,
    subject: Optional[str] = ...,
    emit_runtime_warning: bool = ...,
) -> Callable[[T_Annotatable], T_Annotatable]: ...


def beta(
    __obj: Optional[T_Annotatable] = None,
    *,
    additional_warn_text: Optional[str] = None,
    subject: Optional[str] = None,
    emit_runtime_warning: bool = True,
) -> Union[T_Annotatable, Callable[[T_Annotatable], T_Annotatable]]:
    """Mark an object as beta. This appends some metadata to the object that causes it to be
    rendered with a "beta" tag and associated warning in the docs.

    If `emit_runtime_warning` is True, a warning will also be emitted when the function is called,
    having the same text as is displayed in the docs. For consistency between docs and runtime
    warnings, this decorator is preferred to manual calls to `beta_warning`.

    Args:
        additional_warn_text (Optional[str]): Additional text to display after the beta warning.
        subject (Optional[str]): The subject of the beta warning. Defaults to a string
            representation of the decorated object. This is useful when marking usage of
            a beta API inside an otherwise non-beta function, so
            that it can be easily cleaned up later. It should only be used with
            `emit_runtime_warning=False`, as we don't want to warn users when a
            beta API is used internally.
        emit_runtime_warning (bool): Whether to emit a warning when the function is called.

    Usage:

        .. code-block:: python

            @beta
            def my_beta_function(my_arg):
                ...

            @beta
            class MyBetaClass:
                ...

            @beta(subject="some_beta_function", emit_runtime_warning=False)
            def not_beta_function():
                ...
                some_beta_function()
                ...
    """
    if __obj is None:
        return lambda obj: beta(
            obj,
            subject=subject,
            emit_runtime_warning=emit_runtime_warning,
            additional_warn_text=additional_warn_text,
        )
    else:
        target = _get_annotation_target(__obj)
        setattr(
            target,
            _BETA_ATTR_NAME,
            BetaInfo(additional_warn_text, subject),
        )

        if emit_runtime_warning:
            stack_level = _get_warning_stacklevel(__obj)
            subject = subject or _get_subject(__obj)
            warning_fn = lambda: beta_warning(
                subject,
                additional_warn_text=additional_warn_text,
                stacklevel=stack_level,
            )
            return apply_pre_call_decorator(__obj, warning_fn)
        else:
            return __obj


def is_beta(obj: Annotatable) -> bool:
    target = _get_annotation_target(obj)
    return hasattr(target, _BETA_ATTR_NAME)


def get_beta_info(obj: Annotatable) -> BetaInfo:
    target = _get_annotation_target(obj)
    return getattr(target, _BETA_ATTR_NAME)


# ########################
# ##### BETA PARAM
# ########################

_BETA_PARAM_ATTR_NAME: Final[str] = "_beta_params"


@overload
def beta_param(
    __obj: T_Annotatable,
    *,
    param: str,
    additional_warn_text: Optional[str] = ...,
    emit_runtime_warning: bool = ...,
) -> T_Annotatable: ...


@overload
def beta_param(
    __obj: None = ...,
    *,
    param: str,
    additional_warn_text: Optional[str] = ...,
    emit_runtime_warning: bool = ...,
) -> Callable[[T_Annotatable], T_Annotatable]: ...


def beta_param(
    __obj: Optional[T_Annotatable] = None,
    *,
    param: str,
    additional_warn_text: Optional[str] = None,
    emit_runtime_warning: bool = True,
) -> Union[T_Annotatable, Callable[[T_Annotatable], T_Annotatable]]:
    """Mark a parameter of a class initializer or function/method as beta. This appends some
    metadata to the decorated object that causes the specified argument to be rendered with a
    "beta" tag and associated warning in the docs.

    If `emit_runtime_warning` is True, a warning will also be emitted when the function is called
    and a non-None value is passed for the parameter. For consistency between docs and runtime
    warnings, this decorator is preferred to manual calls to `beta_warning`. Note that the
    warning will only be emitted if the value is passed as a keyword argument.

    Args:
        param (str): The name of the parameter to mark as beta.
        additional_warn_text (str): Additional text to display after the beta warning.
            Typically, this should suggest a newer API.
        emit_runtime_warning (bool): Whether to emit a warning when the function is called.
    """
    if __obj is None:
        return lambda obj: beta_param(
            obj,
            param=param,
            additional_warn_text=additional_warn_text,
            emit_runtime_warning=emit_runtime_warning,
        )
    else:
        check.invariant(
            _annotatable_has_param(__obj, param),
            f"Attempted to mark undefined parameter `{param}` beta.",
        )
        target = _get_annotation_target(__obj)

        if not hasattr(target, _BETA_PARAM_ATTR_NAME):
            setattr(target, _BETA_PARAM_ATTR_NAME, {})
        getattr(target, _BETA_PARAM_ATTR_NAME)[param] = BetaInfo(
            additional_warn_text=additional_warn_text,
        )

        if emit_runtime_warning:
            condition = lambda *_, **kwargs: kwargs.get(param) is not None
            warning_fn = lambda: beta_warning(
                _get_subject(__obj, param=param),
                additional_warn_text=additional_warn_text,
                stacklevel=4,
            )
            return apply_pre_call_decorator(__obj, warning_fn, condition=condition)
        else:
            return __obj


def has_beta_params(obj: Annotatable) -> bool:
    return hasattr(_get_annotation_target(obj), _BETA_PARAM_ATTR_NAME)


def get_beta_params(obj: Annotatable) -> Mapping[str, BetaInfo]:
    return getattr(_get_annotation_target(obj), _BETA_PARAM_ATTR_NAME)


def is_beta_param(obj: Annotatable, param_name: str) -> bool:
    target = _get_annotation_target(obj)
    return param_name in getattr(target, _BETA_PARAM_ATTR_NAME, {})


def get_beta_param_info(obj: Annotatable, param_name: str) -> BetaInfo:
    target = _get_annotation_target(obj)
    return getattr(target, _BETA_PARAM_ATTR_NAME)[param_name]


# ########################
# ##### SUPERSEDED
# ########################


_SUPERSEDED_ATTR_NAME: Final[str] = "_superseded"


@dataclass
class SupersededInfo:
    additional_warn_text: Optional[str] = None
    subject: Optional[str] = None


@overload
def superseded(
    __obj: T_Annotatable,
    *,
    additional_warn_text: Optional[str] = ...,
    subject: Optional[str] = ...,
    emit_runtime_warning: bool = ...,
) -> T_Annotatable: ...


@overload
def superseded(
    __obj: None = ...,
    *,
    additional_warn_text: Optional[str] = ...,
    subject: Optional[str] = ...,
    emit_runtime_warning: bool = ...,
) -> Callable[[T_Annotatable], T_Annotatable]: ...


def superseded(
    __obj: Optional[T_Annotatable] = None,
    *,
    additional_warn_text: Optional[str] = None,
    subject: Optional[str] = None,
    emit_runtime_warning: bool = True,
) -> Union[T_Annotatable, Callable[[T_Annotatable], T_Annotatable]]:
    # TODO: add "superseded" warning to docs
    """Mark an object as superseded. This appends some metadata to the object that causes it to be
    rendered with a "superseded" tag and associated warning in the docs.

    If `emit_runtime_warning` is True, a warning will also be emitted when the function is called,
    having the same text as is displayed in the docs. For consistency between docs and runtime
    warnings, this decorator is preferred to manual calls to `supersession_warning`.

    Args:
        additional_warn_text (Optional[str]): Additional text to display after the supersession warning.
            Typically this should suggest a newer API.
        subject (Optional[str]): The subject of the supersession warning. Defaults to a string
            representation of the decorated object. This is useful when marking usage of
            a superseded API inside an otherwise non-superseded function, so
            that it can be easily cleaned up later. It should only be used with
            `emit_runtime_warning=False`, as we don't want to warn users when a
            superseded API is used internally.
        emit_runtime_warning (bool): Whether to emit a warning when the function is called.

    Usage:

        .. code-block:: python

            @superseded(additional_warn_text="Use my_new_function instead")
            def my_superseded_function(my_arg):
                ...

            @superseded(additional_warn_text="Use MyNewClass instead")
            class MySupersededClass:
                ...

            @superseded(subject="some_superseded_function", emit_runtime_warning=False)
            def not_superseded_function():
                ...
                some_superseded_function()
                ...
    """
    if __obj is None:
        return lambda obj: superseded(
            obj,
            subject=subject,
            emit_runtime_warning=emit_runtime_warning,
            additional_warn_text=additional_warn_text,
        )
    else:
        target = _get_annotation_target(__obj)
        setattr(
            target,
            _SUPERSEDED_ATTR_NAME,
            SupersededInfo(additional_warn_text, subject),
        )

        if emit_runtime_warning:
            stack_level = _get_warning_stacklevel(__obj)
            subject = subject or _get_subject(__obj)
            warning_fn = lambda: supersession_warning(
                subject,
                additional_warn_text=additional_warn_text,
                stacklevel=stack_level,
            )
            return apply_pre_call_decorator(__obj, warning_fn)
        else:
            return __obj


def is_superseded(obj: Annotatable) -> bool:
    target = _get_annotation_target(obj)
    return hasattr(target, _SUPERSEDED_ATTR_NAME)


def get_superseded_info(obj: Annotatable) -> SupersededInfo:
    target = _get_annotation_target(obj)
    return getattr(target, _SUPERSEDED_ATTR_NAME)


# ########################
# ##### DEPRECATED
# ########################


_DEPRECATED_ATTR_NAME: Final[str] = "_deprecated"


@dataclass
class DeprecatedInfo:
    breaking_version: str
    hidden: bool
    additional_warn_text: Optional[str]
    subject: Optional[str]


@overload
def deprecated(
    __obj: T_Annotatable,
    *,
    breaking_version: str,
    additional_warn_text: Optional[str] = ...,
    subject: Optional[str] = ...,
    emit_runtime_warning: bool = ...,
) -> T_Annotatable: ...


@overload
def deprecated(
    __obj: None = ...,
    *,
    breaking_version: str,
    additional_warn_text: Optional[str] = ...,
    subject: Optional[str] = ...,
    emit_runtime_warning: bool = ...,
) -> Callable[[T_Annotatable], T_Annotatable]: ...


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
            subject=subject,
            emit_runtime_warning=emit_runtime_warning,
            breaking_version=breaking_version,
            additional_warn_text=additional_warn_text,
        )
    else:
        target = _get_annotation_target(__obj)
        setattr(
            target,
            _DEPRECATED_ATTR_NAME,
            DeprecatedInfo(
                breaking_version=breaking_version,
                additional_warn_text=additional_warn_text,
                subject=subject,
                hidden=False,
            ),
        )

        if emit_runtime_warning:
            stack_level = _get_warning_stacklevel(__obj)
            subject = subject or _get_subject(__obj)
            warning_fn = lambda: deprecation_warning(
                subject,
                breaking_version=breaking_version,
                additional_warn_text=additional_warn_text,
                stacklevel=stack_level,
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
# ##### DEPRECATED PARAM
# ########################

_DEPRECATED_PARAM_ATTR_NAME: Final[str] = "_deprecated_params"


@overload
def deprecated_param(
    __obj: T_Annotatable,
    *,
    param: str,
    breaking_version: str,
    additional_warn_text: Optional[str] = ...,
    emit_runtime_warning: bool = ...,
) -> T_Annotatable: ...


@overload
def deprecated_param(
    __obj: None = ...,
    *,
    param: str,
    breaking_version: str,
    additional_warn_text: Optional[str] = ...,
    emit_runtime_warning: bool = ...,
) -> Callable[[T_Annotatable], T_Annotatable]: ...


def deprecated_param(
    __obj: Optional[T_Annotatable] = None,
    *,
    param: str,
    breaking_version: str,
    additional_warn_text: Optional[str] = None,
    emit_runtime_warning: bool = True,
) -> T_Annotatable:
    """Mark a parameter of a class initializer or function/method as deprecated. This appends some
    metadata to the decorated object that causes the specified argument to be rendered with a
    "deprecated" tag and associated warning in the docs.

    If `emit_runtime_warning` is True, a warning will also be emitted when the function is called
    and a non-None value is passed for the parameter. For consistency between docs and runtime
    warnings, this decorator is preferred to manual calls to `deprecation_warning`. Note that the
    warning will only be emitted if the value is passed as a keyword argument.

    Args:
        param (str): The name of the parameter to deprecate.
        breaking_version (str): The version at which the deprecated function will be removed.
        additional_warn_text (str): Additional text to display after the deprecation warning.
            Typically this should suggest a newer API.
        emit_runtime_warning (bool): Whether to emit a warning when the function is called.
        hidden (bool): Whether or not this is a hidden parameters. Hidden parameters are only
            passed via kwargs and are hidden from the type signature. This makes it so
            that this hidden parameter does not appear in typeaheads. In order to provide
            high quality error messages we also provide the helper function
            only_allow_hidden_params_in_kwargs to ensure there are high quality
            error messages if the user passes an unsupported keyword argument.


    """
    if __obj is None:
        return lambda obj: deprecated_param(  # type: ignore
            obj,
            param=param,
            breaking_version=breaking_version,
            additional_warn_text=additional_warn_text,
            emit_runtime_warning=emit_runtime_warning,
        )
    else:
        return attach_deprecation_info_and_wrap(
            __obj,
            param=param,
            breaking_version=breaking_version,
            additional_warn_text=additional_warn_text,
            emit_runtime_warning=emit_runtime_warning,
            hidden=False,
        )


def attach_deprecation_info_and_wrap(
    obj: T_Annotatable,
    param: str,
    breaking_version: str,
    additional_warn_text: Optional[str] = None,
    emit_runtime_warning: bool = True,
    hidden: bool = False,
) -> T_Annotatable:
    if not hidden:
        check.invariant(
            _annotatable_has_param(obj, param),
            f"Attempted to mark undefined parameter `{param}` deprecated.",
        )
    target = _get_annotation_target(obj)
    if not hasattr(target, _DEPRECATED_PARAM_ATTR_NAME):
        setattr(target, _DEPRECATED_PARAM_ATTR_NAME, {})
    getattr(target, _DEPRECATED_PARAM_ATTR_NAME)[param] = DeprecatedInfo(
        breaking_version=breaking_version,
        additional_warn_text=additional_warn_text,
        hidden=hidden,
        subject=None,
    )

    if not emit_runtime_warning:
        return obj

    condition = lambda *_, **kwargs: kwargs.get(param) is not None
    warning_fn = lambda: deprecation_warning(
        _get_subject(obj, param=param),
        breaking_version=breaking_version,
        additional_warn_text=additional_warn_text,
        stacklevel=4,
    )
    return apply_pre_call_decorator(obj, warning_fn, condition=condition)


@overload
def hidden_param(
    __obj: T_Annotatable,
    *,
    param: str,
    breaking_version: str,
    additional_warn_text: Optional[str] = ...,
    emit_runtime_warning: bool = ...,
) -> T_Annotatable: ...


@overload
def hidden_param(
    __obj: None = ...,
    *,
    param: str,
    breaking_version: str,
    additional_warn_text: Optional[str] = ...,
    emit_runtime_warning: bool = ...,
) -> Callable[[T_Annotatable], T_Annotatable]: ...


def hidden_param(
    __obj: Optional[T_Annotatable] = None,
    *,
    param: str,
    breaking_version: str,
    additional_warn_text: Optional[str] = None,
    emit_runtime_warning: bool = True,
) -> T_Annotatable:
    """Hidden parameters are only passed via kwargs and are hidden from the
    type signature. This makes it so that this hidden parameter does not
    appear in typeaheads. In order to provide high quality error messages
    we also provide the helper function only_allow_hidden_params_in_kwargs
    to ensure there are high quality error messages if the user passes
    an unsupported keyword argument.

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

            @hidden_param(breaking_version="2.0", additional_warn_text="Use my_new_function instead")
            def func_with_hidden_args(**kwargs):
                only_allow_hidden_params_in_kwargs(func_with_hidden_args, kwargs)
    """
    if __obj is None:
        return lambda obj: hidden_param(  # type: ignore
            obj,
            param=param,
            breaking_version=breaking_version,
            additional_warn_text=additional_warn_text,
            emit_runtime_warning=emit_runtime_warning,
        )
    else:
        return attach_deprecation_info_and_wrap(
            __obj,
            param=param,
            breaking_version=breaking_version,
            additional_warn_text=additional_warn_text,
            emit_runtime_warning=emit_runtime_warning,
            hidden=True,
        )


def has_deprecated_params(obj: Annotatable) -> bool:
    return hasattr(_get_annotation_target(obj), _DEPRECATED_PARAM_ATTR_NAME)


def get_deprecated_params(obj: Annotatable) -> Mapping[str, DeprecatedInfo]:
    return getattr(_get_annotation_target(obj), _DEPRECATED_PARAM_ATTR_NAME)


def is_deprecated_param(obj: Annotatable, param_name: str) -> bool:
    target = _get_annotation_target(obj)
    return param_name in getattr(target, _DEPRECATED_PARAM_ATTR_NAME, {})


def get_deprecated_param_info(obj: Annotatable, param_name: str) -> DeprecatedInfo:
    target = _get_annotation_target(obj)
    return getattr(target, _DEPRECATED_PARAM_ATTR_NAME)[param_name]


# ########################
# ##### HELPERS
# ########################


def copy_annotations(dest: Annotatable, src: Annotatable) -> None:
    """Copy all Dagster annotations from one object to another object."""
    dest_target = _get_annotation_target(dest)
    src_target = _get_annotation_target(src)
    if hasattr(src_target, _PUBLIC_ATTR_NAME):
        setattr(dest_target, _PUBLIC_ATTR_NAME, getattr(src_target, _PUBLIC_ATTR_NAME))
    if hasattr(src_target, _DEPRECATED_ATTR_NAME):
        setattr(dest_target, _DEPRECATED_ATTR_NAME, getattr(src_target, _DEPRECATED_ATTR_NAME))
    if hasattr(src_target, _DEPRECATED_PARAM_ATTR_NAME):
        setattr(
            dest_target,
            _DEPRECATED_PARAM_ATTR_NAME,
            getattr(src_target, _DEPRECATED_PARAM_ATTR_NAME),
        )
    if hasattr(src_target, _SUPERSEDED_ATTR_NAME):
        setattr(dest_target, _SUPERSEDED_ATTR_NAME, getattr(src_target, _SUPERSEDED_ATTR_NAME))
    if hasattr(src_target, _PREVIEW_ATTR_NAME):
        setattr(dest_target, _PREVIEW_ATTR_NAME, getattr(src_target, _PREVIEW_ATTR_NAME))
    if hasattr(src_target, _BETA_ATTR_NAME):
        setattr(dest_target, _BETA_ATTR_NAME, getattr(src_target, _BETA_ATTR_NAME))
    if hasattr(src_target, _BETA_PARAM_ATTR_NAME):
        setattr(
            dest_target,
            _BETA_PARAM_ATTR_NAME,
            getattr(src_target, _BETA_PARAM_ATTR_NAME),
        )

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


def _get_subject(obj: Annotatable, param: Optional[str] = None) -> str:
    """Get the string representation of an annotated object that will appear in
    annotation-generated warnings about the object.
    """
    if param:
        if isinstance(obj, type):
            return f"Parameter `{param}` of initializer `{obj.__qualname__}.__init__`"
        else:
            fn_subject = _get_subject(obj)
            return f"Parameter `{param}` of {fn_subject[:1].lower() + fn_subject[1:]}"
    else:
        if isinstance(obj, type):
            return f"Class `{obj.__qualname__}`"
        elif isinstance(obj, property):
            return f"Property `{obj.fget.__qualname__ if obj.fget else obj}`"
        # classmethod and staticmethod don't themselves get a `__qualname__` attr until Python 3.10.
        elif isinstance(obj, classmethod):
            return f"Class method `{_get_annotation_target(obj).__qualname__}`"
        elif isinstance(obj, staticmethod):
            return f"Static method `{_get_annotation_target(obj).__qualname__}`"
        elif inspect.isfunction(obj):
            return f"Function `{obj.__qualname__}`"
        elif is_resource_def(obj):
            return f"Dagster resource `{obj.__qualname__}`"
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


def _annotatable_has_param(obj: Annotatable, param: str) -> bool:
    target_fn = get_decorator_target(obj)
    return param in inspect.signature(target_fn).parameters


def only_allow_hidden_params_in_kwargs(annotatable: Annotatable, kwargs: Mapping[str, Any]) -> None:
    deprecated_params = (
        get_deprecated_params(annotatable) if has_deprecated_params(annotatable) else {}
    )
    for param in kwargs:
        if param not in deprecated_params:
            raise TypeError(f"{annotatable.__name__} got an unexpected keyword argument '{param}'")

        check.invariant(
            deprecated_params[param].hidden,
            f"Unexpected non-hidden deprecated parameter '{param}' in kwargs. Should never get here.",
        )
