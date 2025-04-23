import contextlib
import logging
import os
import sys
import traceback
import uuid
from types import TracebackType
from typing import Optional, Union

from dagster_shared.error import SerializableErrorInfo
from typing_extensions import TypeAlias

import dagster._check as check
from dagster._core.errors import DagsterUserCodeExecutionError

ExceptionInfo: TypeAlias = Union[
    tuple[type[BaseException], BaseException, TracebackType],
    tuple[None, None, None],
]


def _should_redact_user_code_error() -> bool:
    return str(os.getenv("DAGSTER_REDACT_USER_CODE_ERRORS")).lower() in ("1", "true", "t")


_REDACTED_ERROR_LOGGER_NAME = os.getenv(
    "DAGSTER_REDACTED_ERROR_LOGGER_NAME", "dagster.redacted_errors"
)


USER_FACING_ERROR_ID_ATTR_NAME = "_redacted_error_uuid"


class DagsterRedactedUserCodeError(DagsterUserCodeExecutionError):
    pass


@contextlib.contextmanager
def redact_user_stacktrace_if_enabled():
    """Context manager which, if a user has enabled redacting user code errors, logs exceptions raised from within,
    and clears the stacktrace from the exception. It also marks the exception to be redacted if it was to be persisted
    or otherwise serialized to be sent to Dagster Plus. This is useful for preventing sensitive information from
    being leaked in error messages.
    """
    if not _should_redact_user_code_error():
        yield
    else:
        try:
            yield
        except BaseException as e:
            exc_info = sys.exc_info()

            # Generate a unique error ID for this error, or re-use an existing one
            # if this error has already been seen
            existing_error_id = getattr(e, USER_FACING_ERROR_ID_ATTR_NAME, None)

            if not existing_error_id:
                error_id = str(uuid.uuid4())

                # Track the error ID for this exception so we can redact it later
                setattr(e, USER_FACING_ERROR_ID_ATTR_NAME, error_id)
                masked_logger = logging.getLogger(_REDACTED_ERROR_LOGGER_NAME)

                masked_logger.error(
                    f"Error occurred during user code execution, error ID {error_id}",
                    exc_info=exc_info,
                )
            else:
                error_id = existing_error_id

            if isinstance(e, DagsterUserCodeExecutionError):
                # To be especially sure that user code error information doesn't leak from
                # outside the context, we raise a new exception with a cleared original_exc_info
                # The only remnant that remains is user_exception, which we only use to allow the user
                # to retrieve exceptions in hooks
                try:
                    raise Exception("Masked").with_traceback(None) from None
                except Exception as dummy_exception:
                    redacted_exception = DagsterRedactedUserCodeError(
                        f"Error occurred during user code execution, error ID {error_id}. "
                        "The error has been masked to prevent leaking sensitive information. "
                        "Search in logs for this error ID for more details.",
                        user_exception=e.user_exception,
                        original_exc_info=sys.exc_info(),
                    ).with_traceback(None)
                    setattr(dummy_exception, USER_FACING_ERROR_ID_ATTR_NAME, error_id)
                    setattr(redacted_exception, USER_FACING_ERROR_ID_ATTR_NAME, error_id)
                    raise redacted_exception from None

            # Redact the stacktrace to ensure it will not be passed to Dagster Plus
            raise e.with_traceback(None) from None


def _generate_redacted_user_code_error_message(err_id: str) -> SerializableErrorInfo:
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


def _generate_partly_redacted_framework_error_message(
    exc_info: ExceptionInfo, err_id: str
) -> SerializableErrorInfo:
    exc_type, e, tb = exc_info
    tb_exc = traceback.TracebackException(check.not_none(exc_type), check.not_none(e), tb)
    error_info = SerializableErrorInfo.from_traceback(tb_exc)

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

    err_id = getattr(e, USER_FACING_ERROR_ID_ATTR_NAME, None)
    if err_id:
        if isinstance(e, DagsterUserCodeExecutionError):
            # For user code, we want to completely mask the error message, since
            # both the stacktrace and the message could contain sensitive information
            return _generate_redacted_user_code_error_message(err_id)
        else:
            # For all other errors (framework errors, interrupts),
            # we want to redact the error message, but keep the stacktrace
            return _generate_partly_redacted_framework_error_message(exc_info, err_id)

    if (
        hoist_user_code_error
        and isinstance(e, DagsterUserCodeProcessError)
        and len(e.user_code_process_error_infos) == 1
    ):
        return e.user_code_process_error_infos[0]
    else:
        tb_exc = traceback.TracebackException(exc_type, e, tb)
        return SerializableErrorInfo.from_traceback(tb_exc)


DAGSTER_FRAMEWORK_SUBSTRINGS = [
    "/site-packages/dagster",
    "/python_modules/dagster",
    "/python_modules/libraries/dagster",
]

IMPORT_MACHINERY_SUBSTRINGS = [
    "importlib/__init__.py",
    "importlib._bootstrap",
]


def unwrap_user_code_error(error_info: SerializableErrorInfo) -> SerializableErrorInfo:
    """Extracts the underlying error from the passed error, if it is a DagsterUserCodeLoadError."""
    if error_info.cls_name == "DagsterUserCodeLoadError":
        return unwrap_user_code_error(error_info.cause)
    return error_info
