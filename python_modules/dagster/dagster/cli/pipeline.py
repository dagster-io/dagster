from __future__ import print_function

import re
import textwrap

import click
import yaml

from dagster import InProcessExecutorConfig, PipelineDefinition, RunConfig, check, execute_pipeline
from dagster.cli.load_handle import handle_for_pipeline_cli_args, handle_for_repo_cli_args
from dagster.core.definitions import solids_in_topological_order, Solid
from dagster.utils import DEFAULT_REPOSITORY_YAML_FILENAME, load_yaml_from_glob_list
from dagster.utils.indenting_printer import IndentingPrinter
from dagster.visualize import build_graphviz_graph

from .config_scaffolder import scaffold_pipeline_config


def create_pipeline_cli_group():
    group = click.Group(name="pipeline")
    group.add_command(pipeline_list_command)
    group.add_command(pipeline_print_command)
    group.add_command(pipeline_graphviz_command)
    group.add_command(pipeline_execute_command)
    group.add_command(pipeline_scaffold_command)
    return group


REPO_TARGET_WARNING = (
    'Can only use ONE of --repository-yaml/-y, --python-file/-f, --module-name/-m.'
)


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
            type=click.STRING,
            help=(
                'Path to config file. Defaults to ./{default_filename} if --python-file '
                'and --module-name are not specified'
            ).format(default_filename=DEFAULT_REPOSITORY_YAML_FILENAME),
        ),
        click.option(
            '--python-file',
            '-f',
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
            type=click.STRING,
            help=(
                'Path to config file. Defaults to ./{default_filename} if --python-file '
                'and --module-name are not specified'
            ).format(default_filename=DEFAULT_REPOSITORY_YAML_FILENAME),
        ),
        click.argument('pipeline_name', nargs=-1),
        click.option('--python-file', '-f'),
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
        for solid in solids_in_topological_order(pipeline):
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
        print_pipeline(pipeline, full=True, print_fn=print_fn)
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


def print_pipeline(pipeline, full, print_fn):
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    check.bool_param(full, 'full')
    check.callable_param(print_fn, 'print_fn')

    printer = IndentingPrinter(indent_level=2, printer=print_fn)
    printer.line('Pipeline: {name}'.format(name=pipeline.name))
    print_description(printer, pipeline.description)

    if not full:
        return

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


def format_argument_dict(arg_def_dict):
    return ', '.join(
        [
            '{name}: {type}'.format(name=name, type=arg_def.runtime_type.name)
            for name, arg_def in arg_def_dict.items()
        ]
    )


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
    type=click.STRING,
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
@click.option('--raise-on-error/--no-raise-on-error', default=True)
@click.option(
    '-p',
    '--preset',
    type=click.STRING,
    help=(
        'Specify a preset to use for this pipeline. Presets are defined on the repo_config '
        'on RepositoryDefinition, typically managed under the config key in {default_filename}.'
    ).format(default_filename=DEFAULT_REPOSITORY_YAML_FILENAME),
)
@click.option('-d', '--mode', type=click.STRING)
def pipeline_execute_command(env, raise_on_error, preset, mode, **kwargs):
    check.invariant(isinstance(env, tuple))

    if preset:
        if env:
            raise click.UsageError('Can not use --preset with --env.')
        return execute_execute_command_with_preset(preset, raise_on_error, kwargs, mode)

    env = list(env)
    execute_execute_command(env, raise_on_error, kwargs, mode)


def execute_execute_command(env, raise_on_error, cli_args, mode=None):
    pipeline = create_pipeline_from_cli_args(cli_args)
    return do_execute_command(pipeline, env, raise_on_error, mode)


def execute_execute_command_with_preset(preset, raise_on_error, cli_args, _mode):
    pipeline = handle_for_pipeline_cli_args(cli_args).build_pipeline_definition()
    cli_args.pop('pipeline_name')

    kwargs = pipeline.get_preset(preset)
    kwargs['run_config'] = kwargs['run_config'].with_executor_config(
        InProcessExecutorConfig(raise_on_error=raise_on_error)
    )
    return execute_pipeline(**kwargs)


def do_execute_command(pipeline, env_file_list, raise_on_error, mode=None):
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    env_file_list = check.opt_list_param(env_file_list, 'env_file_list', of_type=str)

    environment_dict = load_yaml_from_glob_list(env_file_list) if env_file_list else {}

    return execute_pipeline(
        pipeline,
        environment_dict=environment_dict,
        run_config=RunConfig(
            mode=mode, executor_config=InProcessExecutorConfig(raise_on_error=raise_on_error)
        ),
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
    skip_optional = cli_args['print_only_required']
    do_scaffold_command(pipeline, print_fn, skip_optional)


def do_scaffold_command(pipeline, printer, skip_optional):
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    check.callable_param(printer, 'printer')
    check.bool_param(skip_optional, 'skip_optional')

    config_dict = scaffold_pipeline_config(pipeline, skip_optional=skip_optional)
    yaml_string = yaml.dump(config_dict, default_flow_style=False)
    printer(yaml_string)
