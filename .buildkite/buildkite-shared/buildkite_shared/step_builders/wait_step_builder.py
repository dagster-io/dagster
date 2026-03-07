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

    def depends_on(self, dependencies) -> "WaitStepBuilder":
        self._step["depends_on"] = dependencies
        return self

    def continue_on_failure(self) -> "WaitStepBuilder":
        self._step["continue_on_failure"] = True
        return self

    def build(self) -> WaitStepConfiguration:
        return self._step
