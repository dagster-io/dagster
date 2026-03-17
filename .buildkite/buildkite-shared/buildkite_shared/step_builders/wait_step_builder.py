from collections.abc import Sequence
from typing import Self

from typing_extensions import Required, TypedDict


class WaitStepConfiguration(TypedDict, total=False):
    label: Required[str]
    wait: None
    key: str
    depends_on: list[str]
    continue_on_failure: bool


class WaitStepBuilder:
    _step: WaitStepConfiguration

    def __init__(self, key: str | None = None):
        self._step = {"wait": None, "label": ""}
        if key is not None:
            self._step["key"] = key

    def depends_on(self, dependencies: str | Sequence[str]) -> Self:
        self._step["depends_on"] = (
            [dependencies] if isinstance(dependencies, str) else list(dependencies)
        )
        return self

    def continue_on_failure(self) -> Self:
        self._step["continue_on_failure"] = True
        return self

    def build(self) -> WaitStepConfiguration:
        return self._step
