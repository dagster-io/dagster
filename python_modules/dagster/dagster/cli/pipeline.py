import logging
import os
import re
import textwrap

import click
import yaml

import dagster
from dagster import check
from dagster.core.execution import (DagsterExecutionFailureReason, execute_pipeline_iterator)
from dagster.graphviz import build_graphviz_graph
from dagster.utils.indenting_printer import IndentingPrinter

from .context import Config


def create_pipeline_cli():
    group = click.Group(name="pipeline")
    group.add_command(list_command)
    group.add_command(print_command)
    group.add_command(graphviz_command)
    group.add_command(execute_command)
    return group


@click.command(name='list', help="list")
@Config.pass_object
def list_command(config):
    pipeline_configs = config.create_pipelines()

    for pipeline_config in pipeline_configs:
        pipeline = pipeline_config.pipeline
        click.echo('Pipeline: {name}'.format(name=pipeline.name))
        if pipeline.description:
            click.echo('Description:')
            click.echo(format_description(pipeline.description, indent=' ' * 4))
        click.echo('Solids: (Execution Order)')
        for solid in pipeline.solid_graph.topological_solids:
            click.echo('    ' + solid.name)
        click.echo('*************')


def format_description(desc, indent):
    check.str_param(desc, 'desc')
    check.str_param(indent, 'indent')
    desc = re.sub(r'\s+', ' ', desc)
    dedented = textwrap.dedent(desc)
    wrapper = textwrap.TextWrapper(initial_indent='', subsequent_indent=indent)
    filled = wrapper.fill(dedented)
    return filled


def set_pipeline(ctx, _arg, value):
    ctx.params['pipeline_config'] = ctx.find_object(Config).get_pipeline(value)


def pipeline_name_argument(f):
    return click.argument('pipeline_name', callback=set_pipeline, expose_value=False)(f)


@click.command(name='print', help="print <<pipeline_name>>")
@click.option('--verbose', is_flag=True)
@pipeline_name_argument
def print_command(pipeline_config, verbose):
    if verbose:
        print_pipeline(pipeline_config.pipeline, full=True, print_fn=click.echo)
    else:
        print_solids(pipeline_config.pipeline, print_fn=click.echo)


def print_solids(pipeline, print_fn):
    check.inst_param(pipeline, 'pipeline', dagster.PipelineDefinition)
    check.callable_param(print_fn, 'print_fn')

    printer = IndentingPrinter(indent_level=2, printer=print_fn)
    printer.line('Pipeline: {name}'.format(name=pipeline.name))

    printer.line('Solids:')
    for solid in pipeline.solids:
        with printer.with_indent():
            printer.line('Solid: {name}'.format(name=solid.name))


def print_pipeline(pipeline, full, print_fn):
    check.inst_param(pipeline, 'pipeline', dagster.PipelineDefinition)
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

    printer.line('Args:')

    with printer.with_indent():
        for arg_name, arg_def in context_definition.argument_def_dict.items():
            printer.line('Arg: {name}'.format(name=arg_name))
            with printer.with_indent():
                printer.line('Type: {arg_type}'.format(arg_type=arg_def.dagster_type.name))

                print_description(printer, arg_def.description)


def print_solid(printer, solid):
    printer.line('Solid: {name}'.format(name=solid.name))

    with printer.with_indent():
        print_inputs(printer, solid)

        printer.line('Output:')

        if solid.output.materializations:
            printer.line('Materializations:')
            for materialization_def in solid.output.materializations:
                arg_list = format_argument_dict(materialization_def.argument_def_dict)
                with printer.with_indent():
                    printer.line(
                        '{name}({arg_list})'.format(
                            name=materialization_def.name, arg_list=arg_list
                        )
                    )


def print_inputs(printer, solid):
    printer.line('Inputs:')
    for input_def in solid.inputs:
        with printer.with_indent():
            if input_def.depends_on:
                printer.line(
                    'Input: {name} (depends on {dep_name})'.format(
                        name=input_def.name, dep_name=input_def.depends_on.name
                    )
                )
            else:
                printer.line('Input: {name}'.format(name=input_def.name))

            if input_def.sources:
                print_sources(printer, input_def.sources)


def print_sources(printer, sources):
    with printer.with_indent():
        printer.line('Sources:')
        with printer.with_indent():
            for source_def in sources:
                arg_list = format_argument_dict(source_def.argument_def_dict)
                printer.line(
                    '{input_name}({arg_list})'.format(
                        input_name=source_def.source_type,
                        arg_list=arg_list,
                    )
                )


def format_argument_dict(arg_def_dict):
    return ', '.join(
        [
            '{name}: {type}'.format(name=name, type=arg_def.dagster_type.name)
            for name, arg_def in arg_def_dict.items()
        ]
    )


@click.command(name='graphviz', help="graphviz <<pipeline_name>>")
@pipeline_name_argument
def graphviz_command(pipeline_config):
    build_graphviz_graph(pipeline_config.pipeline).view(cleanup=True)


def get_default_config_for_pipeline():
    ctx = click.get_current_context()
    pipeline_config = ctx.params['pipeline_config']
    module_path = os.path.dirname(pipeline_config.module.__file__)
    return os.path.join(module_path, 'env.yml')


LOGGING_DICT = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARN': logging.WARN,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL,
}


def load_yaml_from_path(path):
    check.str_param(path, 'path')
    with open(path, 'r') as ff:
        return yaml.load(ff)


@click.command(name='execute', help="execute <<pipeline_name>>")
@pipeline_name_argument
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
    default=get_default_config_for_pipeline,
    help="Path to environment file. Defaults to ./PIPELINE_DIR/env.yml."
)
def execute_command(pipeline_config, env):
    do_execute_command(pipeline_config.pipeline, env, print)


def do_execute_command(pipeline, env, printer):
    check.inst_param(pipeline, 'pipeline', dagster.PipelineDefinition)
    check.str_param(env, 'env')
    check.callable_param(printer, 'printer')

    env_config = load_yaml_from_path(env)

    environment = dagster.config.construct_environment(env_config)

    pipeline_iter = execute_pipeline_iterator(pipeline, environment)

    process_results_for_console(pipeline_iter, printer)


def process_results_for_console(pipeline_iter, printer):
    results = []

    for result in pipeline_iter:
        if not result.success:
            if result.reason == DagsterExecutionFailureReason.USER_CODE_ERROR:
                raise result.user_exception
            elif result.reason == DagsterExecutionFailureReason.EXPECTATION_FAILURE:
                for expectation_result in result.failed_expectation_results:
                    result.context.error(expectation_result.message, solid=result.solid.name)
                click_context = click.get_current_context()
                click_context.exit(1)
        results.append(result)

    print_metrics_to_console(results, printer)


def print_metrics_to_console(results, printer):
    for result in results:
        context = result.context
        metrics_of_solid = list(context.metrics_matching_context({'solid': result.name}))

        printer('Metrics for {name}'.format(name=result.name))

        for input_def in result.solid.inputs:
            metrics_for_input = list(
                context.metrics_covering_context({
                    'solid': result.name,
                    'input': input_def.name,
                })
            )
            if metrics_for_input:
                printer('    Input {input_name}'.format(input_name=input_def.name))
                for metric in metrics_for_input:
                    printer(
                        '{indent}{metric_name}: {value}'.format(
                            indent=' ' * 8, metric_name=metric.metric_name, value=metric.value
                        )
                    )

        for metric in metrics_of_solid:
            printer(
                '{indent}{metric_name}: {value}'.format(
                    indent=' ' * 4, metric_name=metric.metric_name, value=metric.value
                )
            )
