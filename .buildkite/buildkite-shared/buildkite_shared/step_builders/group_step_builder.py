from collections.abc import Sequence
from typing import Any, TypeAlias

from buildkite_shared.step_builders.block_step_builder import BlockStepConfiguration
from buildkite_shared.step_builders.command_step_builder import (
    BuildkiteQueue,
    CommandStepConfiguration,
)
from buildkite_shared.step_builders.input_step_builder import InputStepConfiguration
from buildkite_shared.step_builders.slug import make_label
from buildkite_shared.step_builders.trigger_step_builder import TriggerStepConfiguration
from buildkite_shared.step_builders.wait_step_builder import WaitStepConfiguration
from typing_extensions import Required, TypedDict

GroupLeafStepConfiguration: TypeAlias = (
    CommandStepConfiguration | TriggerStepConfiguration | WaitStepConfiguration
)


class GroupStepConfiguration(TypedDict, total=False):
    group: str
    label: Required[str]
    steps: Required[list[GroupLeafStepConfiguration]]
    key: str | None
    skip: str | None


class GroupStepBuilder:
    _step: GroupStepConfiguration

    def __init__(
        self,
        key: str,
        label_emojis: list[str] | None = None,
        *,
        steps: Sequence[
            CommandStepConfiguration
            | TriggerStepConfiguration
            | WaitStepConfiguration
            | BlockStepConfiguration
            | InputStepConfiguration
            | GroupStepConfiguration
        ],
        skip: str | None = None,
    ) -> None:
        emojis = list(label_emojis or [])
        if all(
            step.get("agents", {}).get("queue") == BuildkiteQueue.KUBERNETES_GKE for step in steps
        ):
            emojis = [":gcp:", *emojis]
        label = make_label(key, emojis)

        steps_list: list[Any] = list(steps)
        self._step: GroupStepConfiguration = {
            "key": key,
            "group": label,
            "label": label,
            "steps": steps_list,
        }
        if skip:
            self._step["skip"] = skip

    def build(self) -> GroupStepConfiguration:
        return self._step
