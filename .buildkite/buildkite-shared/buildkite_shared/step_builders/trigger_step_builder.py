from typing_extensions import Required, TypedDict


class TriggerStepConfiguration(TypedDict, closed=True, total=False):
    trigger: Required[str]
    label: Required[str]
    build: dict[str, object]
    branches: str | None
    key: str | None
    depends_on: list[str] | None
    soft_fail: bool
    # Covers the "async" (bool | None) and "if" (str | None) keys, which are
    # Python reserved words and cannot be used as class attributes. Buildkite
    # uses "async" for asynchronous trigger execution and "if" for conditional
    # step execution.
    __extra_items__: str | bool | None


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
        self._step["if"] = condition  # pyright: ignore[reportGeneralTypeIssues]
        return self

    def depends_on(self, dependencies):
        self._step["depends_on"] = dependencies
        return self

    def with_async(self, async_step: bool):
        self._step["async"] = async_step  # pyright: ignore[reportGeneralTypeIssues]
        return self

    def soft_fail(self, soft_fail: bool):
        self._step["soft_fail"] = soft_fail
        return self

    def with_branches(self, branches: list[str] | None):
        if branches:
            self._step["branches"] = " ".join(branches)
        return self

    def build(self):
        return self._step
