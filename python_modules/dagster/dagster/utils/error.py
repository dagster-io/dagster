from collections import namedtuple

import traceback

SerializableErrorInfo = namedtuple('SerializableErrorInfo', 'message stack cls_name')


def serializable_error_info_from_exc_info(exc_info):
    exc_type, exc_value, exc_tb = exc_info

    return SerializableErrorInfo(
        traceback.format_exception_only(exc_type, exc_value)[0],
        traceback.format_tb(tb=exc_tb),
        exc_type.__name__,
    )
