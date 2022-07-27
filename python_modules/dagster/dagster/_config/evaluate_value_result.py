# pylint disable is for bug: https://github.com/PyCQA/pylint/issues/3299
from typing import Any, Generator, Generic, List, Optional, TypeVar  # pylint: disable=unused-import

import dagster._check as check

from .errors import EvaluationError

T = TypeVar("T")

# Python 3.6 doesn't simultaneously support NamedTuple and Generic, so we omit
# the usual NamedTuple pattern here. See:
# https://stackoverflow.com/questions/50530959/generic-namedtuple-in-python-3-6
class EvaluateValueResult(Generic[T]):

    success: Optional[bool]
    value: Optional[T]
    errors: Optional[List[EvaluationError]]

    def __init__(self, success: Optional[bool], value: T, errors: Optional[List[EvaluationError]]):
        self.success = check.opt_bool_param(success, "success")
        self.value = value
        self.errors = check.opt_list_param(errors, "errors", of_type=EvaluationError)

    @staticmethod
    def for_error(error: EvaluationError) -> "EvaluateValueResult[Any]":
        return EvaluateValueResult(False, None, [error])

    @staticmethod
    def for_errors(errors: List[EvaluationError]) -> "EvaluateValueResult[Any]":
        return EvaluateValueResult(False, None, errors)

    @staticmethod
    def for_value(value: T) -> "EvaluateValueResult[T]":
        return EvaluateValueResult(True, value, None)

    def errors_at_level(self, *levels: str) -> List[EvaluationError]:
        return list(self._iterate_errors_at_level(list(levels)))

    def _iterate_errors_at_level(self, levels: List[str]) -> Generator[EvaluationError, None, None]:
        check.list_param(levels, "levels", of_type=str)
        for error in check.is_list(self.errors):
            if error.stack.levels == levels:
                yield error
