import logging
from typing import Optional

from dagster._utils.error import (
    ExceptionInfo,
    SerializableErrorInfo,
    serializable_error_info_from_exc_info,
)


class DaemonErrorCapture:
    @staticmethod
    def default_on_exception(
        exc_info: ExceptionInfo,
        logger: Optional[logging.Logger] = None,
        log_message: Optional[str] = None,
    ) -> SerializableErrorInfo:
        error_info = serializable_error_info_from_exc_info(exc_info)
        if logger and log_message:
            logger.exception(log_message)
        return error_info

    # global behavior for how to handle unexpected exceptions
    on_exception = default_on_exception
