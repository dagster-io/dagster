import traceback
from collections import namedtuple

from dagster.serdes import whitelist_for_serdes


@whitelist_for_serdes
class SerializableErrorInfo(namedtuple("SerializableErrorInfo", "message stack cls_name cause")):
    # serdes log
    # * added cause - default to None in constructor to allow loading old entries
    #
    def __new__(cls, message, stack, cls_name, cause=None):
        return super(SerializableErrorInfo, cls).__new__(cls, message, stack, cls_name, cause)

    def to_string(self):
        stack_str = "\nStack Trace:\n" + "".join(self.stack) if self.stack else ""
        cause_str = (
            "\nThe above exception was the direct cause of the following exception:\n"
            + self.cause.to_string()
            if self.cause
            else ""
        )
        return "{err.message}{stack}{cause}".format(err=self, stack=stack_str, cause=cause_str)


def _serializable_error_info_from_tb(tb):
    return SerializableErrorInfo(
        # usually one entry, multiple lines for SyntaxError
        "".join(list(tb.format_exception_only())),
        tb.stack.format(),
        tb.exc_type.__name__ if tb.exc_type is not None else None,
        _serializable_error_info_from_tb(tb.__cause__) if tb.__cause__ else None,
    )


def serializable_error_info_from_exc_info(exc_info):
    return _serializable_error_info_from_tb(traceback.TracebackException(*exc_info))
