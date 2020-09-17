import hashlib

from dagster import check


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


def resolve_step_versions(speculative_execution_plan):
    """Resolves the version of each step in an execution plan.

    If an execution plan is not provided, then it is constructed from pipeline_def, run_config, and
    mode. It returns dict[str, str] where each key is a step key, and each value is the associated
    version for that step.

    Args:
        speculative_execution_plan (ExecutionPlan): Execution plan to resolve steps for.
        mode (Optional[str]): The pipeline mode in which to execute this run.
    """
    from dagster.core.execution.plan.plan import ExecutionPlan

    check.inst_param(speculative_execution_plan, "speculative_execution_plan", ExecutionPlan)
    step_versions = {}  # step_key (str) -> version (str)

    for step in speculative_execution_plan.topological_steps():
        input_version_dict = _resolve_step_input_versions(step, step_versions)
        input_versions = [version for version in input_version_dict.values()]

        solid_version = step.solid_version

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
