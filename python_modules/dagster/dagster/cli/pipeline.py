from collections import defaultdict
import logging
import os
import textwrap

import click
import yaml

from dagster import config as dagster_config
from dagster import check
from dagster.core.execution import (DagsterExecutionFailureReason, execute_pipeline_iterator)
from dagster.graphviz import build_graphviz_graph

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
            click.echo(format_description(pipeline.description))
        click.echo('Solids: (Execution Order)')
        for solid in pipeline.solid_graph.topological_solids:
            click.echo('    ' + solid.name)
        click.echo('*************')


def format_description(desc):
    dedented = textwrap.dedent(desc)
    indent = ' ' * 4
    wrapper = textwrap.TextWrapper(initial_indent=indent, subsequent_indent=indent)
    return wrapper.fill(dedented)


def set_pipeline(ctx, _arg, value):
    ctx.params['pipeline_config'] = ctx.find_object(Config).get_pipeline(value)


def pipeline_name_argument(f):
    return click.argument('pipeline_name', callback=set_pipeline, expose_value=False)(f)


@click.command(name='print', help="print <<pipeline_name>>")
@pipeline_name_argument
def print_command(pipeline_config):
    print_pipeline(pipeline_config.pipeline, full=True)


def print_pipeline(pipeline, full=True):
    indent = '    '
    print(
        'Pipeline: {name} Description: {desc}'.format(
            name=pipeline.name, desc=pipeline.description
        )
    )
    if not full:
        return
    for solid in pipeline.solids:
        print('{indent}Solid: {name}'.format(indent=indent, name=solid.name))
        print('{indent}Inputs:'.format(indent=indent * 2))
        for input_def in solid.inputs:
            if input_def.depends_on:
                print(
                    '{indent}Name: {name} (depends on {dep_name})'.format(
                        name=input_def.name, indent=indent * 3, dep_name=input_def.depends_on.name
                    )
                )
            else:
                print('{indent}Name: {name}'.format(name=input_def.name, indent=indent * 3))

            if input_def.sources:
                print('{indent}Sources:'.format(indent=indent * 4))
                for source_def in input_def.sources:
                    arg_list = format_argument_dict(source_def.argument_def_dict)
                    print(
                        '{indent}{input_name}({arg_list})'.format(
                            indent=indent * 5, input_name=source_def.source_type, arg_list=arg_list
                        )
                    )

        print('{indent}Output:'.format(indent=indent * 2))
        print('{indent}Materializations:'.format(indent=indent * 3))
        for materialization_def in solid.output.materializations:
            arg_list = format_argument_dict(materialization_def.argument_def_dict)
            print(
                '{indent}{name}({arg_list})'.format(
                    indent=indent * 4, name=materialization_def.name, arg_list=arg_list
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


def construct_environment(yml_config_object):
    sources = defaultdict(dict)
    sources_obj = check.dict_elem(yml_config_object['environment'], 'sources')
    for solid_name, args_yml in sources_obj.items():
        for input_name, source_yml in args_yml.items():
            sources[solid_name][input_name] = dagster_config.Source(
                name=source_yml['name'], args=source_yml['args']
            )

    materializations = []
    if 'materializations' in yml_config_object:
        materializations = [
            dagster_config.Materialization(solid=m['solid'], name=m['type'], args=m['args'])
            for m in check.list_elem(yml_config_object, 'materializations')
        ]

    return dagster_config.Environment(sources=sources, materializations=materializations)


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
@click.option('--from-solid', type=click.STRING, help="Solid to start execution from", default=None)
# @click.option('--log-level', type=click.Choice(LOGGING_DICT.keys()), default='INFO')
# def execute_command(pipeline_config, env, from_solid, log_level):
def execute_command(pipeline_config, env, from_solid):
    env_config = load_yaml_from_path(env)

    environment = construct_environment(env_config)

    pipeline_iter = execute_pipeline_iterator(
        pipeline_config.pipeline,
        environment=environment,
        from_solids=[from_solid] if from_solid else None,
    )

    process_results_for_console(pipeline_iter)


def process_results_for_console(pipeline_iter):
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

    print_metrics_to_console(results)


def print_metrics_to_console(results):
    for result in results:
        context = result.context
        metrics_of_solid = list(context.metrics_matching_context({'solid': result.name}))

        print('Metrics for {name}'.format(name=result.name))

        for input_def in result.solid.inputs:
            metrics_for_input = list(
                context.metrics_covering_context({
                    'solid': result.name,
                    'input': input_def.name,
                })
            )
            if metrics_for_input:
                print('    Input {input_name}'.format(input_name=input_def.name))
                for metric in metrics_for_input:
                    print(
                        '{indent}{metric_name}: {value}'.format(
                            indent=' ' * 8, metric_name=metric.metric_name, value=metric.value
                        )
                    )

        for metric in metrics_of_solid:
            print(
                '{indent}{metric_name}: {value}'.format(
                    indent=' ' * 4, metric_name=metric.metric_name, value=metric.value
                )
            )
