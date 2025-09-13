# mypy does not support recursive types, so "cause" has to be typed `Any`
import os
import sys
import traceback
from collections.abc import Sequence
from typing import Any, Callable, NamedTuple, Optional

from typing_extensions import Self

from dagster_shared.serdes.serdes import whitelist_for_serdes


class DagsterError(Exception):
    """Base class for all errors thrown by the Dagster framework.

    Users should not subclass this base class for their own exceptions.
    """

    @property
    def is_user_code_error(self):
        """Returns true if this error is attributable to user code."""
        return False


class DagsterUnresolvableSymbolError(DagsterError):
    """Exception raised when a Python symbol reference can't be resolved."""


# TODO: Eventually we need to move the rest of the code in dagster._utils.error into dagster_shared,
# but that is a significant refactor. Currently we're just moving SerializableErrorInfo so that we
# can use it with the dg packages`.
@whitelist_for_serdes
class SerializableErrorInfo(
    NamedTuple(
        "SerializableErrorInfo",
        [
            ("message", str),
            ("stack", Sequence[str]),
            ("cls_name", Optional[str]),
            ("cause", Any),
            ("context", Any),
        ],
    )
):
    # serdes log
    # * added cause - default to None in constructor to allow loading old entries
    # * added context - default to None for similar reasons
    #
    def __new__(
        cls,
        message: str,
        stack: Sequence[str],
        cls_name: Optional[str],
        cause: Optional["SerializableErrorInfo"] = None,
        context: Optional["SerializableErrorInfo"] = None,
    ):
        return super().__new__(cls, message, stack, cls_name, cause, context)

    def __str__(self) -> str:
        return self.to_string()

    def to_string(self) -> str:
        stack_str = "\nStack Trace:\n" + "".join(self.stack) if self.stack else ""
        cause_str = (
            "\nThe above exception was caused by the following exception:\n"
            + self.cause.to_string()
            if self.cause
            else ""
        )
        context_str = (
            "\nThe above exception occurred during handling of the following exception:\n"
            + self.context.to_string()
            if self.context
            else ""
        )

        return f"{self.message}{stack_str}{cause_str}{context_str}"

    def to_exception_message_only(self) -> "SerializableErrorInfo":
        """Return a new SerializableErrorInfo with only the message and cause set.

        This is done in cases when the context about the error should not be exposed to the user.
        """
        return SerializableErrorInfo(message=self.message, stack=[], cls_name=self.cls_name)

    @classmethod
    def from_traceback(cls, tb: traceback.TracebackException) -> Self:
        if sys.version_info >= (3, 13):
            name = tb.exc_type_str.split(".")[-1]
        else:
            name = tb.exc_type.__name__ if tb.exc_type is not None else None

        return cls(
            # usually one entry, multiple lines for SyntaxError
            message="".join(list(tb.format_exception_only())),
            stack=tb.stack.format(),
            cls_name=name,
            cause=cls.from_traceback(tb.__cause__) if tb.__cause__ else None,
            context=cls.from_traceback(tb.__context__)
            if tb.__context__ and not tb.__suppress_context__
            else None,
        )


DAGSTER_FRAMEWORK_SUBSTRINGS = [
    os.sep + os.path.join("site-packages", "dagster"),
    os.sep + os.path.join("python_modules", "dagster"),
    os.sep + os.path.join("python_modules", "libraries", "dagster"),
]

IMPORT_MACHINERY_SUBSTRINGS = [
    os.path.join("importlib", "__init__.py"),
    os.path.join("importlib", "metadata", "__init__.py"),
    "importlib._bootstrap",
]


NO_HINT = lambda _, __: None


def remove_system_frames_from_error(
    error_info: SerializableErrorInfo,
    build_system_frame_removed_hint: Callable[[bool, int], Optional[str]] = NO_HINT,
) -> SerializableErrorInfo:
    """Remove system frames from a SerializableErrorInfo, including Dagster framework boilerplate
    and import machinery, which are generally not useful for users to debug their code.
    """
    return remove_matching_lines_from_error_info(
        error_info,
        DAGSTER_FRAMEWORK_SUBSTRINGS + IMPORT_MACHINERY_SUBSTRINGS,
        build_system_frame_removed_hint,
    )


def make_simple_frames_removed_hint(
    additional_first_hint_warning: Optional[str] = None,
) -> Callable[[bool, int], Optional[str]]:
    def frames_removed_hint(is_first_hidden_frame: bool, num_hidden_frames: int) -> Optional[str]:
        base_hint = f"{num_hidden_frames} dagster system frames hidden"
        if is_first_hidden_frame and additional_first_hint_warning:
            return f"  [{base_hint}, {additional_first_hint_warning}]\n"
        else:
            return f"  [{base_hint}]\n"

    return frames_removed_hint


def remove_matching_lines_from_error_info(
    error_info: SerializableErrorInfo,
    match_substrs: Sequence[str],
    build_system_frame_removed_hint: Callable[[bool, int], Optional[str]],
) -> SerializableErrorInfo:
    """Utility which truncates a stacktrace to drop lines which match the given strings.
    This is useful for e.g. removing Dagster framework lines from a stacktrace that
    involves user code.

    Args:
        error_info (SerializableErrorInfo): The error info to truncate
        matching_lines (Sequence[str]): The lines to truncate from the stacktrace

    Returns:
        SerializableErrorInfo: A new error info with the stacktrace truncated
    """
    return error_info._replace(
        stack=remove_matching_lines_from_stack_trace(
            error_info.stack, match_substrs, build_system_frame_removed_hint
        ),
        cause=(
            remove_matching_lines_from_error_info(
                error_info.cause, match_substrs, build_system_frame_removed_hint
            )
            if error_info.cause
            else None
        ),
        context=(
            remove_matching_lines_from_error_info(
                error_info.context, match_substrs, build_system_frame_removed_hint
            )
            if error_info.context
            else None
        ),
    )


def remove_matching_lines_from_stack_trace(
    stack: Sequence[str],
    matching_lines: Sequence[str],
    build_system_frame_removed_hint: Callable[[bool, int], Optional[str]],
) -> Sequence[str]:
    ctr = 0
    out = []
    is_first_hidden_frame = True

    for i in range(len(stack)):
        if not _line_contains_matching_string(stack[i], matching_lines):
            if ctr > 0:
                hint = build_system_frame_removed_hint(is_first_hidden_frame, ctr)
                is_first_hidden_frame = False
                if hint:
                    out.append(hint)
            ctr = 0
            out.append(stack[i])
        else:
            ctr += 1

    if ctr > 0:
        hint = build_system_frame_removed_hint(is_first_hidden_frame, ctr)
        if hint:
            out.append(hint)

    return out


def _line_contains_matching_string(line: str, matching_strings: Sequence[str]):
    split_by_comma = line.split(",")
    if not split_by_comma:
        return False

    file_portion = split_by_comma[0]
    return any(framework_substring in file_portion for framework_substring in matching_strings)
