# pylint disable is for bug: https://github.com/PyCQA/pylint/issues/3299
from collections.abc import Generator, Sequence
from typing import Any, Generic, Optional, TypeVar

import dagster._check as check
from dagster._config.errors import EvaluationError
from dagster._record import record

T = TypeVar("T")


@record
class EvaluateValueResult(Generic[T]):
    success: bool
    value: Optional[T]
    errors: Optional[Sequence[EvaluationError]]

    @staticmethod
    def for_error(error: EvaluationError) -> "EvaluateValueResult[Any]":
        return EvaluateValueResult(success=False, value=None, errors=[error])

    @staticmethod
    def for_errors(errors: Sequence[EvaluationError]) -> "EvaluateValueResult[Any]":
        return EvaluateValueResult(success=False, value=None, errors=errors)

    @staticmethod
    def for_value(value: T) -> "EvaluateValueResult[T]":
        return EvaluateValueResult(success=True, value=value, errors=None)

    def errors_at_level(self, *levels: str) -> Sequence[EvaluationError]:
        return list(self._iterate_errors_at_level(list(levels)))

    def _iterate_errors_at_level(
        self, levels: Sequence[str]
    ) -> Generator[EvaluationError, None, None]:
        check.sequence_param(levels, "levels", of_type=str)
        for error in check.is_list(self.errors):
            if error.stack.levels == levels:
                yield error
