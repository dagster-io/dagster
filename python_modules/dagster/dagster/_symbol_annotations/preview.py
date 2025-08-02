from dataclasses import dataclass
from typing import Callable, Final, Optional, Union, overload

from dagster._core.decorator_utils import apply_pre_call_decorator
from dagster._symbol_annotations.annotatable import (
    T_Annotatable,
    _get_annotation_target,
    _get_subject,
)
from dagster._utils.warnings import preview_warning

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
            from dagster._symbol_annotations._helpers import _get_warning_stacklevel

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


def is_preview(obj) -> bool:
    target = _get_annotation_target(obj)
    return hasattr(target, _PREVIEW_ATTR_NAME)


def get_preview_info(obj) -> PreviewInfo:
    target = _get_annotation_target(obj)
    return getattr(target, _PREVIEW_ATTR_NAME)
