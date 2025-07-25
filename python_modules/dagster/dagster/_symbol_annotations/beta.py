import inspect
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Callable, Final, Optional, Union, overload

from dagster import _check as check
from dagster._core.decorator_utils import apply_pre_call_decorator, get_decorator_target
from dagster._symbol_annotations.annotatable import (
    Annotatable,
    T_Annotatable,
    _get_annotation_target,
    _get_subject,
)
from dagster._utils.warnings import beta_warning

_BETA_ATTR_NAME: Final[str] = "_beta"
_BETA_PARAM_ATTR_NAME: Final[str] = "_beta_params"


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
            from dagster._symbol_annotations._helpers import _get_warning_stacklevel

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


def _annotatable_has_param(obj: Annotatable, param: str) -> bool:
    target_fn = get_decorator_target(obj)
    return param in inspect.signature(target_fn).parameters
