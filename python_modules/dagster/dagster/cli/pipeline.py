import os
import re
import sys
import textwrap

import click
import pendulum
import yaml
from dagster import PipelineDefinition, check, execute_pipeline
from dagster.cli.workspace.cli_target import (
    WORKSPACE_TARGET_WARNING,
    get_external_pipeline_from_external_repo,
    get_external_pipeline_from_kwargs,
    get_external_repository_from_kwargs,
    get_external_repository_from_repo_location,
    get_pipeline_python_origin_from_kwargs,
    get_repository_location_from_kwargs,
    pipeline_target_argument,
    python_pipeline_config_argument,
    python_pipeline_target_argument,
    repository_target_argument,
)
from dagster.core.definitions.pipeline_base import IPipeline
from dagster.core.errors import (
    DagsterBackfillFailedError,
    DagsterInvariantViolationError,
    DagsterLaunchFailedError,
)
from dagster.core.execution.api import create_execution_plan
from dagster.core.execution.backfill import BulkActionStatus, PartitionBackfill, create_backfill_run
from dagster.core.execution.resolve_versions import resolve_memoized_execution_plan
from dagster.core.host_representation import (
    ExternalPipeline,
    ExternalRepository,
    RepositoryHandle,
    RepositoryLocation,
)
from dagster.core.host_representation.external_data import (
    ExternalPartitionExecutionErrorData,
    ExternalPartitionSetExecutionParamData,
)
from dagster.core.host_representation.selector import PipelineSelector
from dagster.core.instance import DagsterInstance
from dagster.core.snap import PipelineSnapshot, SolidInvocationSnap
from dagster.core.snap.execution_plan_snapshot import ExecutionPlanSnapshotErrorData
from dagster.core.telemetry import log_external_repo_stats, telemetry_wrapper
from dagster.core.utils import make_new_backfill_id
from dagster.seven import IS_WINDOWS, JSONDecodeError, json
from dagster.utils import DEFAULT_WORKSPACE_YAML_FILENAME, load_yaml_from_glob_list, merge_dicts
from dagster.utils.error import serializable_error_info_from_exc_info
from dagster.utils.hosted_user_process import recon_pipeline_from_origin
from dagster.utils.indenting_printer import IndentingPrinter
from dagster.utils.interrupts import capture_interrupts
from tabulate import tabulate

from .config_scaffolder import scaffold_pipeline_config


def create_pipeline_cli_group():
    group = click.Group(name="pipeline")
    group.add_command(pipeline_list_command)
    group.add_command(pipeline_print_command)
    group.add_command(pipeline_execute_command)
    group.add_command(pipeline_backfill_command)
    group.add_command(pipeline_scaffold_command)
    group.add_command(pipeline_launch_command)
    group.add_command(pipeline_list_versions_command)
    return group


def apply_click_params(command, *click_params):
    for click_param in click_params:
        command = click_param(command)
    return command


@click.command(
    name="list",
    help="List the pipelines in a repository. {warning}".format(warning=WORKSPACE_TARGET_WARNING),
)
@repository_target_argument
def pipeline_list_command(**kwargs):
    with DagsterInstance.get() as instance:
        return execute_list_command(kwargs, click.echo, instance)


def execute_list_command(cli_args, print_fn, instance):
    check.inst_param(instance, "instance", DagsterInstance)
    with get_external_repository_from_kwargs(cli_args) as external_repository:
        title = "Repository {name}".format(name=external_repository.name)
        print_fn(title)
        print_fn("*" * len(title))
        first = True
        for pipeline in external_repository.get_all_external_pipelines():
            pipeline_title = "Pipeline: {name}".format(name=pipeline.name)

            if not first:
                print_fn("*" * len(pipeline_title))
            first = False

            print_fn(pipeline_title)
            if pipeline.description:
                print_fn("Description:")
                print_fn(format_description(pipeline.description, indent=" " * 4))
            print_fn("Solids: (Execution Order)")
            for solid_name in pipeline.pipeline_snapshot.solid_names_in_topological_order:
                print_fn("    " + solid_name)


def format_description(desc, indent):
    check.str_param(desc, "desc")
    check.str_param(indent, "indent")
    desc = re.sub(r"\s+", " ", desc)
    dedented = textwrap.dedent(desc)
    wrapper = textwrap.TextWrapper(initial_indent="", subsequent_indent=indent)
    filled = wrapper.fill(dedented)
    return filled


def get_pipeline_in_same_python_env_instructions(command_name):
    return (
        "This commands targets a pipeline. The pipeline can be specified in a number of ways:"
        "\n\n1. dagster pipeline {command_name} -f /path/to/file.py -a define_some_pipeline"
        "\n\n2. dagster pipeline {command_name} -m a_module.submodule -a define_some_pipeline"
        "\n\n3. dagster pipeline {command_name} -f /path/to/file.py -a define_some_repo -p <<pipeline_name>>"
        "\n\n4. dagster pipeline {command_name} -m a_module.submodule -a define_some_repo -p <<pipeline_name>>"
    ).format(command_name=command_name)


def get_pipeline_instructions(command_name):
    return (
        "This commands targets a pipeline. The pipeline can be specified in a number of ways:"
        "\n\n1. dagster pipeline {command_name} -p <<pipeline_name>> (works if .{default_filename} exists)"
        "\n\n2. dagster pipeline {command_name} -p <<pipeline_name>> -w path/to/{default_filename}"
        "\n\n3. dagster pipeline {command_name} -f /path/to/file.py -a define_some_pipeline"
        "\n\n4. dagster pipeline {command_name} -m a_module.submodule -a define_some_pipeline"
        "\n\n5. dagster pipeline {command_name} -f /path/to/file.py -a define_some_repo -p <<pipeline_name>>"
        "\n\n6. dagster pipeline {command_name} -m a_module.submodule -a define_some_repo -p <<pipeline_name>>"
    ).format(command_name=command_name, default_filename=DEFAULT_WORKSPACE_YAML_FILENAME)


def get_partitioned_pipeline_instructions(command_name):
    return (
        "This commands targets a partitioned pipeline. The pipeline and partition set must be "
        "defined in a repository, which can be specified in a number of ways:"
        "\n\n1. dagster pipeline {command_name} -p <<pipeline_name>> (works if .{default_filename} exists)"
        "\n\n2. dagster pipeline {command_name} -p <<pipeline_name>> -w path/to/{default_filename}"
        "\n\n3. dagster pipeline {command_name} -f /path/to/file.py -a define_some_repo -p <<pipeline_name>>"
        "\n\n4. dagster pipeline {command_name} -m a_module.submodule -a define_some_repo -p <<pipeline_name>>"
    ).format(command_name=command_name, default_filename=DEFAULT_WORKSPACE_YAML_FILENAME)


@click.command(
    name="print",
    help="Print a pipeline.\n\n{instructions}".format(
        instructions=get_pipeline_instructions("print")
    ),
)
@click.option("--verbose", is_flag=True)
@pipeline_target_argument
def pipeline_print_command(verbose, **cli_args):
    with DagsterInstance.get():
        return execute_print_command(verbose, cli_args, click.echo)


def execute_print_command(verbose, cli_args, print_fn):
    with get_external_pipeline_from_kwargs(cli_args) as external_pipeline:
        pipeline_snapshot = external_pipeline.pipeline_snapshot

        if verbose:
            print_pipeline(pipeline_snapshot, print_fn=print_fn)
        else:
            print_solids(pipeline_snapshot, print_fn=print_fn)


def print_solids(pipeline_snapshot, print_fn):
    check.inst_param(pipeline_snapshot, "pipeline", PipelineSnapshot)
    check.callable_param(print_fn, "print_fn")

    printer = IndentingPrinter(indent_level=2, printer=print_fn)
    printer.line("Pipeline: {name}".format(name=pipeline_snapshot.name))

    printer.line("Solids:")
    for solid in pipeline_snapshot.dep_structure_snapshot.solid_invocation_snaps:
        with printer.with_indent():
            printer.line("Solid: {name}".format(name=solid.solid_name))


def print_pipeline(pipeline_snapshot, print_fn):
    check.inst_param(pipeline_snapshot, "pipeline", PipelineSnapshot)
    check.callable_param(print_fn, "print_fn")
    printer = IndentingPrinter(indent_level=2, printer=print_fn)
    printer.line("Pipeline: {name}".format(name=pipeline_snapshot.name))
    print_description(printer, pipeline_snapshot.description)

    printer.line("Solids:")
    for solid in pipeline_snapshot.dep_structure_snapshot.solid_invocation_snaps:
        with printer.with_indent():
            print_solid(printer, pipeline_snapshot, solid)


def print_description(printer, desc):
    with printer.with_indent():
        if desc:
            printer.line("Description:")
            with printer.with_indent():
                printer.line(format_description(desc, printer.current_indent_str))


def print_solid(printer, pipeline_snapshot, solid_invocation_snap):
    check.inst_param(pipeline_snapshot, "pipeline_snapshot", PipelineSnapshot)
    check.inst_param(solid_invocation_snap, "solid_invocation_snap", SolidInvocationSnap)
    printer.line("Solid: {name}".format(name=solid_invocation_snap.solid_name))
    with printer.with_indent():
        printer.line("Inputs:")
        for input_dep_snap in solid_invocation_snap.input_dep_snaps:
            with printer.with_indent():
                printer.line("Input: {name}".format(name=input_dep_snap.input_name))

        printer.line("Outputs:")
        for output_def_snap in pipeline_snapshot.get_solid_def_snap(
            solid_invocation_snap.solid_def_name
        ).output_def_snaps:
            printer.line(output_def_snap.name)


@click.command(
    name="list_versions",
    help="Display the freshness of memoized results for the given pipeline.\n\n{instructions}".format(
        instructions=get_pipeline_in_same_python_env_instructions("list_versions")
    ),
)
@python_pipeline_target_argument
@python_pipeline_config_argument("list_versions")
@click.option(
    "--preset",
    type=click.STRING,
    help="Specify a preset to use for this pipeline. Presets are defined on pipelines under "
    "preset_defs.",
)
@click.option(
    "--mode", type=click.STRING, help="The name of the mode in which to execute the pipeline."
)
def pipeline_list_versions_command(**kwargs):
    with DagsterInstance.get() as instance:
        execute_list_versions_command(instance, kwargs)


def execute_list_versions_command(instance, kwargs):
    check.inst_param(instance, "instance", DagsterInstance)

    config = list(check.opt_tuple_param(kwargs.get("config"), "config", default=(), of_type=str))
    preset = kwargs.get("preset")
    mode = kwargs.get("mode")

    if preset and config:
        raise click.UsageError("Can not use --preset with --config.")

    pipeline_origin = get_pipeline_python_origin_from_kwargs(kwargs)
    pipeline = recon_pipeline_from_origin(pipeline_origin)
    run_config = get_run_config_from_file_list(config)
    execution_plan = create_execution_plan(
        pipeline.get_definition(), run_config=run_config, mode=mode
    )
    step_output_versions = execution_plan.resolve_step_output_versions()
    memoized_plan = resolve_memoized_execution_plan(execution_plan)
    # the step keys that we need to execute are those which do not have their inputs populated.
    step_keys_not_stored = set(memoized_plan.step_keys_to_execute)
    table = []
    for step_output_handle, version in step_output_versions.items():
        table.append(
            [
                "{key}.{output}".format(
                    key=step_output_handle.step_key, output=step_output_handle.output_name
                ),
                version,
                "stored"
                if step_output_handle.step_key not in step_keys_not_stored
                else "to-be-recomputed",
            ]
        )
    table_str = tabulate(
        table, headers=["Step Output", "Version", "Status of Output"], tablefmt="github"
    )
    click.echo(table_str)


@click.command(
    name="execute",
    help="Execute a pipeline.\n\n{instructions}".format(
        instructions=get_pipeline_in_same_python_env_instructions("execute")
    ),
)
@python_pipeline_target_argument
@python_pipeline_config_argument("execute")
@click.option(
    "--preset",
    type=click.STRING,
    help="Specify a preset to use for this pipeline. Presets are defined on pipelines under "
    "preset_defs.",
)
@click.option(
    "--mode", type=click.STRING, help="The name of the mode in which to execute the pipeline."
)
@click.option("--tags", type=click.STRING, help="JSON string of tags to use for this pipeline run")
@click.option(
    "-s",
    "--solid-selection",
    type=click.STRING,
    help=(
        "Specify the solid subselection to execute. It can be multiple clauses separated by commas."
        "Examples:"
        '\n- "some_solid" will execute "some_solid" itself'
        '\n- "*some_solid" will execute "some_solid" and all its ancestors (upstream dependencies)'
        '\n- "*some_solid+++" will execute "some_solid", all its ancestors, and its descendants'
        "   (downstream dependencies) within 3 levels down"
        '\n- "*some_solid,other_solid_a,other_solid_b+" will execute "some_solid" and all its'
        '   ancestors, "other_solid_a" itself, and "other_solid_b" and its direct child solids'
    ),
)
def pipeline_execute_command(**kwargs):
    with capture_interrupts():
        with DagsterInstance.get() as instance:
            execute_execute_command(instance, kwargs)


@telemetry_wrapper
def execute_execute_command(instance, kwargs):
    check.inst_param(instance, "instance", DagsterInstance)

    config = list(check.opt_tuple_param(kwargs.get("config"), "config", default=(), of_type=str))
    preset = kwargs.get("preset")
    mode = kwargs.get("mode")

    if preset and config:
        raise click.UsageError("Can not use --preset with --config.")

    tags = get_tags_from_args(kwargs)

    pipeline_origin = get_pipeline_python_origin_from_kwargs(kwargs)
    pipeline = recon_pipeline_from_origin(pipeline_origin)
    solid_selection = get_solid_selection_from_args(kwargs)
    result = do_execute_command(pipeline, instance, config, mode, tags, solid_selection, preset)

    if not result.success:
        raise click.ClickException("Pipeline run {} resulted in failure.".format(result.run_id))

    return result


def get_run_config_from_file_list(file_list):
    check.opt_list_param(file_list, "file_list", of_type=str)
    return load_yaml_from_glob_list(file_list) if file_list else {}


def _check_execute_external_pipeline_args(
    external_pipeline, run_config, mode, preset, tags, solid_selection
):
    check.inst_param(external_pipeline, "external_pipeline", ExternalPipeline)
    run_config = check.opt_dict_param(run_config, "run_config")
    check.opt_str_param(mode, "mode")
    check.opt_str_param(preset, "preset")
    check.invariant(
        not (mode is not None and preset is not None),
        "You may set only one of `mode` (got {mode}) or `preset` (got {preset}).".format(
            mode=mode, preset=preset
        ),
    )

    tags = check.opt_dict_param(tags, "tags", key_type=str)
    check.opt_list_param(solid_selection, "solid_selection", of_type=str)

    if preset is not None:
        pipeline_preset = external_pipeline.get_preset(preset)

        if pipeline_preset.run_config is not None:
            check.invariant(
                (not run_config) or (pipeline_preset.run_config == run_config),
                "The environment set in preset '{preset}' does not agree with the environment "
                "passed in the `run_config` argument.".format(preset=preset),
            )

            run_config = pipeline_preset.run_config

        # load solid_selection from preset
        if pipeline_preset.solid_selection is not None:
            check.invariant(
                solid_selection is None or solid_selection == pipeline_preset.solid_selection,
                "The solid_selection set in preset '{preset}', {preset_subset}, does not agree with "
                "the `solid_selection` argument: {solid_selection}".format(
                    preset=preset,
                    preset_subset=pipeline_preset.solid_selection,
                    solid_selection=solid_selection,
                ),
            )
            solid_selection = pipeline_preset.solid_selection

        check.invariant(
            mode is None or mode == pipeline_preset.mode,
            "Mode {mode} does not agree with the mode set in preset '{preset}': "
            "('{preset_mode}')".format(preset=preset, preset_mode=pipeline_preset.mode, mode=mode),
        )

        mode = pipeline_preset.mode

        tags = merge_dicts(pipeline_preset.tags, tags)

    if mode is not None:
        if not external_pipeline.has_mode(mode):
            raise DagsterInvariantViolationError(
                (
                    "You have attempted to execute pipeline {name} with mode {mode}. "
                    "Available modes: {modes}"
                ).format(
                    name=external_pipeline.name,
                    mode=mode,
                    modes=external_pipeline.available_modes,
                )
            )
    else:
        if len(external_pipeline.available_modes) > 1:
            raise DagsterInvariantViolationError(
                (
                    "Pipeline {name} has multiple modes (Available modes: {modes}) and you have "
                    "attempted to execute it without specifying a mode. Set "
                    "mode property on the PipelineRun object."
                ).format(name=external_pipeline.name, modes=external_pipeline.available_modes)
            )
        mode = external_pipeline.get_default_mode_name()

    tags = merge_dicts(external_pipeline.tags, tags)

    return (
        run_config,
        mode,
        tags,
        solid_selection,
    )


def _create_external_pipeline_run(
    instance,
    repo_location,
    external_repo,
    external_pipeline,
    run_config,
    mode,
    preset,
    tags,
    solid_selection,
    run_id,
):
    check.inst_param(instance, "instance", DagsterInstance)
    check.inst_param(repo_location, "repo_location", RepositoryLocation)
    check.inst_param(external_repo, "external_repo", ExternalRepository)
    check.inst_param(external_pipeline, "external_pipeline", ExternalPipeline)
    check.opt_dict_param(run_config, "run_config")

    check.opt_str_param(mode, "mode")
    check.opt_str_param(preset, "preset")
    check.opt_dict_param(tags, "tags", key_type=str)
    check.opt_list_param(solid_selection, "solid_selection", of_type=str)
    check.opt_str_param(run_id, "run_id")

    run_config, mode, tags, solid_selection = _check_execute_external_pipeline_args(
        external_pipeline,
        run_config,
        mode,
        preset,
        tags,
        solid_selection,
    )

    pipeline_name = external_pipeline.name
    pipeline_selector = PipelineSelector(
        location_name=repo_location.name,
        repository_name=external_repo.name,
        pipeline_name=pipeline_name,
        solid_selection=solid_selection,
    )

    subset_pipeline_result = repo_location.get_subset_external_pipeline_result(pipeline_selector)
    if subset_pipeline_result.success == False:
        raise DagsterLaunchFailedError(
            "Failed to load external pipeline subset: {error_message}".format(
                error_message=subset_pipeline_result.error.message
            ),
            serializable_error_info=subset_pipeline_result.error,
        )

    external_pipeline_subset = ExternalPipeline(
        subset_pipeline_result.external_pipeline_data,
        external_repo.handle,
    )

    pipeline_mode = mode or external_pipeline_subset.get_default_mode_name()

    external_execution_plan = repo_location.get_external_execution_plan(
        external_pipeline_subset,
        run_config,
        pipeline_mode,
        step_keys_to_execute=None,
    )
    if isinstance(external_execution_plan, ExecutionPlanSnapshotErrorData):
        raise DagsterLaunchFailedError(
            "Failed to load external execution plan",
            serializable_error_info=external_execution_plan.error,
        )
    else:
        execution_plan_snapshot = external_execution_plan.execution_plan_snapshot

    return instance.create_run(
        pipeline_name=pipeline_name,
        run_id=run_id,
        run_config=run_config,
        mode=pipeline_mode,
        solids_to_execute=external_pipeline_subset.solids_to_execute,
        step_keys_to_execute=None,
        solid_selection=solid_selection,
        status=None,
        root_run_id=None,
        parent_run_id=None,
        tags=tags,
        pipeline_snapshot=external_pipeline_subset.pipeline_snapshot,
        execution_plan_snapshot=execution_plan_snapshot,
        parent_pipeline_snapshot=external_pipeline_subset.parent_pipeline_snapshot,
        external_pipeline_origin=external_pipeline_subset.get_external_origin(),
    )


def do_execute_command(
    pipeline,
    instance,
    config,
    mode=None,
    tags=None,
    solid_selection=None,
    preset=None,
):
    check.inst_param(pipeline, "pipeline", IPipeline)
    check.inst_param(instance, "instance", DagsterInstance)
    check.opt_list_param(config, "config", of_type=str)

    return execute_pipeline(
        pipeline,
        run_config=get_run_config_from_file_list(config),
        mode=mode,
        tags=tags,
        instance=instance,
        raise_on_error=False,
        solid_selection=solid_selection,
        preset=preset,
    )


@click.command(
    name="launch",
    help="Launch a pipeline using the run launcher configured on the Dagster instance.\n\n{instructions}".format(
        instructions=get_pipeline_instructions("launch")
    ),
)
@pipeline_target_argument
@python_pipeline_config_argument("launch")
@click.option(
    "--config-json",
    type=click.STRING,
    help="JSON string of run config to use for this pipeline run. Cannot be used with -c / --config.",
)
@click.option(
    "--preset",
    type=click.STRING,
    help="Specify a preset to use for this pipeline. Presets are defined on pipelines under "
    "preset_defs.",
)
@click.option(
    "--mode", type=click.STRING, help="The name of the mode in which to execute the pipeline."
)
@click.option("--tags", type=click.STRING, help="JSON string of tags to use for this pipeline run")
@click.option(
    "-s",
    "--solid-selection",
    type=click.STRING,
    help=(
        "Specify the solid subselection to launch. It can be multiple clauses separated by commas."
        "Examples:"
        '\n- "some_solid" will launch "some_solid" itself'
        '\n- "*some_solid" will launch "some_solid" and all its ancestors (upstream dependencies)'
        '\n- "*some_solid+++" will launch "some_solid", all its ancestors, and its descendants'
        "   (downstream dependencies) within 3 levels down"
        '\n- "*some_solid,other_solid_a,other_solid_b+" will launch "some_solid" and all its'
        '   ancestors, "other_solid_a" itself, and "other_solid_b" and its direct child solids'
    ),
)
@click.option("--run-id", type=click.STRING, help="The ID to give to the launched pipeline run")
def pipeline_launch_command(**kwargs):
    with DagsterInstance.get() as instance:
        return execute_launch_command(instance, kwargs)


@telemetry_wrapper
def execute_launch_command(instance, kwargs):
    preset = kwargs.get("preset")
    mode = kwargs.get("mode")
    check.inst_param(instance, "instance", DagsterInstance)
    config = get_config_from_args(kwargs)

    with get_repository_location_from_kwargs(kwargs) as repo_location:
        external_repo = get_external_repository_from_repo_location(
            repo_location, kwargs.get("repository")
        )
        external_pipeline = get_external_pipeline_from_external_repo(
            external_repo, kwargs.get("pipeline")
        )

        log_external_repo_stats(
            instance=instance,
            external_pipeline=external_pipeline,
            external_repo=external_repo,
            source="pipeline_launch_command",
        )

        if preset and config:
            raise click.UsageError("Can not use --preset with -c / --config / --config-json.")

        run_tags = get_tags_from_args(kwargs)

        solid_selection = get_solid_selection_from_args(kwargs)

        pipeline_run = _create_external_pipeline_run(
            instance=instance,
            repo_location=repo_location,
            external_repo=external_repo,
            external_pipeline=external_pipeline,
            run_config=config,
            mode=mode,
            preset=preset,
            tags=run_tags,
            solid_selection=solid_selection,
            run_id=kwargs.get("run_id"),
        )

        return instance.submit_run(pipeline_run.run_id, external_pipeline)


@click.command(
    name="scaffold_config",
    help="Scaffold the config for a pipeline.\n\n{instructions}".format(
        instructions=get_pipeline_in_same_python_env_instructions("scaffold_config")
    ),
)
@python_pipeline_target_argument
@click.option("--print-only-required", default=False, is_flag=True)
def pipeline_scaffold_command(**kwargs):
    execute_scaffold_command(kwargs, click.echo)


def execute_scaffold_command(cli_args, print_fn):
    pipeline_origih = get_pipeline_python_origin_from_kwargs(cli_args)
    pipeline = recon_pipeline_from_origin(pipeline_origih)
    skip_non_required = cli_args["print_only_required"]
    do_scaffold_command(pipeline.get_definition(), print_fn, skip_non_required)


def do_scaffold_command(pipeline_def, printer, skip_non_required):
    check.inst_param(pipeline_def, "pipeline_def", PipelineDefinition)
    check.callable_param(printer, "printer")
    check.bool_param(skip_non_required, "skip_non_required")

    config_dict = scaffold_pipeline_config(pipeline_def, skip_non_required=skip_non_required)
    yaml_string = yaml.dump(config_dict, default_flow_style=False)
    printer(yaml_string)


def gen_partition_names_from_args(partition_names, kwargs):
    partition_selector_args = [
        bool(kwargs.get("all")),
        bool(kwargs.get("partitions")),
        (bool(kwargs.get("from")) or bool(kwargs.get("to"))),
    ]
    if sum(partition_selector_args) > 1:
        raise click.UsageError(
            "error, cannot use more than one of: `--all`, `--partitions`, `--from/--to`"
        )

    if kwargs.get("all"):
        return partition_names

    if kwargs.get("partitions"):
        selected_args = [s.strip() for s in kwargs.get("partitions").split(",") if s.strip()]
        selected_partitions = [
            partition for partition in partition_names if partition in selected_args
        ]
        if len(selected_partitions) < len(selected_args):
            selected_names = [partition for partition in selected_partitions]
            unknown = [selected for selected in selected_args if selected not in selected_names]
            raise click.UsageError("Unknown partitions: {}".format(unknown.join(", ")))
        return selected_partitions

    start = validate_partition_slice(partition_names, "from", kwargs.get("from"))
    end = validate_partition_slice(partition_names, "to", kwargs.get("to"))

    return partition_names[start:end]


def get_config_from_args(kwargs):
    config_files = kwargs.get("config")
    config_json = kwargs.get("config_json")

    if not config_files and not config_json:
        return {}

    if config_files and config_json:
        raise click.UsageError("Cannot specify both -c / --config and --config-json")

    if config_files:
        config_file_list = list(
            check.opt_tuple_param(kwargs.get("config"), "config", default=(), of_type=str)
        )
        return get_run_config_from_file_list(config_file_list)

    if config_json:
        try:
            return json.loads(config_json)

        except JSONDecodeError:
            raise click.UsageError(
                "Invalid JSON-string given for `--config-json`: {}\n\n{}".format(
                    config_json,
                    serializable_error_info_from_exc_info(sys.exc_info()).to_string(),
                )
            )


def get_tags_from_args(kwargs):
    if kwargs.get("tags") is None:
        return {}
    try:
        return json.loads(kwargs.get("tags"))
    except JSONDecodeError:
        raise click.UsageError(
            "Invalid JSON-string given for `--tags`: {}\n\n{}".format(
                kwargs.get("tags"),
                serializable_error_info_from_exc_info(sys.exc_info()).to_string(),
            )
        )


def get_solid_selection_from_args(kwargs):
    solid_selection_str = kwargs.get("solid_selection")
    if not isinstance(solid_selection_str, str):
        return None

    return [ele.strip() for ele in solid_selection_str.split(",")] if solid_selection_str else None


def print_partition_format(partitions, indent_level):
    if not IS_WINDOWS and sys.stdout.isatty():
        _, tty_width = os.popen("stty size", "r").read().split()
        screen_width = min(250, int(tty_width))
    else:
        screen_width = 250
    max_str_len = max(len(x) for x in partitions)
    spacing = 10
    num_columns = min(10, int((screen_width - indent_level) / (max_str_len + spacing)))
    column_width = int((screen_width - indent_level) / num_columns)
    prefix = " " * max(0, indent_level - spacing)
    lines = []
    for chunk in list(split_chunk(partitions, num_columns)):
        lines.append(prefix + "".join(partition.rjust(column_width) for partition in chunk))

    return "\n" + "\n".join(lines)


def split_chunk(l, n):
    for i in range(0, len(l), n):
        yield l[i : i + n]


def validate_partition_slice(partition_names, name, value):
    is_start = name == "from"
    if value is None:
        return 0 if is_start else len(partition_names)
    if value not in partition_names:
        raise click.UsageError("invalid value {} for {}".format(value, name))
    index = partition_names.index(value)
    return index if is_start else index + 1


@click.command(
    name="backfill",
    help="Backfill a partitioned pipeline.\n\n{instructions}".format(
        instructions=get_partitioned_pipeline_instructions("backfill")
    ),
)
@pipeline_target_argument
@click.option(
    "--partitions",
    type=click.STRING,
    help="Comma-separated list of partition names that we want to backfill",
)
@click.option(
    "--partition-set",
    type=click.STRING,
    help="The name of the partition set over which we want to backfill.",
)
@click.option(
    "--all",
    type=click.STRING,
    help="Specify to select all partitions to backfill.",
)
@click.option(
    "--from",
    type=click.STRING,
    help=(
        "Specify a start partition for this backfill job"
        "\n\nExample: "
        "dagster pipeline backfill log_daily_stats --from 20191101"
    ),
)
@click.option(
    "--to",
    type=click.STRING,
    help=(
        "Specify an end partition for this backfill job"
        "\n\nExample: "
        "dagster pipeline backfill log_daily_stats --to 20191201"
    ),
)
@click.option("--tags", type=click.STRING, help="JSON string of tags to use for this pipeline run")
@click.option("--noprompt", is_flag=True)
def pipeline_backfill_command(**kwargs):
    with DagsterInstance.get() as instance:
        execute_backfill_command(kwargs, click.echo, instance)


def execute_backfill_command(cli_args, print_fn, instance):
    with get_repository_location_from_kwargs(cli_args) as repo_location:
        _execute_backfill_command_at_location(cli_args, print_fn, instance, repo_location)


def _execute_backfill_command_at_location(cli_args, print_fn, instance, repo_location):
    external_repo = get_external_repository_from_repo_location(
        repo_location, cli_args.get("repository")
    )

    external_pipeline = get_external_pipeline_from_external_repo(
        external_repo,
        cli_args.get("pipeline"),
    )

    noprompt = cli_args.get("noprompt")

    pipeline_partition_set_names = {
        external_partition_set.name: external_partition_set
        for external_partition_set in external_repo.get_external_partition_sets()
        if external_partition_set.pipeline_name == external_pipeline.name
    }

    if not pipeline_partition_set_names:
        raise click.UsageError(
            "No partition sets found for pipeline `{}`".format(external_pipeline.name)
        )
    partition_set_name = cli_args.get("partition_set")
    if not partition_set_name:
        if len(pipeline_partition_set_names) == 1:
            partition_set_name = next(iter(pipeline_partition_set_names.keys()))
        elif noprompt:
            raise click.UsageError("No partition set specified (see option `--partition-set`)")
        else:
            partition_set_name = click.prompt(
                "Select a partition set to use for backfill: {}".format(
                    ", ".join(x for x in pipeline_partition_set_names.keys())
                )
            )

    partition_set = pipeline_partition_set_names.get(partition_set_name)

    if not partition_set:
        raise click.UsageError("No partition set found named `{}`".format(partition_set_name))

    run_tags = get_tags_from_args(cli_args)

    repo_handle = RepositoryHandle(
        repository_name=external_repo.name,
        repository_location_handle=repo_location.location_handle,
    )

    # Resolve partitions to backfill
    partition_names_or_error = repo_location.get_external_partition_names(
        repo_handle,
        partition_set_name,
    )

    if isinstance(partition_names_or_error, ExternalPartitionExecutionErrorData):
        raise DagsterBackfillFailedError(
            "Failure fetching partition names for {partition_set_name}: {error_message}".format(
                partition_set_name=partition_set_name,
                error_message=partition_names_or_error.error.message,
            ),
            serialized_error_info=partition_names_or_error.error,
        )

    partition_names = gen_partition_names_from_args(
        partition_names_or_error.partition_names, cli_args
    )

    # Print backfill info
    print_fn("\n     Pipeline: {}".format(external_pipeline.name))
    print_fn("Partition set: {}".format(partition_set_name))
    print_fn("   Partitions: {}\n".format(print_partition_format(partition_names, indent_level=15)))

    # Confirm and launch
    if noprompt or click.confirm(
        "Do you want to proceed with the backfill ({} partitions)?".format(len(partition_names))
    ):

        print_fn("Launching runs... ")

        backfill_id = make_new_backfill_id()
        backfill_job = PartitionBackfill(
            backfill_id=backfill_id,
            partition_set_origin=partition_set.get_external_origin(),
            status=BulkActionStatus.REQUESTED,
            partition_names=partition_names,
            from_failure=False,
            reexecution_steps=None,
            tags=run_tags,
            backfill_timestamp=pendulum.now("UTC").timestamp(),
        )
        partition_execution_data = repo_location.get_external_partition_set_execution_param_data(
            repository_handle=repo_handle,
            partition_set_name=partition_set_name,
            partition_names=partition_names,
        )

        if isinstance(partition_execution_data, ExternalPartitionExecutionErrorData):
            if instance.has_bulk_actions_table():
                instance.add_backfill(
                    backfill_job.with_status(BulkActionStatus.FAILED).with_error(
                        partition_execution_data.error
                    )
                )
            return print_fn("Backfill failed: {}".format(partition_execution_data.error))

        assert isinstance(partition_execution_data, ExternalPartitionSetExecutionParamData)

        for partition_data in partition_execution_data.partition_data:
            pipeline_run = create_backfill_run(
                instance,
                repo_location,
                external_pipeline,
                partition_set,
                backfill_job,
                partition_data,
            )
            if pipeline_run:
                instance.submit_run(pipeline_run.run_id, external_pipeline)

        if instance.has_bulk_actions_table():
            instance.add_backfill(backfill_job.with_status(BulkActionStatus.COMPLETED))

        print_fn("Launched backfill job `{}`".format(backfill_id))

    else:
        print_fn("Aborted!")


pipeline_cli = create_pipeline_cli_group()
