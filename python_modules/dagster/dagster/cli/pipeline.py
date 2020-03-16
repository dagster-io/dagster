from __future__ import print_function

import os
import re
import sys
import textwrap
import time

import click
import six
import yaml

from dagster import (
    PipelineDefinition,
    RunConfig,
    check,
    execute_pipeline,
    execute_pipeline_with_preset,
)
from dagster.cli.load_handle import handle_for_pipeline_cli_args, handle_for_repo_cli_args
from dagster.core.definitions import ExecutionTargetHandle, Solid
from dagster.core.definitions.partition import PartitionScheduleDefinition
from dagster.core.definitions.pipeline import ExecutionSelector
from dagster.core.instance import DagsterInstance
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunStatus
from dagster.core.telemetry import telemetry_wrapper
from dagster.core.utils import make_new_backfill_id, make_new_run_id
from dagster.seven import IS_WINDOWS
from dagster.utils import DEFAULT_REPOSITORY_YAML_FILENAME, load_yaml_from_glob_list, merge_dicts
from dagster.utils.indenting_printer import IndentingPrinter
from dagster.visualize import build_graphviz_graph

from .config_scaffolder import scaffold_pipeline_config


def create_pipeline_cli_group():
    group = click.Group(name="pipeline")
    group.add_command(pipeline_list_command)
    group.add_command(pipeline_print_command)
    group.add_command(pipeline_graphviz_command)
    group.add_command(pipeline_execute_command)
    group.add_command(pipeline_backfill_command)
    group.add_command(pipeline_scaffold_command)
    return group


REPO_TARGET_WARNING = (
    'Can only use ONE of --repository-yaml/-y, --python-file/-f, --module-name/-m.'
)
REPO_ARG_NAMES = ['repository_yaml', 'module_name', 'fn_name', 'python_file']


def apply_click_params(command, *click_params):
    for click_param in click_params:
        command = click_param(command)
    return command


def repository_target_argument(f):
    return apply_click_params(
        f,
        click.option(
            '--repository-yaml',
            '-y',
            type=click.Path(exists=True),
            help=(
                'Path to config file. Defaults to ./{default_filename} if --python-file '
                'and --module-name are not specified'
            ).format(default_filename=DEFAULT_REPOSITORY_YAML_FILENAME),
        ),
        click.option(
            '--python-file',
            '-f',
            type=click.Path(exists=True),
            help='Specify python file where repository or pipeline function lives.',
        ),
        click.option(
            '--module-name', '-m', help='Specify module where repository or pipeline function lives'
        ),
        click.option('--fn-name', '-n', help='Function that returns either repository or pipeline'),
    )


def pipeline_target_command(f):
    # f = repository_config_argument(f)
    # nargs=-1 is used right now to make this argument optional
    # it can only handle 0 or 1 pipeline names
    # see .pipeline.create_pipeline_from_cli_args
    return apply_click_params(
        f,
        click.option(
            '--repository-yaml',
            '-y',
            type=click.Path(exists=True),
            help=(
                'Path to config file. Defaults to ./{default_filename} if --python-file '
                'and --module-name are not specified'
            ).format(default_filename=DEFAULT_REPOSITORY_YAML_FILENAME),
        ),
        click.argument('pipeline_name', nargs=-1),
        click.option('--python-file', '-f', type=click.Path(exists=True)),
        click.option('--module-name', '-m'),
        click.option('--fn-name', '-n'),
    )


@click.command(
    name='list',
    help="List the pipelines in a repository. {warning}".format(warning=REPO_TARGET_WARNING),
)
@repository_target_argument
def pipeline_list_command(**kwargs):
    return execute_list_command(kwargs, click.echo)


def execute_list_command(cli_args, print_fn):
    repository = handle_for_repo_cli_args(cli_args).build_repository_definition()

    title = 'Repository {name}'.format(name=repository.name)
    print_fn(title)
    print_fn('*' * len(title))
    first = True
    for pipeline in repository.get_all_pipelines():
        pipeline_title = 'Pipeline: {name}'.format(name=pipeline.name)

        if not first:
            print_fn('*' * len(pipeline_title))
        first = False

        print_fn(pipeline_title)
        if pipeline.description:
            print_fn('Description:')
            print_fn(format_description(pipeline.description, indent=' ' * 4))
        print_fn('Solids: (Execution Order)')
        for solid in pipeline.solids_in_topological_order:
            print_fn('    ' + solid.name)


def format_description(desc, indent):
    check.str_param(desc, 'desc')
    check.str_param(indent, 'indent')
    desc = re.sub(r'\s+', ' ', desc)
    dedented = textwrap.dedent(desc)
    wrapper = textwrap.TextWrapper(initial_indent='', subsequent_indent=indent)
    filled = wrapper.fill(dedented)
    return filled


def create_pipeline_from_cli_args(kwargs):
    return handle_for_pipeline_cli_args(kwargs).build_pipeline_definition()


def get_pipeline_instructions(command_name):
    return (
        'This commands targets a pipeline. The pipeline can be specified in a number of ways:'
        '\n\n1. dagster {command_name} <<pipeline_name>> (works if .{default_filename} exists)'
        '\n\n2. dagster {command_name} <<pipeline_name>> -y path/to/{default_filename}'
        '\n\n3. dagster {command_name} -f /path/to/file.py -n define_some_pipeline'
        '\n\n4. dagster {command_name} -m a_module.submodule  -n define_some_pipeline'
        '\n\n5. dagster {command_name} -f /path/to/file.py -n define_some_repo <<pipeline_name>>'
        '\n\n6. dagster {command_name} -m a_module.submodule -n define_some_repo <<pipeline_name>>'
    ).format(command_name=command_name, default_filename=DEFAULT_REPOSITORY_YAML_FILENAME)


def get_partitioned_pipeline_instructions(command_name):
    return (
        'This commands targets a partitioned pipeline. The pipeline and partition set must be '
        'defined in a repository, which can be specified in a number of ways:'
        '\n\n1. dagster {command_name} <<pipeline_name>> (works if .{default_filename} exists)'
        '\n\n2. dagster {command_name} <<pipeline_name>> -y path/to/{default_filename}'
        '\n\n3. dagster {command_name} -f /path/to/file.py -n define_some_repo <<pipeline_name>>'
        '\n\n4. dagster {command_name} -m a_module.submodule -n define_some_repo <<pipeline_name>>'
    ).format(command_name=command_name, default_filename=DEFAULT_REPOSITORY_YAML_FILENAME)


@click.command(
    name='print',
    help='Print a pipeline.\n\n{instructions}'.format(
        instructions=get_pipeline_instructions('print')
    ),
)
@click.option('--verbose', is_flag=True)
@pipeline_target_command
def pipeline_print_command(verbose, **cli_args):
    return execute_print_command(verbose, cli_args, click.echo)


def execute_print_command(verbose, cli_args, print_fn):
    pipeline = create_pipeline_from_cli_args(cli_args)

    if verbose:
        print_pipeline(pipeline, print_fn=print_fn)
    else:
        print_solids(pipeline, print_fn=print_fn)


def print_solids(pipeline, print_fn):
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    check.callable_param(print_fn, 'print_fn')

    printer = IndentingPrinter(indent_level=2, printer=print_fn)
    printer.line('Pipeline: {name}'.format(name=pipeline.name))

    printer.line('Solids:')
    for solid in pipeline.solids:
        with printer.with_indent():
            printer.line('Solid: {name}'.format(name=solid.name))


def print_pipeline(pipeline, print_fn):
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    check.callable_param(print_fn, 'print_fn')

    printer = IndentingPrinter(indent_level=2, printer=print_fn)
    printer.line('Pipeline: {name}'.format(name=pipeline.name))
    print_description(printer, pipeline.description)

    printer.line('Solids:')
    for solid in pipeline.solids:
        with printer.with_indent():
            print_solid(printer, solid)


def print_description(printer, desc):
    with printer.with_indent():
        if desc:
            printer.line('Description:')
            with printer.with_indent():
                printer.line(format_description(desc, printer.current_indent_str))


def print_solid(printer, solid):
    check.inst_param(solid, 'solid', Solid)
    printer.line('Solid: {name}'.format(name=solid.name))

    with printer.with_indent():
        print_inputs(printer, solid)

        printer.line('Outputs:')

        for name in solid.definition.output_dict.keys():
            printer.line(name)


def print_inputs(printer, solid):
    printer.line('Inputs:')
    for name in solid.definition.input_dict.keys():
        with printer.with_indent():
            printer.line('Input: {name}'.format(name=name))


@click.command(
    name='graphviz',
    help=(
        'Visualize a pipeline using graphviz. Must be installed on your system '
        '(e.g. homebrew install graphviz on mac). \n\n{instructions}'.format(
            instructions=get_pipeline_instructions('graphviz')
        )
    ),
)
@click.option('--only-solids', is_flag=True)
@pipeline_target_command
def pipeline_graphviz_command(only_solids, **kwargs):
    pipeline = create_pipeline_from_cli_args(kwargs)
    build_graphviz_graph(pipeline, only_solids).view(cleanup=True)


@click.command(
    name='execute',
    help='Execute a pipeline.\n\n{instructions}'.format(
        instructions=get_pipeline_instructions('execute')
    ),
)
@pipeline_target_command
@click.option(
    '-e',
    '--env',
    type=click.Path(exists=True),
    multiple=True,
    help=(
        'Specify one or more environment files. These can also be file patterns. '
        'If more than one environment file is captured then those files are merged. '
        'Files listed first take precendence. They will smash the values of subsequent '
        'files at the key-level granularity. If the file is a pattern then you must '
        'enclose it in double quotes'
        '\n\nExample: '
        'dagster pipeline execute pandas_hello_world -e "pandas_hello_world/*.yaml"'
        '\n\nYou can also specifiy multiple files:'
        '\n\nExample: '
        'dagster pipeline execute pandas_hello_world -e pandas_hello_world/solids.yaml '
        '-e pandas_hello_world/env.yaml'
    ),
)
@click.option(
    '-p',
    '--preset',
    type=click.STRING,
    help='Specify a preset to use for this pipeline. Presets are defined on pipelines under '
    'preset_defs.',
)
@click.option(
    '-d', '--mode', type=click.STRING, help='The name of the mode in which to execute the pipeline.'
)
@telemetry_wrapper
def pipeline_execute_command(env, preset, mode, **kwargs):
    check.invariant(isinstance(env, tuple))

    if preset:
        if env:
            raise click.UsageError('Can not use --preset with --env.')
        return execute_execute_command_with_preset(preset, kwargs, mode)

    env = list(env)

    execute_execute_command(env, kwargs, mode)


def execute_execute_command(env, cli_args, mode=None):
    pipeline = create_pipeline_from_cli_args(cli_args)
    return do_execute_command(pipeline, env, mode)


def execute_execute_command_with_preset(preset_name, cli_args, _mode):
    pipeline = handle_for_pipeline_cli_args(cli_args).build_pipeline_definition()
    cli_args.pop('pipeline_name')

    return execute_pipeline_with_preset(
        pipeline, preset_name, instance=DagsterInstance.get(), raise_on_error=False
    )


def do_execute_command(pipeline, env_file_list, mode=None):
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    env_file_list = check.opt_list_param(env_file_list, 'env_file_list', of_type=str)

    environment_dict = load_yaml_from_glob_list(env_file_list) if env_file_list else {}

    return execute_pipeline(
        pipeline,
        environment_dict=environment_dict,
        run_config=RunConfig(mode=mode),
        instance=DagsterInstance.get(),
        raise_on_error=False,
    )


@click.command(
    name='scaffold_config',
    help='Scaffold the config for a pipeline.\n\n{instructions}'.format(
        instructions=get_pipeline_instructions('scaffold_config')
    ),
)
@pipeline_target_command
@click.option('-p', '--print-only-required', default=False, is_flag=True)
def pipeline_scaffold_command(**kwargs):
    execute_scaffold_command(kwargs, click.echo)


def execute_scaffold_command(cli_args, print_fn):
    pipeline = create_pipeline_from_cli_args(cli_args)
    skip_non_required = cli_args['print_only_required']
    do_scaffold_command(pipeline, print_fn, skip_non_required)


def do_scaffold_command(pipeline, printer, skip_non_required):
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    check.callable_param(printer, 'printer')
    check.bool_param(skip_non_required, 'skip_non_required')

    config_dict = scaffold_pipeline_config(pipeline, skip_non_required=skip_non_required)
    yaml_string = yaml.dump(config_dict, default_flow_style=False)
    printer(yaml_string)


def gen_partitions_from_args(partition_set, kwargs):
    partition_selector_args = [
        bool(kwargs.get('all')),
        bool(kwargs.get('partitions')),
        (bool(kwargs.get('from')) or bool(kwargs.get('to'))),
    ]
    if sum(partition_selector_args) > 1:
        raise click.UsageError(
            'error, cannot use more than one of: `--all`, `--partitions`, `--from/--to`'
        )

    partitions = partition_set.get_partitions()

    if kwargs.get('all'):
        return partitions

    if kwargs.get('partitions'):
        selected_args = [s.strip() for s in kwargs.get('partitions').split(',') if s.strip()]
        selected_partitions = [
            partition for partition in partitions if partition.name in selected_args
        ]
        if len(selected_partitions) < len(selected_args):
            selected_names = [partition.name for partition in selected_partitions]
            unknown = [selected for selected in selected_args if selected not in selected_names]
            raise click.UsageError('Unknown partitions: {}'.format(unknown.join(', ')))
        return selected_partitions

    start = validate_partition_slice(partitions, 'from', kwargs.get('from'))
    end = validate_partition_slice(partitions, 'to', kwargs.get('to'))

    return partitions[start:end]


def get_backfill_priority_from_args(kwargs):
    if kwargs.get('celery_base_priority') is None:
        return None
    return int(kwargs.get('celery_base_priority'))


def print_partition_format(partitions, indent_level):
    if not IS_WINDOWS and sys.stdout.isatty():
        _, tty_width = os.popen('stty size', 'r').read().split()
        screen_width = min(250, int(tty_width))
    else:
        screen_width = 250
    max_str_len = max(len(x.name) for x in partitions)
    spacing = 10
    num_columns = min(10, int((screen_width - indent_level) / (max_str_len + spacing)))
    column_width = int((screen_width - indent_level) / num_columns)
    prefix = ' ' * max(0, indent_level - spacing)
    lines = []
    for chunk in list(split_chunk(partitions, num_columns)):
        lines.append(prefix + ''.join(partition.name.rjust(column_width) for partition in chunk))

    return '\n' + '\n'.join(lines)


def split_chunk(l, n):
    for i in range(0, len(l), n):
        yield l[i : i + n]


def validate_partition_slice(partitions, name, value):
    is_start = name == 'from'
    if value is None:
        return 0 if is_start else len(partitions)
    partition_names = [partition.name for partition in partitions]
    if value not in partition_names:
        raise click.UsageError('invalid value {} for {}'.format(value, name))
    index = partition_names.index(value)
    return index if is_start else index + 1


def get_partition_sets_for_handle(handle):
    check.inst_param(handle, 'handle', ExecutionTargetHandle)
    partitions_handle = handle.build_partitions_handle()
    scheduler_handle = handle.build_scheduler_handle()
    partition_sets = []
    if partitions_handle:
        partition_sets.extend(partitions_handle.get_partition_sets())
    if scheduler_handle:
        partition_sets.extend(
            [
                schedule_def.get_partition_set()
                for schedule_def in scheduler_handle.all_schedule_defs()
                if isinstance(schedule_def, PartitionScheduleDefinition)
            ]
        )
    return partition_sets


@click.command(
    name='backfill',
    help='Backfill a partitioned pipeline.\n\n{instructions}'.format(
        instructions=get_partitioned_pipeline_instructions('backfill')
    ),
)
@pipeline_target_command
@click.option(
    '-d', '--mode', type=click.STRING, help='The name of the mode in which to execute the pipeline.'
)
@click.option(
    '-p',
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
    '-a', '--all', type=click.STRING, help='Specify to select all partitions to backfill.',
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
@click.option(
    '--celery-base-priority',
    type=click.STRING,
    help=(
        'Specify a base run priority for all runs kicked off by this backfill job. Only meaningful '
        'if you are launching runs against a Celery executor on a messaging queue that supports '
        'priority.'
        '\n\nExample: '
        'dagster pipeline backfill log_daily_stats --celery-base-priority -3'
    ),
)
@click.option('--noprompt', is_flag=True)
def pipeline_backfill_command(**kwargs):
    execute_backfill_command(kwargs, click.echo)


def execute_backfill_command(cli_args, print_fn, instance=None):
    pipeline_name = cli_args.pop('pipeline_name')
    repo_args = {k: v for k, v in cli_args.items() if k in REPO_ARG_NAMES}
    if pipeline_name and not isinstance(pipeline_name, six.string_types):
        if len(pipeline_name) == 1:
            pipeline_name = pipeline_name[0]

    instance = instance or DagsterInstance.get()
    handle = handle_for_repo_cli_args(repo_args)
    repository = handle.build_repository_definition()
    noprompt = cli_args.get('noprompt')

    # check run launcher
    if not instance.run_launcher:
        raise click.UsageError(
            'A run launcher must be configured before running a backfill. You can configure a run '
            'launcher (e.g. dagster_graphql.launcher.RemoteDagitRunLauncher) in your instance '
            '`dagster.yaml` settings. See '
            'https://docs.dagster.io/latest/deploying/instance/ for more'
            'information.'
        )

    # Resolve pipeline
    if not pipeline_name and noprompt:
        raise click.UsageError('No pipeline specified')
    if not pipeline_name:
        pipeline_name = click.prompt(
            'Select a pipeline to backfill: {}'.format(', '.join(repository.pipeline_names))
        )
    repository = handle.build_repository_definition()
    if not repository.has_pipeline(pipeline_name):
        raise click.UsageError('No pipeline found named `{}`'.format(pipeline_name))

    pipeline = repository.get_pipeline(pipeline_name)

    # Resolve partition set
    all_partition_sets = get_partition_sets_for_handle(handle)
    pipeline_partition_sets = [x for x in all_partition_sets if x.pipeline_name == pipeline.name]
    if not pipeline_partition_sets:
        raise click.UsageError('No partition sets found for pipeline `{}`'.format(pipeline.name))
    partition_set_name = cli_args.get('partition_set')
    if not partition_set_name:
        if len(pipeline_partition_sets) == 1:
            partition_set_name = pipeline_partition_sets[0].name
        elif noprompt:
            raise click.UsageError('No partition set specified (see option `--partition-set`)')
        else:
            partition_set_name = click.prompt(
                'Select a partition set to use for backfill: {}'.format(
                    ', '.join(x.name for x in pipeline_partition_sets)
                )
            )
    partition_set = next((x for x in pipeline_partition_sets if x.name == partition_set_name), None)
    if not partition_set:
        raise click.UsageError('No partition set found named `{}`'.format(partition_set_name))

    # Resolve partitions to backfill
    partitions = gen_partitions_from_args(partition_set, cli_args)

    # Resolve priority
    celery_priority = get_backfill_priority_from_args(cli_args)

    # Print backfill info
    print_fn('\n     Pipeline: {}'.format(pipeline.name))
    print_fn('Partition set: {}'.format(partition_set.name))
    print_fn('   Partitions: {}\n'.format(print_partition_format(partitions, indent_level=15)))

    # Confirm and launch
    if noprompt or click.confirm(
        'Do you want to proceed with the backfill ({} partitions)?'.format(len(partitions))
    ):

        print_fn('Launching runs... ')
        backfill_id = make_new_backfill_id()
        run_tags = {'dagster/backfill': backfill_id}
        if celery_priority is not None:
            run_tags['dagster-celery/run_priority'] = celery_priority

        for partition in partitions:
            run = PipelineRun(
                pipeline_name=pipeline.name,
                run_id=make_new_run_id(),
                selector=ExecutionSelector(pipeline.name),
                environment_dict=partition_set.environment_dict_for_partition(partition),
                mode=cli_args.get('mode') or 'default',
                tags=merge_dicts(partition_set.tags_for_partition(partition), run_tags),
                status=PipelineRunStatus.NOT_STARTED,
            )
            instance.launch_run(run)
            # Remove once we can handle synchronous execution... currently limited by sqlite
            time.sleep(0.1)

        print_fn('Launched backfill job `{}`'.format(backfill_id))
    else:
        print_fn(' Aborted!')


pipeline_cli = create_pipeline_cli_group()
