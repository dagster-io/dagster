import traceback
from collections import namedtuple
from types import TracebackType
from typing import List, Optional, Tuple, Type, Union

from dagster.serdes import whitelist_for_serdes


@whitelist_for_serdes
class SerializableErrorInfo(namedtuple("SerializableErrorInfo", "message stack cls_name cause")):
    # serdes log
    # * added cause - default to None in constructor to allow loading old entries
    #
    def __new__(
        cls, message: str, stack: List[str], cls_name: str, cause: "SerializableErrorInfo" = None
    ):
        return super().__new__(cls, message, stack, cls_name, cause)

    def to_string(self):
        stack_str = "\nStack Trace:\n" + "".join(self.stack) if self.stack else ""
        cause_str = (
            "\nThe above exception was the direct cause of the following exception:\n"
            + self.cause.to_string()
            if self.cause
            else ""
        )
        return "{err.message}{stack}{cause}".format(err=self, stack=stack_str, cause=cause_str)


def _serializable_error_info_from_tb(tb: traceback.TracebackException) -> SerializableErrorInfo:
    return SerializableErrorInfo(
        # usually one entry, multiple lines for SyntaxError
        "".join(list(tb.format_exception_only())),
        tb.stack.format(),
        tb.exc_type.__name__ if tb.exc_type is not None else None,
        _serializable_error_info_from_tb(tb.__cause__) if tb.__cause__ else None,
    )


def serializable_error_info_from_exc_info(
    exc_info: Union[
        Tuple[Type[BaseException], BaseException, TracebackType], Tuple[None, None, None]
    ],
    # Whether to forward serialized errors thrown from subprocesses
    hoist_user_code_error: Optional[bool] = True,
) -> SerializableErrorInfo:
    _exc_type, e, _tb = exc_info
    from dagster.core.errors import DagsterUserCodeProcessError

    if (
        hoist_user_code_error
        and isinstance(e, DagsterUserCodeProcessError)
        and len(e.user_code_process_error_infos) == 1
    ):
        return e.user_code_process_error_infos[0]
    else:
        return _serializable_error_info_from_tb(traceback.TracebackException(*exc_info))
