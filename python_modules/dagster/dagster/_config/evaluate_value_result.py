# pylint disable is for bug: https://github.com/PyCQA/pylint/issues/3299
from typing import (  # pylint: disable=unused-import
    Any,
    Generator,
    Generic,
    Optional,
    Sequence,
    TypeVar,
)

from typing_extensions import NamedTuple

import dagster._check as check

from .errors import EvaluationError

T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)

class EvaluateValueResult(
    NamedTuple(
        "_EvaluateValueResult",
        [
            ("success", bool),
            ("value", T_co),
            ("errors", Sequence[EvaluationError]),
        ],
    ),
    Generic[T_co],
):
    def __new__(cls, value: T_co, errors: Optional[Sequence[EvaluationError]] = None):
        return super(EvaluateValueResult, cls).__new__(
            cls,
            errors is None,
            value,
            check.opt_sequence_param(errors, "errors", of_type=EvaluationError),
        )

    @staticmethod
    def valid(value: T) -> "EvaluateValueResult[T]":
        return EvaluateValueResult(value)

    @staticmethod
    def invalid(value: T, *errors: EvaluationError) -> "EvaluateValueResult[T]":
        return EvaluateValueResult(value, errors)

    def errors_at_level(self, *levels: str) -> Sequence[EvaluationError]:
        return list(self._iterate_errors_at_level(list(levels)))

    def _iterate_errors_at_level(
        self, levels: Sequence[str]
    ) -> Generator[EvaluationError, None, None]:
        check.sequence_param(levels, "levels", of_type=str)
        for error in check.is_list(self.errors):
            if error.stack.levels == levels:
                yield error
