from typing import TypeAlias

from buildkite_shared.step_builders.command_step_builder import (
    BuildkiteQueue,
    CommandStepConfiguration,
)
from buildkite_shared.step_builders.trigger_step_builder import TriggerStepConfiguration
from buildkite_shared.step_builders.wait_step_builder import WaitStepConfiguration
from typing_extensions import Required, TypedDict

GroupLeafStepConfiguration: TypeAlias = (
    CommandStepConfiguration | TriggerStepConfiguration | WaitStepConfiguration
)


class GroupStepConfiguration(TypedDict, total=False):
    group: str
    label: str
    steps: Required[list[GroupLeafStepConfiguration]]
    key: str | None
    skip: str | None


class GroupStepBuilder:
    _step: GroupStepConfiguration

    def __init__(self, name, steps, key=None, skip=None):
        if all(step["agents"]["queue"] == BuildkiteQueue.KUBERNETES_GKE.value for step in steps):
            name = ":gcp: " + name

        self._step = {
            "group": name,
            "label": name,
            "steps": steps,
        }
        if key:
            self._step["key"] = key
        if skip:
            self._step["skip"] = skip

    def build(self):
        return self._step
