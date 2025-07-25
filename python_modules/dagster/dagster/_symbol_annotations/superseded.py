from dataclasses import dataclass
from typing import Callable, Final, Optional, Union, overload

from dagster._core.decorator_utils import apply_pre_call_decorator
from dagster._symbol_annotations.annotatable import (
    Annotatable,
    T_Annotatable,
    _get_annotation_target,
    _get_subject,
)
from dagster._utils.warnings import supersession_warning

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
            from dagster._symbol_annotations._helpers import _get_warning_stacklevel

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
