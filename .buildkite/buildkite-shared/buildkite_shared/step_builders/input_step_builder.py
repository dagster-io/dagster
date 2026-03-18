from collections.abc import Sequence
from typing import Any, Self

from typing_extensions import Required, TypedDict


class InputStepConfiguration(TypedDict, closed=True, total=False):
    input: Required[str]
    fields: Required[list[dict[str, Any]]]
    key: str | None
    depends_on: list[str]
    # Covers the "if" key, which is a Python reserved word and cannot be used as
    # a class attribute. Buildkite uses "if" for conditional step execution.
    __extra_items__: str | None


class InputStepBuilder:
    _step: InputStepConfiguration

    def __init__(self, prompt: str, fields: list[dict[str, Any]], key: str | None = None) -> None:
        self._step: InputStepConfiguration = {"input": prompt, "fields": fields}
        if key is not None:
            self._step["key"] = key

    def with_condition(self, condition: str) -> Self:
        self._step["if"] = condition  # pyright: ignore[reportGeneralTypeIssues]
        return self

    def depends_on(self, dependencies: str | Sequence[str]) -> Self:
        self._step["depends_on"] = (
            [dependencies] if isinstance(dependencies, str) else list(dependencies)
        )
        return self

    def build(self) -> InputStepConfiguration:
        return self._step
