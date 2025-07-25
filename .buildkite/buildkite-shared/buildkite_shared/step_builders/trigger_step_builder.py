from typing import Optional, TypedDict

# use alt syntax because of `async` and `if` reserved words
TriggerStepConfiguration = TypedDict(
    "TriggerStepConfiguration",
    {
        "trigger": str,
        "label": str,
        "async": Optional[bool],
        "build": dict[str, object],
        "branches": Optional[str],
        "if": Optional[str],
        "key": Optional[str],
        "depends_on": Optional[list[str]],
        "soft_fail": bool,
    },
    total=False,
)


class TriggerStepBuilder:
    _step: TriggerStepConfiguration

    def __init__(self, label, pipeline, key=None):
        self._step = {"trigger": pipeline, "label": label}

        if key is not None:
            self._step["key"] = key

    def with_build_params(self, build_params):
        self._step["build"] = build_params
        return self

    def with_condition(self, condition):
        self._step["if"] = condition
        return self

    def depends_on(self, dependencies):
        self._step["depends_on"] = dependencies
        return self

    def with_async(self, async_step: bool):
        self._step["async"] = async_step
        return self

    def soft_fail(self, soft_fail: bool):
        self._step["soft_fail"] = soft_fail
        return self

    def with_branches(self, branches: Optional[list[str]]):
        if branches:
            self._step["branches"] = " ".join(branches)
        return self

    def build(self):
        return self._step
