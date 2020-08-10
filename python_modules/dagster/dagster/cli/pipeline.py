from __future__ import print_function

import os
import re
import sys
import textwrap
import time

import click
import yaml

from dagster import PipelineDefinition, check, execute_pipeline
from dagster.cli.workspace.cli_target import (
    get_external_pipeline_from_external_repo,
    get_external_pipeline_from_kwargs,
    get_external_repository_from_kwargs,
    get_external_repository_from_repo_location,
    get_repository_location_from_kwargs,
    pipeline_target_argument,
    repository_target_argument,
)
from dagster.core.definitions.executable import ExecutablePipeline
from dagster.core.errors import (
    DagsterBackfillFailedError,
    DagsterInvariantViolationError,
    DagsterLaunchFailedError,
)
from dagster.core.host_representation import (
    ExternalPipeline,
    ExternalRepository,
    RepositoryHandle,
    RepositoryLocation,
)
from dagster.core.host_representation.external_data import ExternalPartitionExecutionErrorData
from dagster.core.host_representation.selector import PipelineSelector
from dagster.core.instance import DagsterInstance
from dagster.core.snap import PipelineSnapshot, SolidInvocationSnap
from dagster.core.snap.execution_plan_snapshot import ExecutionPlanSnapshotErrorData
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.core.telemetry import log_external_repo_stats, telemetry_wrapper
from dagster.core.utils import make_new_backfill_id
from dagster.seven import IS_WINDOWS, JSONDecodeError, json
from dagster.utils import DEFAULT_WORKSPACE_YAML_FILENAME, load_yaml_from_glob_list, merge_dicts
from dagster.utils.error import serializable_error_info_from_exc_info
from dagster.utils.hosted_user_process import recon_pipeline_from_origin
from dagster.utils.indenting_printer import IndentingPrinter

from .config_scaffolder import scaffold_pipeline_config


def create_pipeline_cli_group():
    group = click.Group(name="pipeline")
    group.add_command(pipeline_list_command)
    group.add_command(pipeline_print_command)
    group.add_command(pipeline_execute_command)
    group.add_command(pipeline_backfill_command)
    group.add_command(pipeline_scaffold_command)
    group.add_command(pipeline_launch_command)
    return group


WORKSPACE_TARGET_WARNING = 'Can only use ONE of --workspace/-w, --python-file/-f, --module-name/-m.'
WORKSPACE_ARG_NAMES = ['workspace', 'module_name', 'python_file', 'attribute']


def apply_click_params(command, *click_params):
    for click_param in click_params:
        command = click_param(command)
    return command


@click.command(
    name='list',
    help="List the pipelines in a repository. {warning}".format(warning=WORKSPACE_TARGET_WARNING),
)
@repository_target_argument
def pipeline_list_command(**kwargs):
    return execute_list_command(kwargs, click.echo, DagsterInstance.get())


def execute_list_command(cli_args, print_fn, instance):
    check.inst_param(instance, 'instance', DagsterInstance)
    external_repository = get_external_repository_from_kwargs(cli_args, instance)
    title = 'Repository {name}'.format(name=external_repository.name)
    print_fn(title)
    print_fn('*' * len(title))
    first = True
    for pipeline in external_repository.get_all_external_pipelines():
        pipeline_title = 'Pipeline: {name}'.format(name=pipeline.name)

        if not first:
            print_fn('*' * len(pipeline_title))
        first = False

        print_fn(pipeline_title)
        if pipeline.description:
            print_fn('Description:')
            print_fn(format_description(pipeline.description, indent=' ' * 4))
        print_fn('Solids: (Execution Order)')
        for solid_name in pipeline.pipeline_snapshot.solid_names_in_topological_order:
            print_fn('    ' + solid_name)


def format_description(desc, indent):
    check.str_param(desc, 'desc')
    check.str_param(indent, 'indent')
    desc = re.sub(r'\s+', ' ', desc)
    dedented = textwrap.dedent(desc)
    wrapper = textwrap.TextWrapper(initial_indent='', subsequent_indent=indent)
    filled = wrapper.fill(dedented)
    return filled


def get_pipeline_instructions(command_name):
    return (
        'This commands targets a pipeline. The pipeline can be specified in a number of ways:'
        '\n\n1. dagster pipeline {command_name} -p <<pipeline_name>> (works if .{default_filename} exists)'
        '\n\n2. dagster pipeline {command_name} -p <<pipeline_name>> -w path/to/{default_filename}'
        '\n\n3. dagster pipeline {command_name} -f /path/to/file.py -a define_some_pipeline'
        '\n\n4. dagster pipeline {command_name} -m a_module.submodule -a define_some_pipeline'
        '\n\n5. dagster pipeline {command_name} -f /path/to/file.py -a define_some_repo -p <<pipeline_name>>'
        '\n\n6. dagster pipeline {command_name} -m a_module.submodule -a define_some_repo -p <<pipeline_name>>'
    ).format(command_name=command_name, default_filename=DEFAULT_WORKSPACE_YAML_FILENAME)


def get_partitioned_pipeline_instructions(command_name):
    return (
        'This commands targets a partitioned pipeline. The pipeline and partition set must be '
        'defined in a repository, which can be specified in a number of ways:'
        '\n\n1. dagster pipeline {command_name} -p <<pipeline_name>> (works if .{default_filename} exists)'
        '\n\n2. dagster pipeline {command_name} -p <<pipeline_name>> -w path/to/{default_filename}'
        '\n\n3. dagster pipeline {command_name} -f /path/to/file.py -a define_some_repo -p <<pipeline_name>>'
        '\n\n4. dagster pipeline {command_name} -m a_module.submodule -a define_some_repo -p <<pipeline_name>>'
    ).format(command_name=command_name, default_filename=DEFAULT_WORKSPACE_YAML_FILENAME)


@click.command(
    name='print',
    help='Print a pipeline.\n\n{instructions}'.format(
        instructions=get_pipeline_instructions('print')
    ),
)
@click.option('--verbose', is_flag=True)
@pipeline_target_argument
def pipeline_print_command(verbose, **cli_args):
    return execute_print_command(verbose, cli_args, click.echo, instance=DagsterInstance.get())


def execute_print_command(verbose, cli_args, print_fn, instance):
    external_pipeline = get_external_pipeline_from_kwargs(cli_args, instance)
    pipeline_snapshot = external_pipeline.pipeline_snapshot

    if verbose:
        print_pipeline(pipeline_snapshot, print_fn=print_fn)
    else:
        print_solids(pipeline_snapshot, print_fn=print_fn)


def print_solids(pipeline_snapshot, print_fn):
    check.inst_param(pipeline_snapshot, 'pipeline', PipelineSnapshot)
    check.callable_param(print_fn, 'print_fn')

    printer = IndentingPrinter(indent_level=2, printer=print_fn)
    printer.line('Pipeline: {name}'.format(name=pipeline_snapshot.name))

    printer.line('Solids:')
    for solid in pipeline_snapshot.dep_structure_snapshot.solid_invocation_snaps:
        with printer.with_indent():
            printer.line('Solid: {name}'.format(name=solid.solid_name))


def print_pipeline(pipeline_snapshot, print_fn):
    check.inst_param(pipeline_snapshot, 'pipeline', PipelineSnapshot)
    check.callable_param(print_fn, 'print_fn')
    printer = IndentingPrinter(indent_level=2, printer=print_fn)
    printer.line('Pipeline: {name}'.format(name=pipeline_snapshot.name))
    print_description(printer, pipeline_snapshot.description)

    printer.line('Solids:')
    for solid in pipeline_snapshot.dep_structure_snapshot.solid_invocation_snaps:
        with printer.with_indent():
            print_solid(printer, pipeline_snapshot, solid)


def print_description(printer, desc):
    with printer.with_indent():
        if desc:
            printer.line('Description:')
            with printer.with_indent():
                printer.line(format_description(desc, printer.current_indent_str))


def print_solid(printer, pipeline_snapshot, solid_invocation_snap):
    check.inst_param(pipeline_snapshot, 'pipeline_snapshot', PipelineSnapshot)
    check.inst_param(solid_invocation_snap, 'solid_invocation_snap', SolidInvocationSnap)
    printer.line('Solid: {name}'.format(name=solid_invocation_snap.solid_name))
    with printer.with_indent():
        printer.line('Inputs:')
        for input_dep_snap in solid_invocation_snap.input_dep_snaps:
            with printer.with_indent():
                printer.line('Input: {name}'.format(name=input_dep_snap.input_name))

        printer.line('Outputs:')
        for output_def_snap in pipeline_snapshot.get_solid_def_snap(
            solid_invocation_snap.solid_def_name
        ).output_def_snaps:
            printer.line(output_def_snap.name)


@click.command(
    name='execute',
    help='Execute a pipeline.\n\n{instructions}'.format(
        instructions=get_pipeline_instructions('execute')
    ),
)
@pipeline_target_argument
@click.option(
    '-c',
    '--config',
    type=click.Path(exists=True),
    multiple=True,
    help=(
        'Specify one or more run config files. These can also be file patterns. '
        'If more than one run config file is captured then those files are merged. '
        'Files listed first take precedence. They will smash the values of subsequent '
        'files at the key-level granularity. If the file is a pattern then you must '
        'enclose it in double quotes'
        '\n\nExample: '
        'dagster pipeline execute -p pandas_hello_world -c "pandas_hello_world/*.yaml"'
        '\n\nYou can also specify multiple files:'
        '\n\nExample: '
        'dagster pipeline execute -p pandas_hello_world -c pandas_hello_world/solids.yaml '
        '-e pandas_hello_world/env.yaml'
    ),
)
@click.option(
    '--preset',
    type=click.STRING,
    help='Specify a preset to use for this pipeline. Presets are defined on pipelines under '
    'preset_defs.',
)
@click.option(
    '--mode', type=click.STRING, help='The name of the mode in which to execute the pipeline.'
)
@click.option('--tags', type=click.STRING, help='JSON string of tags to use for this pipeline run')
@click.option(
    '-s',
    '--solid-selection',
    type=click.STRING,
    help=(
        'Specify the solid subselection to execute. It can be multiple clauses separated by commas.'
        'Examples:'
        '\n- "some_solid" will execute "some_solid" itself'
        '\n- "*some_solid" will execute "some_solid" and all its ancestors (upstream dependencies)'
        '\n- "*some_solid+++" will execute "some_solid", all its ancestors, and its descendants'
        '   (downstream dependencies) within 3 levels down'
        '\n- "*some_solid,other_solid_a,other_solid_b+" will execute "some_solid" and all its'
        '   ancestors, "other_solid_a" itself, and "other_solid_b" and its direct child solids'
    ),
)
def pipeline_execute_command(**kwargs):
    execute_execute_command(DagsterInstance.get(), kwargs)


@telemetry_wrapper
def execute_execute_command(instance, kwargs):
    check.inst_param(instance, 'instance', DagsterInstance)

    config = list(check.opt_tuple_param(kwargs.get('config'), 'config', default=(), of_type=str))
    preset = kwargs.get('preset')
    mode = kwargs.get('mode')

    if preset and config:
        raise click.UsageError('Can not use --preset with --config.')

    tags = get_tags_from_args(kwargs)

    external_pipeline = get_external_pipeline_from_kwargs(kwargs, instance)
    # We should move this to use external pipeline
    # https://github.com/dagster-io/dagster/issues/2556

    pipeline = recon_pipeline_from_origin(external_pipeline.handle.get_origin())
    solid_selection = get_solid_selection_from_args(kwargs)
    result = do_execute_command(pipeline, instance, config, mode, tags, solid_selection, preset)

    if not result.success:
        raise click.ClickException('Pipeline run {} resulted in failure.'.format(result.run_id))

    return result


def get_run_config_from_file_list(file_list):
    check.opt_list_param(file_list, 'file_list', of_type=str)
    return load_yaml_from_glob_list(file_list) if file_list else {}


def _check_execute_external_pipeline_args(
    external_pipeline, run_config, mode, preset, tags, solid_selection
):
    check.inst_param(external_pipeline, 'external_pipeline', ExternalPipeline)
    run_config = check.opt_dict_param(run_config, 'run_config')
    check.opt_str_param(mode, 'mode')
    check.opt_str_param(preset, 'preset')
    check.invariant(
        not (mode is not None and preset is not None),
        'You may set only one of `mode` (got {mode}) or `preset` (got {preset}).'.format(
            mode=mode, preset=preset
        ),
    )

    tags = check.opt_dict_param(tags, 'tags', key_type=str)
    check.opt_list_param(solid_selection, 'solid_selection', of_type=str)

    if preset is not None:
        pipeline_preset = external_pipeline.get_preset(preset)

        if pipeline_preset.run_config is not None:
            check.invariant(
                (not run_config) or (pipeline_preset.run_config == run_config),
                'The environment set in preset \'{preset}\' does not agree with the environment '
                'passed in the `run_config` argument.'.format(preset=preset),
            )

            run_config = pipeline_preset.run_config

        # load solid_selection from preset
        if pipeline_preset.solid_selection is not None:
            check.invariant(
                solid_selection is None or solid_selection == pipeline_preset.solid_selection,
                'The solid_selection set in preset \'{preset}\', {preset_subset}, does not agree with '
                'the `solid_selection` argument: {solid_selection}'.format(
                    preset=preset,
                    preset_subset=pipeline_preset.solid_selection,
                    solid_selection=solid_selection,
                ),
            )
            solid_selection = pipeline_preset.solid_selection

        check.invariant(
            mode is None or mode == pipeline_preset.mode,
            'Mode {mode} does not agree with the mode set in preset \'{preset}\': '
            '(\'{preset_mode}\')'.format(
                preset=preset, preset_mode=pipeline_preset.mode, mode=mode
            ),
        )

        mode = pipeline_preset.mode

        tags = merge_dicts(pipeline_preset.tags, tags)

    if mode is not None:
        if not external_pipeline.has_mode(mode):
            raise DagsterInvariantViolationError(
                (
                    'You have attempted to execute pipeline {name} with mode {mode}. '
                    'Available modes: {modes}'
                ).format(
                    name=external_pipeline.name, mode=mode, modes=external_pipeline.available_modes,
                )
            )
    else:
        if len(external_pipeline.available_modes) > 1:
            raise DagsterInvariantViolationError(
                (
                    'Pipeline {name} has multiple modes (Available modes: {modes}) and you have '
                    'attempted to execute it without specifying a mode. Set '
                    'mode property on the PipelineRun object.'
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
):
    check.inst_param(instance, 'instance', DagsterInstance)
    check.inst_param(repo_location, 'repo_location', RepositoryLocation)
    check.inst_param(external_repo, 'external_repo', ExternalRepository)
    check.inst_param(external_pipeline, 'external_pipeline', ExternalPipeline)
    check.opt_dict_param(run_config, 'run_config')

    check.opt_str_param(mode, 'mode')
    check.opt_str_param(preset, 'preset')
    check.opt_dict_param(tags, 'tags', key_type=str)
    check.opt_list_param(solid_selection, 'solid_selection', of_type=str)

    run_config, mode, tags, solid_selection = _check_execute_external_pipeline_args(
        external_pipeline, run_config, mode, preset, tags, solid_selection,
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
            'Failed to load external pipeline subset: {error_message}'.format(
                error_message=subset_pipeline_result.error.message
            ),
            serializable_error_info=subset_pipeline_result.error,
        )

    external_pipeline_subset = ExternalPipeline(
        subset_pipeline_result.external_pipeline_data, external_repo.handle,
    )

    pipeline_mode = mode or external_pipeline_subset.get_default_mode_name()

    external_execution_plan = repo_location.get_external_execution_plan(
        external_pipeline_subset, run_config, pipeline_mode, step_keys_to_execute=None,
    )
    if isinstance(external_execution_plan, ExecutionPlanSnapshotErrorData):
        raise DagsterLaunchFailedError(
            'Failed to load external execution plan',
            serializable_error_info=external_execution_plan.error,
        )
    else:
        execution_plan_snapshot = external_execution_plan.execution_plan_snapshot

    return instance.create_run(
        pipeline_name=pipeline_name,
        run_id=None,
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
    )


def do_execute_command(
    pipeline, instance, config, mode=None, tags=None, solid_selection=None, preset=None,
):
    check.inst_param(pipeline, 'pipeline', ExecutablePipeline)
    check.inst_param(instance, 'instance', DagsterInstance)
    check.opt_list_param(config, 'config', of_type=str)

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
    name='launch',
    help='Launch a pipeline using the run launcher configured on the Dagster instance.\n\n{instructions}'.format(
        instructions=get_pipeline_instructions('launch')
    ),
)
@pipeline_target_argument
@click.option(
    '-c',
    '--config',
    type=click.Path(exists=True),
    multiple=True,
    help=(
        'Specify one or more run config files. These can also be file patterns. '
        'If more than one run config file is captured then those files are merged. '
        'Files listed first take precedence. They will smash the values of subsequent '
        'files at the key-level granularity. If the file is a pattern then you must '
        'enclose it in double quotes'
        '\n\nExample: '
        'dagster pipeline launch pandas_hello_world -c "pandas_hello_world/*.yaml"'
        '\n\nYou can also specify multiple files:'
        '\n\nExample: '
        'dagster pipeline launch pandas_hello_world -c pandas_hello_world/solids.yaml '
        '-e pandas_hello_world/env.yaml'
    ),
)
@click.option(
    '--preset',
    type=click.STRING,
    help='Specify a preset to use for this pipeline. Presets are defined on pipelines under '
    'preset_defs.',
)
@click.option(
    '--mode', type=click.STRING, help='The name of the mode in which to execute the pipeline.'
)
@click.option('--tags', type=click.STRING, help='JSON string of tags to use for this pipeline run')
@click.option(
    '-s',
    '--solid-selection',
    type=click.STRING,
    help=(
        'Specify the solid subselection to launch. It can be multiple clauses separated by commas.'
        'Examples:'
        '\n- "some_solid" will launch "some_solid" itself'
        '\n- "*some_solid" will launch "some_solid" and all its ancestors (upstream dependencies)'
        '\n- "*some_solid+++" will launch "some_solid", all its ancestors, and its descendants'
        '   (downstream dependencies) within 3 levels down'
        '\n- "*some_solid,other_solid_a,other_solid_b+" will launch "some_solid" and all its'
        '   ancestors, "other_solid_a" itself, and "other_solid_b" and its direct child solids'
    ),
)
def pipeline_launch_command(**kwargs):
    return execute_launch_command(DagsterInstance.get(), kwargs)


@telemetry_wrapper
def execute_launch_command(instance, kwargs):
    preset = kwargs.get('preset')
    mode = kwargs.get('mode')
    check.inst_param(instance, 'instance', DagsterInstance)
    config = list(check.opt_tuple_param(kwargs.get('config'), 'config', default=(), of_type=str))

    repo_location = get_repository_location_from_kwargs(kwargs, instance)
    external_repo = get_external_repository_from_repo_location(
        repo_location, kwargs.get('repository')
    )
    external_pipeline = get_external_pipeline_from_external_repo(
        external_repo, kwargs.get('pipeline'),
    )

    log_external_repo_stats(
        instance=instance,
        external_pipeline=external_pipeline,
        external_repo=external_repo,
        source='pipeline_launch_command',
    )

    if preset:
        if config:
            raise click.UsageError('Can not use --preset with --config.')

        preset = external_pipeline.get_preset(preset)
    else:
        preset = None

    run_tags = get_tags_from_args(kwargs)

    solid_selection = get_solid_selection_from_args(kwargs)

    pipeline_run = _create_external_pipeline_run(
        instance=instance,
        repo_location=repo_location,
        external_repo=external_repo,
        external_pipeline=external_pipeline,
        run_config=get_run_config_from_file_list(config),
        mode=mode,
        preset=preset,
        tags=run_tags,
        solid_selection=solid_selection,
    )

    return instance.launch_run(pipeline_run.run_id, external_pipeline)


@click.command(
    name='scaffold_config',
    help='Scaffold the config for a pipeline.\n\n{instructions}'.format(
        instructions=get_pipeline_instructions('scaffold_config')
    ),
)
@pipeline_target_argument
@click.option('--print-only-required', default=False, is_flag=True)
def pipeline_scaffold_command(**kwargs):
    execute_scaffold_command(kwargs, click.echo)


def execute_scaffold_command(cli_args, print_fn):
    external_pipeline = get_external_pipeline_from_kwargs(cli_args, DagsterInstance.get())
    # We should move this to use external pipeline
    # https://github.com/dagster-io/dagster/issues/2556
    pipeline = recon_pipeline_from_origin(external_pipeline.get_origin())
    skip_non_required = cli_args['print_only_required']
    do_scaffold_command(pipeline.get_definition(), print_fn, skip_non_required)


def do_scaffold_command(pipeline_def, printer, skip_non_required):
    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
    check.callable_param(printer, 'printer')
    check.bool_param(skip_non_required, 'skip_non_required')

    config_dict = scaffold_pipeline_config(pipeline_def, skip_non_required=skip_non_required)
    yaml_string = yaml.dump(config_dict, default_flow_style=False)
    printer(yaml_string)


def gen_partition_names_from_args(partition_names, kwargs):
    partition_selector_args = [
        bool(kwargs.get('all')),
        bool(kwargs.get('partitions')),
        (bool(kwargs.get('from')) or bool(kwargs.get('to'))),
    ]
    if sum(partition_selector_args) > 1:
        raise click.UsageError(
            'error, cannot use more than one of: `--all`, `--partitions`, `--from/--to`'
        )

    if kwargs.get('all'):
        return partition_names

    if kwargs.get('partitions'):
        selected_args = [s.strip() for s in kwargs.get('partitions').split(',') if s.strip()]
        selected_partitions = [
            partition for partition in partition_names if partition in selected_args
        ]
        if len(selected_partitions) < len(selected_args):
            selected_names = [partition for partition in selected_partitions]
            unknown = [selected for selected in selected_args if selected not in selected_names]
            raise click.UsageError('Unknown partitions: {}'.format(unknown.join(', ')))
        return selected_partitions

    start = validate_partition_slice(partition_names, 'from', kwargs.get('from'))
    end = validate_partition_slice(partition_names, 'to', kwargs.get('to'))

    return partition_names[start:end]


def get_tags_from_args(kwargs):
    if kwargs.get('tags') is None:
        return {}
    try:
        return json.loads(kwargs.get('tags'))
    except JSONDecodeError:
        raise click.UsageError(
            'Invalid JSON-string given for `--tags`: {}\n\n{}'.format(
                kwargs.get('tags'),
                serializable_error_info_from_exc_info(sys.exc_info()).to_string(),
            )
        )


def get_solid_selection_from_args(kwargs):
    solid_selection_str = kwargs.get('solid_selection')
    if not check.is_str(solid_selection_str):
        return None

    return [ele.strip() for ele in solid_selection_str.split(',')] if solid_selection_str else None


def print_partition_format(partitions, indent_level):
    if not IS_WINDOWS and sys.stdout.isatty():
        _, tty_width = os.popen('stty size', 'r').read().split()
        screen_width = min(250, int(tty_width))
    else:
        screen_width = 250
    max_str_len = max(len(x) for x in partitions)
    spacing = 10
    num_columns = min(10, int((screen_width - indent_level) / (max_str_len + spacing)))
    column_width = int((screen_width - indent_level) / num_columns)
    prefix = ' ' * max(0, indent_level - spacing)
    lines = []
    for chunk in list(split_chunk(partitions, num_columns)):
        lines.append(prefix + ''.join(partition.rjust(column_width) for partition in chunk))

    return '\n' + '\n'.join(lines)


def split_chunk(l, n):
    for i in range(0, len(l), n):
        yield l[i : i + n]


def validate_partition_slice(partition_names, name, value):
    is_start = name == 'from'
    if value is None:
        return 0 if is_start else len(partition_names)
    if value not in partition_names:
        raise click.UsageError('invalid value {} for {}'.format(value, name))
    index = partition_names.index(value)
    return index if is_start else index + 1


@click.command(
    name='backfill',
    help='Backfill a partitioned pipeline.\n\n{instructions}'.format(
        instructions=get_partitioned_pipeline_instructions('backfill')
    ),
)
@pipeline_target_argument
@click.option(
    '--partitions',
    type=click.STRING,
    help='Comma-separated list of partition names that we want to backfill',
)
@click.option(
    '--partition-set',
    type=click.STRING,
    help='The name of the partition set over which we want to backfill.',
)
@click.option(
    '--all', type=click.STRING, help='Specify to select all partitions to backfill.',
)
@click.option(
    '--from',
    type=click.STRING,
    help=(
        'Specify a start partition for this backfill job'
        '\n\nExample: '
        'dagster pipeline backfill log_daily_stats --from 20191101'
    ),
)
@click.option(
    '--to',
    type=click.STRING,
    help=(
        'Specify an end partition for this backfill job'
        '\n\nExample: '
        'dagster pipeline backfill log_daily_stats --to 20191201'
    ),
)
@click.option('--tags', type=click.STRING, help='JSON string of tags to use for this pipeline run')
@click.option('--noprompt', is_flag=True)
def pipeline_backfill_command(**kwargs):
    execute_backfill_command(kwargs, click.echo, DagsterInstance.get())


def execute_backfill_command(cli_args, print_fn, instance):
    repo_location = get_repository_location_from_kwargs(cli_args, instance)
    external_repo = get_external_repository_from_repo_location(
        repo_location, cli_args.get('repository')
    )

    external_pipeline = get_external_pipeline_from_external_repo(
        external_repo, cli_args.get('pipeline'),
    )

    noprompt = cli_args.get('noprompt')

    pipeline_partition_set_names = {
        external_partition_set.name: external_partition_set
        for external_partition_set in external_repo.get_external_partition_sets()
        if external_partition_set.pipeline_name == external_pipeline.name
    }

    if not pipeline_partition_set_names:
        raise click.UsageError(
            'No partition sets found for pipeline `{}`'.format(external_pipeline.name)
        )
    partition_set_name = cli_args.get('partition_set')
    if not partition_set_name:
        if len(pipeline_partition_set_names) == 1:
            partition_set_name = next(iter(pipeline_partition_set_names.keys()))
        elif noprompt:
            raise click.UsageError('No partition set specified (see option `--partition-set`)')
        else:
            partition_set_name = click.prompt(
                'Select a partition set to use for backfill: {}'.format(
                    ', '.join(x for x in pipeline_partition_set_names.keys())
                )
            )

    partition_set = pipeline_partition_set_names.get(partition_set_name)

    if not partition_set:
        raise click.UsageError('No partition set found named `{}`'.format(partition_set_name))

    mode = partition_set.mode
    solid_selection = partition_set.solid_selection

    repo_handle = RepositoryHandle(
        repository_name=external_repo.name,
        repository_location_handle=repo_location.location_handle,
    )

    # Resolve partitions to backfill
    partition_names_or_error = repo_location.get_external_partition_names(
        repo_handle, partition_set_name,
    )

    if isinstance(partition_names_or_error, ExternalPartitionExecutionErrorData):
        raise DagsterBackfillFailedError(
            'Failure fetching partition names for {partition_set_name}: {error_message}'.format(
                partition_set_name=partition_set_name,
                error_message=partition_names_or_error.error.message,
            ),
            serialized_error_info=partition_names_or_error.error,
        )

    partition_names = gen_partition_names_from_args(
        partition_names_or_error.partition_names, cli_args
    )

    # Print backfill info
    print_fn('\n     Pipeline: {}'.format(external_pipeline.name))
    print_fn('Partition set: {}'.format(partition_set_name))
    print_fn('   Partitions: {}\n'.format(print_partition_format(partition_names, indent_level=15)))

    # Confirm and launch
    if noprompt or click.confirm(
        'Do you want to proceed with the backfill ({} partitions)?'.format(len(partition_names))
    ):

        print_fn('Launching runs... ')
        backfill_id = make_new_backfill_id()

        run_tags = merge_dicts(
            PipelineRun.tags_for_backfill_id(backfill_id), get_tags_from_args(cli_args),
        )

        for partition_name in partition_names:
            run_config_or_error = repo_location.get_external_partition_config(
                repo_handle, partition_set_name, partition_name
            )
            if isinstance(run_config_or_error, ExternalPartitionExecutionErrorData):
                raise DagsterBackfillFailedError(
                    'Failure fetching run config for partition {partition_name} in {partition_set_name}: {error_message}'.format(
                        partition_name=partition_name,
                        partition_set_name=partition_set_name,
                        error_message=run_config_or_error.error.message,
                    ),
                    serialized_error_info=run_config_or_error.error,
                )

            tags_or_error = repo_location.get_external_partition_tags(
                repo_handle, partition_set_name, partition_name
            )
            if isinstance(tags_or_error, ExternalPartitionExecutionErrorData):
                raise DagsterBackfillFailedError(
                    'Failure fetching tags for partition {partition_name} in {partition_set_name}: {error_message}'.format(
                        partition_name=partition_name,
                        partition_set_name=partition_set_name,
                        error_message=tags_or_error.error.message,
                    ),
                    serialized_error_info=tags_or_error.error,
                )
            run = _create_external_pipeline_run(
                instance=instance,
                repo_location=repo_location,
                external_repo=external_repo,
                external_pipeline=external_pipeline,
                run_config=run_config_or_error.run_config,
                mode=mode,
                preset=None,
                tags=merge_dicts(tags_or_error.tags, run_tags),
                solid_selection=frozenset(solid_selection) if solid_selection else None,
            )

            instance.launch_run(run.run_id, external_pipeline)
            # Remove once we can handle synchronous execution... currently limited by sqlite
            time.sleep(0.1)

        print_fn('Launched backfill job `{}`'.format(backfill_id))
    else:
        print_fn('Aborted!')


pipeline_cli = create_pipeline_cli_group()
