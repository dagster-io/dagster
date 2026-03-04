from typing import TypeAlias, TypeGuard

from buildkite_shared.step_builders.block_step_builder import BlockStepConfiguration
from buildkite_shared.step_builders.command_step_builder import CommandStepConfiguration
from buildkite_shared.step_builders.group_step_builder import GroupStepConfiguration
from buildkite_shared.step_builders.trigger_step_builder import TriggerStepConfiguration
from buildkite_shared.step_builders.wait_step_builder import WaitStepConfiguration

StepConfiguration: TypeAlias = (
    CommandStepConfiguration
    | GroupStepConfiguration
    | TriggerStepConfiguration
    | WaitStepConfiguration
    | BlockStepConfiguration
)

TopLevelStepConfiguration: TypeAlias = CommandStepConfiguration | GroupStepConfiguration


def is_command_step(step: StepConfiguration) -> TypeGuard[CommandStepConfiguration]:
    return isinstance(step, dict) and "commands" in step


def is_group_step(step: StepConfiguration) -> TypeGuard[GroupStepConfiguration]:
    return isinstance(step, dict) and "group" in step and "steps" in step


def is_wait_step(step: StepConfiguration) -> TypeGuard[WaitStepConfiguration]:
    return isinstance(step, dict) and "wait" in step


def is_block_step(step: StepConfiguration) -> TypeGuard[BlockStepConfiguration]:
    return isinstance(step, dict) and "block" in step


def is_trigger_step(step: StepConfiguration) -> TypeGuard[TriggerStepConfiguration]:
    return isinstance(step, dict) and "trigger" in step
