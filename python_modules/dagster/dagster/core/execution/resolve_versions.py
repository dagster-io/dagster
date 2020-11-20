import hashlib

from dagster import check
from dagster.core.definitions.mode import ModeDefinition
from dagster.core.execution.plan.inputs import (
    FromConfig,
    FromDefaultValue,
    FromMultipleSources,
    FromStepOutput,
)
from dagster.core.system_config.objects import EnvironmentConfig


def _resolve_step_input_versions(step, step_versions):
    """Computes and returns the versions for each input defined for a given step.

    If an input is constructed from outputs of other steps, the input version is computed by
    sorting, concatenating, and hashing the versions of each output it is constructed from.

    If an input is constructed from externally loaded input (via run config) or a default value (no
    run config provided), the input version is the version of the provided type loader for that
    input.

    Args:
        step (ExecutionStep): The step for which to compute input versions.
        step_versions (Dict[str, Optional[str]]): Each key is a step key, and the value is the
            version of the corresponding step.

    Returns:
        Dict[str, Optional[str]]: A dictionary that maps the names of the inputs to the provided
            step to their computed versions.
    """

    def _resolve_output_version(step_output_handle):
        """Returns version of step output.

        Step output version is computed by sorting, concatenating, and hashing together the version
        of the step corresponding to the provided step output handle and the name of the output.
        """
        if (
            step_output_handle.step_key not in step_versions
            or not step_versions[step_output_handle.step_key]
        ):
            return None
        else:
            return join_and_hash(
                step_versions[step_output_handle.step_key], step_output_handle.output_name
            )

    def _resolve_source_version(input_source, dagster_type):
        if isinstance(input_source, FromMultipleSources):
            return join_and_hash(
                *[
                    _resolve_source_version(inner_source, dagster_type.get_inner_type_for_fan_in(),)
                    for inner_source in input_source.sources
                ]
            )
        elif isinstance(input_source, FromStepOutput):
            return _resolve_output_version(input_source.step_output_handle)
        elif isinstance(input_source, FromConfig):
            return dagster_type.loader.compute_loaded_input_version(input_source.config_data)
        elif isinstance(input_source, FromDefaultValue):
            return join_and_hash(repr(input_source.value))
        else:
            check.failed(
                "Unhandled step input source type for version calculation: {}".format(input_source)
            )

    input_versions = {}
    for input_name, step_input in step.step_input_dict.items():
        input_versions[input_name] = _resolve_source_version(
            step_input.source, step_input.dagster_type,
        )

    return input_versions


def resolve_resource_versions(environment_config, mode_def):
    """Resolves the version of each resource provided within the EnvironmentConfig.

    If `environment_config` was constructed from the mode represented by `mode_def`, then
    `environment_config` will have an entry for each resource in the mode (even if it does not
    require any configuration). For each resource, calculates a version for the run config provided
    by `environment_config`, and joins with the corresponding version for the resource definition.

    Args:
        environment_config (EnvironmentConfig): Environment configuration which contains resource
            config for each resource in the provided mode.
        mode_def (ModeDefinition): Definition for the mode for which we want to resolve versions.
    Returns:
        Dict[str, Optional[str]]: dictionary where each key is a resource key, and each value is the
            resolved version of the corresponding resource.
    """
    environment_config = check.inst_param(
        environment_config, "environment_config", EnvironmentConfig
    )
    mode_def = check.inst_param(mode_def, "mode_def", ModeDefinition)

    assert set(environment_config.resources.keys()) == set(
        mode_def.resource_defs.keys()
    )  # verify that environment config and mode_def refer to the same resources

    resource_versions = {}

    for resource_key, config in environment_config.resources.items():
        resource_def_version = mode_def.resource_defs[resource_key].version
        resource_versions[resource_key] = join_and_hash(
            resolve_config_version(config), resource_def_version
        )

    return resource_versions


def resolve_step_versions(execution_plan, environment_config, mode_def):
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

    Args:
        execution_plan (ExecutionPlan): Execution plan to resolve steps for.
        environment_config (EnvironmentConfig): Parsed Configuration for current execution
        mode_def (ModeDefinition): The Mode of the current execution

    Returns:
        Dict[str, Optional[str]]: A dictionary that maps the key of an execution step to a version.
            If a step has no computed version, then the step key maps to None.
    """

    from dagster.core.execution.plan.plan import ExecutionPlan

    check.inst_param(execution_plan, "execution_plan", ExecutionPlan)
    check.inst_param(environment_config, "environment_config", EnvironmentConfig)
    check.inst_param(mode_def, "mode_def", ModeDefinition)

    resource_versions_by_key = resolve_resource_versions(environment_config, mode_def)

    step_versions = {}  # step_key (str) -> version (str)

    for step in execution_plan.topological_steps():
        input_version_dict = _resolve_step_input_versions(step, step_versions)
        input_versions = [version for version in input_version_dict.values()]

        solid_name = str(step.solid_handle)
        solid_def_version = step.solid.definition.version
        solid_config_version = resolve_config_version(environment_config.solids[solid_name].config)
        hashed_resources = [
            resource_versions_by_key[resource_key]
            for resource_key in step.solid.definition.required_resource_keys
        ]
        solid_resources_version = join_and_hash(*hashed_resources)
        solid_version = join_and_hash(
            solid_def_version, solid_config_version, solid_resources_version
        )

        from_versions = input_versions + [solid_version]

        step_version = join_and_hash(*from_versions)

        step_versions[step.key] = step_version

    return step_versions


def resolve_step_output_versions(execution_plan, environment_config, mode_def):
    from dagster.core.execution.plan.plan import ExecutionPlan
    from dagster.core.execution.plan.objects import StepOutputHandle

    check.inst_param(execution_plan, "execution_plan", ExecutionPlan)
    check.inst_param(environment_config, "environment_config", EnvironmentConfig)
    check.inst_param(mode_def, "mode_def", ModeDefinition)

    step_versions = resolve_step_versions(execution_plan, environment_config, mode_def)
    return {
        StepOutputHandle(step.key, output_name): join_and_hash(output_name, step_versions[step.key])
        for step in execution_plan.steps
        for output_name in step.step_output_dict.keys()
    }


def join_and_hash(*args):
    lst = [check.opt_str_param(elem, "elem") for elem in args]
    if None in lst:
        return None
    else:
        unhashed = "".join(sorted(lst))
        return hashlib.sha1(unhashed.encode("utf-8")).hexdigest()


def resolve_config_version(config_value):
    """Resolve a configuration value into a hashed version.

    If a single value is passed in, it is converted to a string, hashed, and returned as the
    version. If a dictionary of config values is passed in, each value is resolved to a version,
    concatenated with its key, joined, and hashed into a single version.

    Args:
        config_value (Union[Any, dict]): Either a single config value or a dictionary of config
            values.
    """
    if not isinstance(config_value, dict):
        return join_and_hash(str(config_value))
    else:
        config_value = check.dict_param(config_value, "config_value")
        return join_and_hash(
            *[key + resolve_config_version(val) for key, val in config_value.items()]
        )
