import contextlib
import logging
import os
import sys
import traceback
import uuid
from collections.abc import Mapping, Sequence
from contextvars import ContextVar
from types import TracebackType
from typing import Any, NamedTuple, Optional, Union

from typing_extensions import TypeAlias

import dagster._check as check
from dagster._core.errors import DagsterUserCodeExecutionError
from dagster._serdes import whitelist_for_serdes


# mypy does not support recursive types, so "cause" has to be typed `Any`
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


def _serializable_error_info_from_tb(tb: traceback.TracebackException) -> SerializableErrorInfo:
    return SerializableErrorInfo(
        # usually one entry, multiple lines for SyntaxError
        "".join(list(tb.format_exception_only())),
        tb.stack.format(),
        tb.exc_type.__name__ if tb.exc_type is not None else None,
        _serializable_error_info_from_tb(tb.__cause__) if tb.__cause__ else None,
        _serializable_error_info_from_tb(tb.__context__) if tb.__context__ else None,
    )


ExceptionInfo: TypeAlias = Union[
    tuple[type[BaseException], BaseException, TracebackType],
    tuple[None, None, None],
]


def _should_redact_user_code_error() -> bool:
    return str(os.getenv("DAGSTER_REDACT_USER_CODE_ERRORS")).lower() in ("1", "true", "t")


_REDACTED_ERROR_LOGGER_NAME = os.getenv(
    "DAGSTER_REDACTED_ERROR_LOGGER_NAME", "dagster.redacted_errors"
)

error_id_by_exception: ContextVar[Mapping[int, str]] = ContextVar(
    "error_id_by_exception", default={}
)


@contextlib.contextmanager
def log_and_redact_stacktrace_if_enabled():
    if not _should_redact_user_code_error():
        yield
    else:
        try:
            yield
        except BaseException as e:
            exc_info = sys.exc_info()

            # Generate a unique error ID for this error, or re-use an existing one
            # if this error has already been seen
            existing_error_id = error_id_by_exception.get().get(id(e))

            if not existing_error_id:
                error_id = str(uuid.uuid4())
                error_id_by_exception.set({**error_id_by_exception.get(), id(e): error_id})
                masked_logger = logging.getLogger(_REDACTED_ERROR_LOGGER_NAME)

                masked_logger.error(
                    f"Error occurred during user code execution, error ID {error_id}",
                    exc_info=exc_info,
                )

            raise e.with_traceback(None) from None


def serializable_error_info_from_exc_info(
    exc_info: ExceptionInfo,
    # Whether to forward serialized errors thrown from subprocesses
    hoist_user_code_error: Optional[bool] = True,
) -> SerializableErrorInfo:
    """This function is used to turn an exception into a serializable object that can be passed
    across process boundaries or sent over GraphQL.

    Args:
        exc_info (ExceptionInfo): The exception info to serialize
        hoist_user_code_error (Optional[bool]): Whether to extract the inner user code error if the raised exception
            is a DagsterUserCodeProcessError. Defaults to True.
    """
    # `sys.exc_info() return Tuple[None, None, None] when there is no exception being processed. We accept this in
    # the type signature here since this function is meant to directly receive the return value of
    # `sys.exc_info`, but the function should never be called when there is no exception to process.
    exc_type, e, tb = exc_info
    additional_message = "sys.exc_info() called but no exception available to process."
    exc_type = check.not_none(exc_type, additional_message=additional_message)
    e = check.not_none(e, additional_message=additional_message)
    tb = check.not_none(tb, additional_message=additional_message)

    from dagster._core.errors import DagsterUserCodeProcessError

    err_id = error_id_by_exception.get().get(id(e))
    if err_id:
        if isinstance(e, DagsterUserCodeExecutionError):
            return SerializableErrorInfo(
                message=(
                    f"Error occurred during user code execution, error ID {err_id}. "
                    "The error has been masked to prevent leaking sensitive information. "
                    "Search in logs for this error ID for more details."
                ),
                stack=[],
                cls_name="DagsterRedactedUserCodeError",
                cause=None,
                context=None,
            )
        else:
            tb_exc = traceback.TracebackException(exc_type, e, tb)
            error_info = _serializable_error_info_from_tb(tb_exc)
            return SerializableErrorInfo(
                message=error_info.message
                + (
                    f"Error ID {err_id}. "
                    "The error has been masked to prevent leaking sensitive information. "
                    "Search in logs for this error ID for more details."
                ),
                stack=[],
                cls_name=error_info.cls_name,
                cause=None,
                context=None,
            )

    if (
        hoist_user_code_error
        and isinstance(e, DagsterUserCodeProcessError)
        and len(e.user_code_process_error_infos) == 1
    ):
        return e.user_code_process_error_infos[0]
    else:
        tb_exc = traceback.TracebackException(exc_type, e, tb)
        return _serializable_error_info_from_tb(tb_exc)
