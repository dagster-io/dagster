import sys

from dagster.utils.error import serializable_error_info_from_exc_info


def capture_dauphin_error(fn):
    def _fn(*args, **kwargs):
        from dagster_graphql.schema.errors import DauphinPythonError

        try:
            return fn(*args, **kwargs)
        except UserFacingGraphQLError as de_exception:
            return de_exception.dauphin_error
        except Exception:  # pylint: disable=broad-except
            return DauphinPythonError(serializable_error_info_from_exc_info(sys.exc_info()))

    return _fn


class UserFacingGraphQLError(Exception):
    def __init__(self, dauphin_error, *args, **kwargs):
        self.dauphin_error = dauphin_error
        super(UserFacingGraphQLError, self).__init__(*args, **kwargs)
