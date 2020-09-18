import hashlib

from dagster import check
from dagster.core.definitions.mode import ModeDefinition
from dagster.core.system_config.objects import EnvironmentConfig


def _resolve_step_input_versions(step, step_versions):
    def _resolve_output_version(step_output_handle):
        if (
            step_output_handle.step_key not in step_versions
            or not step_versions[step_output_handle.step_key]
        ):
            return None
        else:
            return join_and_hash(
                [step_versions[step_output_handle.step_key], step_output_handle.output_name]
            )

    input_versions = {}
    for input_name, step_input in step.step_input_dict.items():
        if step_input.is_from_output:
            output_handle_versions = [
                _resolve_output_version(source_handle)
                for source_handle in step_input.source_handles
            ]
            version = join_and_hash(output_handle_versions)
        elif step_input.is_from_config:
            version = step_input.dagster_type.loader.compute_loaded_input_version(
                step_input.config_data
            )
        input_versions[input_name] = version

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
            [resolve_config_version(config), resource_def_version]
        )

    return resource_versions


def resolve_step_versions(speculative_execution_plan, mode=None, run_config=None):
    """Resolves the version of each step in an execution plan.

    Execution plan provides execution steps for analysis. It returns dict[str, str] where each key
    is a step key, and each value is the associated version for that step.

    Args:
        speculative_execution_plan (ExecutionPlan): Execution plan to resolve steps for.
        mode (Optional[str]): The pipeline mode in which to execute this run.
        run_config (Optional[dict]): The config value to use for this pipeline.
    """
    from dagster.core.execution.plan.plan import ExecutionPlan

    check.inst_param(speculative_execution_plan, "speculative_execution_plan", ExecutionPlan)
    check.opt_str_param(mode, "mode")
    check.opt_dict_param(run_config, "run_config", key_type=str)

    environment_config = EnvironmentConfig.build(
        speculative_execution_plan.pipeline_def, run_config, mode
    )  # environment_config.resources guaranteed to have an entry for each resource in mode,
    # environment_config.solids guaranteed to have an entry for each solid in pipeline.

    mode_def = speculative_execution_plan.pipeline_def.get_mode_definition(mode)

    resource_versions_by_key = resolve_resource_versions(environment_config, mode_def)

    step_versions = {}  # step_key (str) -> version (str)

    for step in speculative_execution_plan.topological_steps():
        input_version_dict = _resolve_step_input_versions(step, step_versions)
        input_versions = [version for version in input_version_dict.values()]

        solid_name = step.solid_handle.name
        solid_def_version = step.solid_version
        solid_config_version = resolve_config_version(environment_config.solids[solid_name].config)
        hashed_resources = [
            resource_versions_by_key[resource_key]
            for resource_key in step.solid_required_resource_keys
        ]
        solid_resources_version = join_and_hash(hashed_resources)
        solid_version = join_and_hash(
            [solid_def_version, solid_config_version, solid_resources_version]
        )

        from_versions = input_versions + [solid_version]

        step_version = join_and_hash(from_versions)

        step_versions[step.key] = step_version

    return step_versions


def join_and_hash(lst):
    lst = check.list_param(lst, "lst")
    lst = [check.opt_str_param(elem, "elem") for elem in lst]
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
        return join_and_hash([str(config_value)])
    else:
        config_value = check.dict_param(config_value, "config_value")
        return join_and_hash(
            [key + resolve_config_version(val) for key, val in config_value.items()]
        )
