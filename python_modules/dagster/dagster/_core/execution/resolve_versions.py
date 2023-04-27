import re
from typing import TYPE_CHECKING, Dict, Mapping, Optional

import dagster._check as check
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.version_strategy import OpVersionContext, ResourceVersionContext
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.execution.plan.outputs import StepOutputHandle
from dagster._core.execution.plan.step import is_executable_step
from dagster._core.system_config.objects import ResolvedRunConfig

from .plan.inputs import join_and_hash

if TYPE_CHECKING:
    from dagster._core.execution.plan.plan import ExecutionPlan

VALID_VERSION_REGEX_STR = r"^[A-Za-z0-9_]+$"
VALID_VERSION_REGEX = re.compile(VALID_VERSION_REGEX_STR)


def check_valid_version(version: str) -> None:
    is_valid = bool(VALID_VERSION_REGEX.match(version))
    if not is_valid:
        raise DagsterInvariantViolationError(
            f"'{version}' is not a valid version string. Version must be in regex "
            f"{VALID_VERSION_REGEX_STR}."
        )


def resolve_config_version(config_value: object):
    """Resolve a configuration value into a hashed version.

    If a None value is passed in, we return the result of an empty join_and_hash.
    If a single value is passed in, it is converted to a string, hashed, and returned as the
    version. If a dictionary of config values is passed in, each value is resolved to a version,
    concatenated with its key, joined, and hashed into a single version.

    Args:
        config_value (Union[Any, dict]): Either a single config value or a dictionary of config
            values.
    """
    if config_value is None:
        return join_and_hash()
    if not isinstance(config_value, dict):
        return join_and_hash(str(config_value))
    else:
        config_value = check.dict_param(config_value, "config_value")
        return join_and_hash(
            *[key + resolve_config_version(val) for key, val in config_value.items()]
        )


def resolve_step_versions(
    pipeline_def: JobDefinition,
    execution_plan: "ExecutionPlan",
    resolved_run_config: ResolvedRunConfig,
) -> Mapping[str, Optional[str]]:
    """Resolves the version of each step in an execution plan.

    Execution plan provides execution steps for analysis. It returns dict[str, str] where each key
    is a step key, and each value is the associated version for that step.

    The version for a step combines the versions of all inputs to the step, and the version of the
    solid that the step contains. The inputs consist of all input definitions provided to the step.
    The process for computing the step version is as follows:
        1.  Compute the version for each input to the step.
        2.  Compute the version of the solid provided to the step.
        3.  Sort, concatenate and hash the input and solid versions.

    The solid version combines the version of the solid definition, the versions of the required
    resources, and the version of the config provided to the solid.
    The process for computing the solid version is as follows:
        1.  Sort, concatenate and hash the versions of the required resources.
        2.  Resolve the version of the configuration provided to the solid.
        3.  Sort, concatenate and hash together the concatted resource versions, the config version,
                and the solid's version definition.

    Returns:
        Dict[str, Optional[str]]: A dictionary that maps the key of an execution step to a version.
            If a step has no computed version, then the step key maps to None.
    """
    resource_versions = {}
    resource_defs = pipeline_def.resource_defs

    step_versions: Dict[str, Optional[str]] = {}  # step_key (str) -> version (str)

    for step in execution_plan.get_all_steps_in_topo_order():
        # do not compute versions for steps that are not executable
        if not is_executable_step(step):  # type: ignore
            continue

        solid_def = pipeline_def.get_node(step.node_handle).definition

        input_version_dict = {
            input_name: step_input.source.compute_version(
                step_versions, pipeline_def, resolved_run_config
            )
            for input_name, step_input in step.step_input_dict.items()
        }
        node_label = f"{solid_def.node_type_str} '{solid_def.name}'"
        for input_name, version in input_version_dict.items():
            if version is None:
                raise DagsterInvariantViolationError(
                    f"Received None version for input {input_name} to {node_label}."
                )
        input_versions = [version for version in input_version_dict.values()]

        solid_name = str(step.node_handle)

        solid_config = resolved_run_config.ops[solid_name].config

        solid_def_version = None
        if solid_def.version is not None:  # type: ignore  # (should be OpDefinition)
            solid_def_version = solid_def.version  # type: ignore  # (should be OpDefinition)
        elif pipeline_def.version_strategy is not None:
            version_context = OpVersionContext(op_def=solid_def, op_config=solid_config)  # type: ignore  # (should be OpDefinition)
            solid_def_version = pipeline_def.version_strategy.get_op_version(version_context)

        if solid_def_version is None:
            raise DagsterInvariantViolationError(
                f"While using memoization, version for {node_label} was None. Please "
                "either provide a versioning strategy for your job, or provide a version using the "
                f"{solid_def.node_type_str} decorator."
            )

        check_valid_version(solid_def_version)

        solid_config_version = resolve_config_version(solid_config)

        resource_versions_for_solid = []
        for resource_key in solid_def.required_resource_keys:  # type: ignore  # (should be OpDefinition)
            if resource_key not in resource_versions:
                resource_config = resolved_run_config.resources[resource_key].config
                resource_config_version = resolve_config_version(resource_config)

                resource_def = resource_defs[resource_key]
                resource_def_version = None
                if resource_def.version is not None:
                    resource_def_version = resource_def.version
                else:
                    resource_version_context = ResourceVersionContext(
                        resource_def=resource_def, resource_config=resource_config
                    )
                    resource_def_version = check.not_none(
                        pipeline_def.version_strategy
                    ).get_resource_version(resource_version_context)

                if resource_def_version is not None:
                    check_valid_version(resource_def_version)
                    resource_versions[resource_key] = join_and_hash(
                        resource_config_version, resource_def_version
                    )
                else:
                    resource_versions[resource_key] = join_and_hash(resource_config)

            if resource_versions[resource_key] is not None:
                resource_versions_for_solid.append(resource_versions[resource_key])
        solid_resources_version = join_and_hash(*resource_versions_for_solid)
        solid_version = join_and_hash(
            solid_def_version, solid_config_version, solid_resources_version
        )

        from_versions = input_versions + [solid_version]

        step_version = join_and_hash(*from_versions)

        step_versions[step.key] = step_version

    return step_versions


def resolve_step_output_versions(
    pipeline_def: JobDefinition,
    execution_plan: "ExecutionPlan",
    resolved_run_config: ResolvedRunConfig,
):
    step_versions = resolve_step_versions(pipeline_def, execution_plan, resolved_run_config)
    return {
        StepOutputHandle(step.key, output_name): join_and_hash(output_name, step_versions[step.key])
        for step in execution_plan.steps
        if is_executable_step(step)  # type: ignore
        for output_name in step.step_output_dict.keys()
    }
