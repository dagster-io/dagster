from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from dagster.core.execution.context.system import SystemStepExecutionContext


def build_resources_for_manager(
    io_manager_key: str, step_context: "SystemStepExecutionContext"
) -> NamedTuple:
    required_resource_keys = step_context.mode_def.resource_defs[
        io_manager_key
    ].required_resource_keys
    return step_context.scoped_resources_builder.build(required_resource_keys)
