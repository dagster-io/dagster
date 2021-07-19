from dagster import check
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.execution.plan.outputs import StepOutputHandle
from dagster.core.execution.plan.step import is_executable_step

from .plan.inputs import join_and_hash


def resolve_config_version(config_value):
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


def resolve_resource_versions(resolved_run_config, pipeline_definition):
    """Resolves the version of each resource provided within the ResolvedRunConfig.

    If `resolved_run_config` was constructed from the mode represented by `mode_def`, then
    `resolved_run_config` will have an entry for each resource in the mode (even if it does not
    require any configuration). For each resource, calculates a version for the run config provided
    by `resolved_run_config`, and joins with the corresponding version for the resource definition.

    Args:
        resolved_run_config (ResolvedRunConfig): Provides configuration values passed for each
            resource.
        pipeline_definition (PipelineDefinition): Definition for pipeline that configuration is
            provided for.
    Returns:
        Dict[str, Optional[str]]: dictionary where each key is a resource key, and each value is
            the resolved version of the corresponding resource.
    """

    mode = resolved_run_config.mode
    mode_definition = pipeline_definition.get_mode_definition(mode)

    resource_versions = {}

    for resource_key, resource_config in resolved_run_config.resources.items():
        resource_def_version = mode_definition.resource_defs[resource_key].version
        resource_versions[resource_key] = join_and_hash(
            resolve_config_version(resource_config.config), resource_def_version
        )

    return resource_versions


def resolve_step_versions(pipeline_def, execution_plan, resolved_run_config):
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

    resource_versions_by_key = resolve_resource_versions(resolved_run_config, pipeline_def)

    step_versions = {}  # step_key (str) -> version (str)

    for step in execution_plan.get_all_steps_in_topo_order():
        # do not compute versions for steps that are not executable
        if not is_executable_step(step):
            continue

        solid_def = pipeline_def.get_solid(step.solid_handle).definition

        input_version_dict = {
            input_name: step_input.source.compute_version(
                step_versions, pipeline_def, resolved_run_config
            )
            for input_name, step_input in step.step_input_dict.items()
        }
        for input_name, version in input_version_dict.items():
            if version is None:
                raise DagsterInvariantViolationError(
                    f"Received None version for input {input_name} to solid {solid_def.name}."
                )
        input_versions = [version for version in input_version_dict.values()]

        solid_name = str(step.solid_handle)
        solid_def_version = solid_def.version
        if solid_def_version is None:
            raise DagsterInvariantViolationError(
                f"No version argument provided for solid '{solid_def.name}' when using memoization. "
                "Please provide a version argument to the '@solid' decorator when defining your solid."
            )
        solid_config_version = resolve_config_version(resolved_run_config.solids[solid_name].config)

        resource_versions = []
        for resource_key in solid_def.required_resource_keys:
            if resource_versions_by_key[resource_key] is None:
                raise DagsterInvariantViolationError(
                    f"No version argument provided for resource '{resource_key}' when using "
                    "memoization. Please provide a version argument to the '@resource' decorator "
                    "when defining your resource."
                )
            resource_versions.append(resource_versions_by_key[resource_key])
        solid_resources_version = join_and_hash(*resource_versions)
        solid_version = join_and_hash(
            solid_def_version, solid_config_version, solid_resources_version
        )

        from_versions = input_versions + [solid_version]

        step_version = join_and_hash(*from_versions)

        step_versions[step.key] = step_version

    return step_versions


def resolve_step_output_versions(pipeline_def, execution_plan, resolved_run_config):
    step_versions = resolve_step_versions(pipeline_def, execution_plan, resolved_run_config)
    return {
        StepOutputHandle(step.key, output_name): join_and_hash(output_name, step_versions[step.key])
        for step in execution_plan.steps
        if is_executable_step(step)
        for output_name in step.step_output_dict.keys()
    }
