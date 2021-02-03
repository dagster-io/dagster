from dagster import check
from dagster.core.execution.context.init import InitResourceContext
from dagster.core.execution.context.system import get_output_context
from dagster.core.execution.plan.outputs import StepOutputHandle
from dagster.core.execution.plan.step import is_executable_step
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.utils.backcompat import experimental

from .plan.inputs import join_and_hash


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


def resolve_resource_versions(environment_config, pipeline_definition):
    """Resolves the version of each resource provided within the EnvironmentConfig.

    If `environment_config` was constructed from the mode represented by `mode_def`, then
    `environment_config` will have an entry for each resource in the mode (even if it does not
    require any configuration). For each resource, calculates a version for the run config provided
    by `environment_config`, and joins with the corresponding version for the resource definition.

    Args:
        environment_config (EnvironmentConfig): Provides configuration values passed for each
            resource.
        pipeline_definition (PipelineDefinition): Definition for pipeline that configuration is
            provided for.
    Returns:
        Dict[str, Optional[str]]: dictionary where each key is a resource key, and each value is
            the resolved version of the corresponding resource.
    """

    mode = environment_config.mode
    mode_definition = pipeline_definition.get_mode_definition(mode)
    check.invariant(
        set(environment_config.resources.keys()) == set(mode_definition.resource_defs.keys())
    )  # verify that environment config and mode_def refer to the same resources

    resource_versions = {}

    for resource_key, config in environment_config.resources.items():
        resource_def_version = mode_definition.resource_defs[resource_key].version
        resource_versions[resource_key] = join_and_hash(
            resolve_config_version(config), resource_def_version
        )

    return resource_versions


def resolve_step_versions_helper(execution_plan):
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

    pipeline_def = execution_plan.pipeline.get_definition()

    resource_versions_by_key = resolve_resource_versions(
        execution_plan.environment_config,
        pipeline_def,
    )

    step_versions = {}  # step_key (str) -> version (str)

    for step in execution_plan.get_all_steps_in_topo_order():
        # do not compute versions for steps that are not executable
        if not is_executable_step(step):
            continue

        solid_def = pipeline_def.get_solid(step.solid_handle).definition

        input_version_dict = {
            input_name: step_input.source.compute_version(
                step_versions, pipeline_def, execution_plan.environment_config
            )
            for input_name, step_input in step.step_input_dict.items()
        }
        input_versions = [version for version in input_version_dict.values()]

        solid_name = str(step.solid_handle)
        solid_def_version = solid_def.version
        solid_config_version = resolve_config_version(
            execution_plan.environment_config.solids[solid_name].config
        )
        hashed_resources = [
            resource_versions_by_key[resource_key]
            for resource_key in solid_def.required_resource_keys
        ]
        solid_resources_version = join_and_hash(*hashed_resources)
        solid_version = join_and_hash(
            solid_def_version, solid_config_version, solid_resources_version
        )

        from_versions = input_versions + [solid_version]

        step_version = join_and_hash(*from_versions)

        step_versions[step.key] = step_version

    return step_versions


def resolve_step_output_versions_helper(execution_plan):

    step_versions = execution_plan.resolve_step_versions()
    return {
        StepOutputHandle(step.key, output_name): join_and_hash(output_name, step_versions[step.key])
        for step in execution_plan.steps
        if is_executable_step(step)
        for output_name in step.step_output_dict.keys()
    }


@experimental
def resolve_memoized_execution_plan(execution_plan):
    """
    Returns:
        ExecutionPlan: Execution plan configured to only run unmemoized steps.
    """

    pipeline_def = execution_plan.pipeline.get_definition()

    environment_config = execution_plan.environment_config
    pipeline_def = execution_plan.pipeline.get_definition()
    mode_def = pipeline_def.get_mode_definition(environment_config.mode)

    step_keys_to_execute = set()

    for step in execution_plan.steps:
        for output_name in step.step_output_dict.keys():
            step_output_handle = StepOutputHandle(step.key, output_name)

            io_manager_key = execution_plan.get_manager_key(step_output_handle)
            # TODO: https://github.com/dagster-io/dagster/issues/3302
            # The following code block is HIGHLY experimental. It initializes an IO manager
            # outside of the resource initialization context, and will ignore any exit hooks defined
            # for the IO manager, and will not work if the IO manager requires resource keys
            # for initialization.
            resource_config = (
                environment_config.resources[io_manager_key]["config"]
                if "config" in environment_config.resources[io_manager_key]
                else {}
            )
            resource_def = mode_def.resource_defs[io_manager_key]
            resource_context = InitResourceContext(
                resource_config,
                resource_def,
                pipeline_run=PipelineRun(
                    pipeline_name=pipeline_def.name, run_id="", mode=environment_config.mode
                ),
            )
            io_manager = resource_def.resource_fn(resource_context)
            context = get_output_context(
                execution_plan, environment_config, step_output_handle, None
            )
            if not io_manager.has_output(context):
                step_keys_to_execute.add(step_output_handle.step_key)

    return execution_plan.build_subset_plan(list(step_keys_to_execute))
