from collections.abc import Sequence
from typing import Self

from buildkite_shared.step_builders.slug import make_label
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

    def __init__(self, key: str, pipeline: str, label_emojis: list[str] | None = None) -> None:
        self._step: TriggerStepConfiguration = {
            "key": key,
            "trigger": pipeline,
            "label": make_label(key, label_emojis),
        }

    def with_build_params(self, build_params: dict[str, object]) -> Self:
        self._step["build"] = build_params
        return self

    def with_condition(self, condition: str) -> Self:
        self._step["if"] = condition  # pyright: ignore[reportGeneralTypeIssues]
        return self

    def depends_on(self, dependencies: str | Sequence[str]) -> Self:
        self._step["depends_on"] = (
            [dependencies] if isinstance(dependencies, str) else list(dependencies)
        )
        return self

    def with_async(self, async_step: bool) -> Self:
        self._step["async"] = async_step  # pyright: ignore[reportGeneralTypeIssues]
        return self

    def soft_fail(self, soft_fail: bool) -> Self:
        self._step["soft_fail"] = soft_fail
        return self

    def with_branches(self, branches: list[str] | None) -> Self:
        if branches:
            self._step["branches"] = " ".join(branches)
        return self

    def build(self) -> TriggerStepConfiguration:
        return self._step
