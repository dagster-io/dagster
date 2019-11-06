import traceback
from collections import namedtuple

from dagster.core.serdes import whitelist_for_serdes


@whitelist_for_serdes
class SerializableErrorInfo(namedtuple('SerializableErrorInfo', 'message stack cls_name')):
    def to_string(self):
        return '({err.cls_name}) - {err.message}\nStack Trace: \n{stack}'.format(
            err=self, stack=''.join(self.stack)
        )


def serializable_error_info_from_exc_info(exc_info):
    exc_type, exc_value, exc_tb = exc_info

    return SerializableErrorInfo(
        traceback.format_exception_only(exc_type, exc_value)[0],
        traceback.format_tb(tb=exc_tb),
        exc_type.__name__,
    )
