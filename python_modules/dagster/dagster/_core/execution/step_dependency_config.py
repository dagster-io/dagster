from typing import Optional

from dagster_shared.record import record

from dagster._config import Field, Shape


def get_step_dependency_config_field():
    return Field(
        Shape(
            {"require_upstream_step_success": Field(bool, default_value=True)},
        ),
        is_required=False,
        description="Determines when steps will be executed in relation to their upstream dependencies.",
    )


@record
class StepDependencyConfig:
    require_upstream_step_success: bool

    @staticmethod
    def default() -> "StepDependencyConfig":
        return StepDependencyConfig(require_upstream_step_success=True)

    @staticmethod
    def from_config(config_value: Optional[dict[str, bool]]) -> "StepDependencyConfig":
        return StepDependencyConfig(
            require_upstream_step_success=config_value["require_upstream_step_success"]
            if config_value
            else True,
        )
