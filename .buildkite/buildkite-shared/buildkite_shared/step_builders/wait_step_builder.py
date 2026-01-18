from typing_extensions import TypedDict


class WaitStepConfiguration(TypedDict, total=False):
    wait: None
    key: str
    depends_on: list[str]
    continue_on_failure: bool


class WaitStepBuilder:
    _step: WaitStepConfiguration

    def __init__(self, key=None):
        self._step = {"wait": None}
        if key is not None:
            self._step["key"] = key

    def depends_on(self, dependencies):
        self._step["depends_on"] = dependencies
        return self

    def continue_on_failure(self):
        self._step["continue_on_failure"] = True
        return self

    def build(self):
        return self._step
