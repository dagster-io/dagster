from enum import Enum
from typing import Optional

from dagster._config import Field, Selector

_DEFAULT_CONFIG = {"after_upstream_steps": {}}


def get_step_execution_mode_config():
    return Field(
        Selector({"after_upstream_steps": {}, "after_upstream_outputs": {}}),
        default_value=_DEFAULT_CONFIG,
        description="Determines when steps will be executed in relation to their upstream dependencies.",
    )


class StepExecutionMode(Enum):
    AFTER_UPSTREAM_STEPS = "after_upstream_steps"
    AFTER_UPSTREAM_OUTPUTS = "after_upstream_outputs"

    @staticmethod
    def from_config(config_value: Optional[dict[str, dict]]) -> "StepExecutionMode":
        config_key = next(iter((config_value or _DEFAULT_CONFIG).keys()))
        return StepExecutionMode(config_key)
