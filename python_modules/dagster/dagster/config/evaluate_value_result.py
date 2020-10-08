from collections import namedtuple

from dagster import check

from .errors import EvaluationError


class EvaluateValueResult(namedtuple("_EvaluateValueResult", "success value errors")):
    def __new__(cls, success, value, errors):
        return super(EvaluateValueResult, cls).__new__(
            cls,
            check.opt_bool_param(success, "success"),
            value,
            check.opt_list_param(errors, "errors", of_type=EvaluationError),
        )

    @staticmethod
    def for_error(error):
        return EvaluateValueResult(False, None, [error])

    @staticmethod
    def for_errors(errors):
        return EvaluateValueResult(False, None, errors)

    @staticmethod
    def for_value(value):
        return EvaluateValueResult(True, value, None)

    def errors_at_level(self, *levels):
        return list(self._iterate_errors_at_level(list(levels)))

    def _iterate_errors_at_level(self, levels):
        check.list_param(levels, "levels", of_type=str)
        for error in self.errors:
            if error.stack.levels == levels:
                yield error
