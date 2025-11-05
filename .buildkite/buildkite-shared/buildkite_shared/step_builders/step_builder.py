from typing import TypeAlias, TypeGuard, Union

from buildkite_shared.step_builders.block_step_builder import BlockStepConfiguration
from buildkite_shared.step_builders.command_step_builder import CommandStepConfiguration
from buildkite_shared.step_builders.group_step_builder import GroupStepConfiguration
from buildkite_shared.step_builders.trigger_step_builder import TriggerStepConfiguration
from buildkite_shared.step_builders.wait_step_builder import WaitStepConfiguration

StepConfiguration: TypeAlias = Union[
    CommandStepConfiguration,
    GroupStepConfiguration,
    TriggerStepConfiguration,
    WaitStepConfiguration,
    BlockStepConfiguration,
]

TopLevelStepConfiguration: TypeAlias = Union[CommandStepConfiguration, GroupStepConfiguration]


def is_command_step(step: StepConfiguration) -> TypeGuard[CommandStepConfiguration]:
    return isinstance(step, dict) and "commands" in step
