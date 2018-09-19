from __future__ import print_function
import logging
import re
import textwrap

import click
import yaml

from dagster import (
    PipelineDefinition,
    check,
    config,
)

from dagster.core.definitions import ExecutionGraph, Solid
from dagster.core.execution import execute_pipeline_iterator
from dagster.core.errors import DagsterExecutionFailureReason
from dagster.graphviz import build_graphviz_graph
from dagster.utils import load_yaml_from_path
from dagster.utils.indenting_printer import IndentingPrinter

from .repository_config import (
    load_repository_from_file,
    repository_config_argument,
)


def create_pipeline_cli():
    group = click.Group(name="pipeline")
    group.add_command(list_command)
    group.add_command(print_command)
    group.add_command(graphviz_command)
    group.add_command(execute_command)
    return group


@click.command(name='list', help="list")
@repository_config_argument
def list_command(conf):
    repository = load_repository_from_file(conf).repository
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


def pipeline_from_conf(conf, name):
    repository = load_repository_from_file(conf).repository
    return repository.get_pipeline(name)


@click.command(name='print', help="print <<pipeline_name>>")
@repository_config_argument
@click.option('--verbose', is_flag=True)
@click.argument('name')
def print_command(conf, name, verbose):
    pipeline = pipeline_from_conf(conf, name)
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
    check.inst_param(solid, 'solid', Solid)
    printer.line('Solid: {name}'.format(name=solid.name))

    with printer.with_indent():
        print_inputs(printer, solid)

        printer.line('Outputs:')

        for output_def in solid.definition.output_defs:
            print(output_def.name)


def print_inputs(printer, solid):
    printer.line('Inputs:')
    for input_def in solid.definition.input_defs:
        with printer.with_indent():
            printer.line('Input: {name}'.format(name=input_def.name))


def format_argument_dict(arg_def_dict):
    return ', '.join(
        [
            '{name}: {type}'.format(name=name, type=arg_def.dagster_type.name)
            for name, arg_def in arg_def_dict.items()
        ]
    )


@click.command(name='graphviz', help="graphviz <<pipeline_name>>")
@repository_config_argument
@click.argument('name')
@click.option('--only-solids', is_flag=True)
def graphviz_command(conf, name, only_solids):
    pipeline = pipeline_from_conf(conf, name)
    build_graphviz_graph(pipeline, only_solids).view(cleanup=True)


LOGGING_DICT = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARN': logging.WARN,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL,
}


@click.command(name='execute', help="execute <<pipeline_name>>")
@repository_config_argument
@click.argument('name')
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
def execute_command(conf, name, env):
    pipeline = pipeline_from_conf(conf, name)
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
