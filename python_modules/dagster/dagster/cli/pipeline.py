from __future__ import print_function
import logging
import re
import textwrap

import click

from dagster import (
    RepositoryDefinition,
    PipelineDefinition,
    check,
    config,
)

from dagster.core.definitions import ExecutionGraph
from dagster.core.execution import execute_pipeline_iterator
from dagster.graphviz import build_graphviz_graph
from dagster.utils import load_yaml_from_path
from dagster.utils.indenting_printer import IndentingPrinter

from .dynamic_loader import (
    PipelineTargetInfo,
    RepositoryTargetInfo,
    load_pipeline_from_target_info,
    load_repository_from_file,
    load_repository_from_target_info,
    pipeline_target_command,
    repository_config_argument,
    load_target_info_from_kwargs,
)


def create_pipeline_cli():
    group = click.Group(name="pipeline")
    group.add_command(list_command)
    group.add_command(print_command)
    group.add_command(graphviz_command)
    group.add_command(execute_command)
    return group


REPO_TARGET_WARNING = (
    'Can only use ONE of --repository-yaml/-y, --python-file/-f, --module-name/-m.'
)


@click.command(
    name='list',
    help="List the pipelines in a repository. {warning}".format(warning=REPO_TARGET_WARNING),
)
@repository_config_argument
def list_command(**kwargs):
    repository_target_info = load_target_info_from_kwargs(kwargs)
    repository = load_repository_from_target_info(repository_target_info)

    title = 'Repository {name}'.format(name=repository.name)
    click.echo(title)
    click.echo('*' * len(title))
    first = True
    for pipeline in repository.get_all_pipelines():
        pipeline_title = 'Pipeline: {name}'.format(name=pipeline.name)

        if not first:
            click.echo('*' * len(pipeline_title))
        first = False

        click.echo(pipeline_title)
        if pipeline.description:
            click.echo('Description:')
            click.echo(format_description(pipeline.description, indent=' ' * 4))
        click.echo('Solids: (Execution Order)')
        solid_graph = ExecutionGraph(pipeline, pipeline.solids, pipeline.dependency_structure)
        for solid in solid_graph.topological_solids:
            click.echo('    ' + solid.name)


def format_description(desc, indent):
    check.str_param(desc, 'desc')
    check.str_param(indent, 'indent')
    desc = re.sub(r'\s+', ' ', desc)
    dedented = textwrap.dedent(desc)
    wrapper = textwrap.TextWrapper(initial_indent='', subsequent_indent=indent)
    filled = wrapper.fill(dedented)
    return filled


def create_pipeline_from_cli_args(kwargs):
    check.dict_param(kwargs, 'kwargs')

    pipeline_names = list(kwargs['pipeline_name'])

    if not pipeline_names:
        pipeline_name = None
    elif len(pipeline_names) == 1:
        pipeline_name = pipeline_names[0]
    else:
        check.failed('Can only handle zero or one pipeline args')

    if kwargs['pipeline_name'] and kwargs['repository_yaml'] is None:
        repository_yaml = 'repository.yml'
    else:
        repository_yaml = kwargs['repository_yaml']

    return load_pipeline_from_target_info(
        PipelineTargetInfo(
            repository_yaml=repository_yaml,
            pipeline_name=pipeline_name,
            python_file=kwargs['python_file'],
            pipeline_fn_name=kwargs['pipeline_fn_name'],
            module_name=kwargs['module_name'],
            repository_fn_name=kwargs['repository_fn_name'],
        )
    )


def get_pipeline_instructions(command_name):
    return (
        'This commands targets a pipeline. The pipeline can be specified in a number of ways:'
        '\n\n1. dagster {command_name} <<pipeline_name>> (works if .repository.yml exists)'
        '\n\n2. dagster {command_name} <<pipeline_name>> -y path/to/repository.yml'
        '\n\n3. dagster {command_name} -f /path/to/file.py -p define_some_pipeline'
        '\n\n4. dagster {command_name} -m a_module.submodule  -p define_some_pipeline'
        '\n\n5. dagster {command_name} -f /path/to/file.py -r define_some_repo -p pipeline_name'
        '\n\n6. dagster {command_name} -m a_module.submodule  -r define_some_repo -p pipeline_name'
    ).format(command_name=command_name)


@click.command(
    name='print',
    help='Print a pipeline.\n\n{instructions}'.format(
        instructions=get_pipeline_instructions('print')
    ),
)
@click.option('--verbose', is_flag=True)
@pipeline_target_command
def print_command(verbose, **kwargs):
    pipeline = create_pipeline_from_cli_args(kwargs)

    if verbose:
        print_pipeline(pipeline, full=True, print_fn=click.echo)
    else:
        print_solids(pipeline, print_fn=click.echo)


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

    with printer.with_indent():
        printer.line('Context Definitions:')

        with printer.with_indent():

            for context_name, context_definition in pipeline.context_definitions.items():
                print_context_definition(printer, context_name, context_definition)

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


def print_context_definition(printer, context_name, context_definition):
    printer.line('Name: {context_name}'.format(context_name=context_name))

    print_description(printer, context_definition.description)

    printer.line(
        'Type: {config_type}'.format(config_type=context_definition.config_def.config_type.name)
    )


def print_solid(printer, solid):
    printer.line('Solid: {name}'.format(name=solid.name))

    with printer.with_indent():
        print_inputs(printer, solid)

        printer.line('Outputs:')

        for output_def in solid.output_defs:
            print(output_def.name)


def print_inputs(printer, solid):
    printer.line('Inputs:')
    for input_def in solid.input_defs:
        with printer.with_indent():
            printer.line('Input: {name}'.format(name=input_def.name))


def format_argument_dict(arg_def_dict):
    return ', '.join(
        [
            '{name}: {type}'.format(name=name, type=arg_def.dagster_type.name)
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
def graphviz_command(only_solids, **kwargs):
    pipeline_target_info = PipelineTargetInfo(**kwargs)
    pipeline = load_pipeline_from_target_info(pipeline_target_info)
    build_graphviz_graph(pipeline, only_solids).view(cleanup=True)


LOGGING_DICT = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARN': logging.WARN,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL,
}


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
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        resolve_path=True,
    ),
)
def execute_command(env, **kwargs):
    pipeline_target_info = PipelineTargetInfo(**kwargs)
    pipeline = load_pipeline_from_target_info(pipeline_target_info)
    do_execute_command(pipeline, env, print)


def do_execute_command(pipeline, env, printer):
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    check.str_param(env, 'env')
    check.callable_param(printer, 'printer')

    env_config = load_yaml_from_path(env)

    environment = config.construct_environment(env_config)

    pipeline_iter = execute_pipeline_iterator(pipeline, environment)

    process_results_for_console(pipeline_iter)


def process_results_for_console(pipeline_iter):
    results = []

    for result in pipeline_iter:
        if not result.success:
            result.reraise_user_error()
        results.append(result)

    return results
