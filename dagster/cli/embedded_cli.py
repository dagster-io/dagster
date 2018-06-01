from collections import defaultdict
import logging

import click

from dagster import check
from dagster import config
from dagster.core.errors import DagsterExecutionFailureReason
from dagster.core.execution import (
    DagsterExecutionContext,
    DagsterPipeline,
    execute_pipeline_iterator,
    materialize_pipeline_iterator,
    create_pipeline_env_from_arg_dicts,
)
from dagster.utils.logging import define_logger

from dagster.graphviz import build_graphviz_graph
from .structured_flags import structure_flags

LOGGING_DICT = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARN': logging.WARN,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL,
}


def create_dagster_context(log_level):
    return DagsterExecutionContext(loggers=[define_logger('dagster')], log_level=log_level)


@click.command(name='graphviz')
@click.pass_context
def embedded_dagster_single_pipeline_graphviz_command(cxt):
    pipeline = check.inst(cxt.obj['pipeline'], DagsterPipeline)
    build_graphviz_graph(pipeline).view(cleanup=True)


@click.command(name='meta')
@click.pass_context
def embedded_dagster_single_pipeline_meta_command(cxt):
    pipeline = check.inst(cxt.obj['pipeline'], DagsterPipeline)
    print_pipeline(pipeline)


def _pipeline_named(pipelines, name):
    for pipeline in pipelines:
        if pipeline.name == name:
            return pipeline

    check.failed('Could not find pipeline named {name}'.format(name=name))


@click.command(name='pipelines')
@click.option('--full/--bare', default=False)
@click.pass_context
def embedded_dagster_multi_pipeline_pipelines_command(cxt, full):
    check.bool_param(full, 'full')
    pipelines = check.inst(cxt.obj['pipelines'], list)
    check.list_param(pipelines, 'pipelines', of_type=DagsterPipeline)

    print('*** All Pipelines ***')
    for pipeline in pipelines:
        print_pipeline(pipeline, full=full)


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
                    indent=indent * 4,
                    name=materialization_def.materialization_type,
                    arg_list=arg_list
                )
            )


def format_argument_dict(arg_def_dict):
    return ', '.join(
        [
            '{name}: {type}'.format(name=name, type=arg_type.name)
            for name, arg_type in arg_def_dict.items()
        ]
    )


@click.command(name='graphviz')
@click.argument('pipeline_name')
@click.pass_context
def embedded_dagster_multi_pipeline_graphviz_command(cxt, pipeline_name):
    pipelines = check.inst(cxt.obj['pipelines'], list)
    check.list_param(pipelines, 'pipelines', of_type=DagsterPipeline)
    pipeline = _pipeline_named(pipelines, pipeline_name)
    check.str_param(pipeline_name, 'pipeline_name')

    build_graphviz_graph(pipeline).view(cleanup=True)


@click.command(name='output')
@click.argument('pipeline_name')
@click.option('--input', multiple=True)
@click.option('--output', multiple=True)
@click.option('--log-level', type=click.STRING, default='INFO')
@click.pass_context
def embedded_dagster_multi_pipeline_output_command(
    cxt,
    pipeline_name,
    input,  # pylint: disable=W0622
    output,
    log_level
):
    check.str_param(pipeline_name, 'pipeline_name')
    pipelines = check.inst(cxt.obj['pipelines'], list)
    check.list_param(pipelines, 'pipelines', of_type=DagsterPipeline)
    pipeline = _pipeline_named(pipelines, pipeline_name)
    run_pipeline_output_command(input, output, log_level, pipeline)


@click.command(name='output')
@click.option('--input', multiple=True)
@click.option('--output', multiple=True)
@click.option('--log-level', type=click.STRING, default='INFO')
@click.pass_context
def embedded_dagster_single_pipeline_output_command(cxt, input, output, log_level):  # pylint: disable=W0622
    pipeline = check.inst(cxt.obj['pipeline'], DagsterPipeline)
    run_pipeline_output_command(input, output, log_level, pipeline)


def run_pipeline_output_command(input_tuple, output, log_level, pipeline):
    check.opt_tuple_param(input_tuple, 'input_tuple')
    check.opt_tuple_param(output, 'output')
    check.opt_str_param(log_level, 'log_level')

    input_list = list(input_tuple)
    output_list = list(output)

    input_arg_dicts = construct_arg_dicts(input_list)
    materializations = _get_materializations(output_list)

    context = create_dagster_context(log_level=LOGGING_DICT[log_level])
    pipeline_iter = materialize_pipeline_iterator(
        context,
        pipeline,
        environment=create_pipeline_env_from_arg_dicts(pipeline, input_arg_dicts),
        materializations=materializations,
    )

    process_results_for_console(pipeline_iter, context)


def process_results_for_console(pipeline_iter, context):
    results = []
    for result in pipeline_iter:
        if not result.success:
            if result.reason == DagsterExecutionFailureReason.USER_CODE_ERROR:
                raise result.user_exception
            else:
                raise result.exception

        results.append(result)

    print_metrics_to_console(results, context)


def _get_materializations(output_list):
    flat_output_arg_dicts = construct_arg_dicts(output_list)

    materializations = []

    for output_name, output_arg_dict in flat_output_arg_dicts.items():
        check.invariant('type' in output_arg_dict, 'must specify output type')
        materialization_name = output_arg_dict.pop('type')

        materializations.append(
            config.Materialization(
                solid=output_name,
                materialization_type=materialization_name,
                args=output_arg_dict,
            )
        )

    return materializations


@click.command(name='execute')
@click.option('--input', multiple=True)
@click.option('--through', multiple=True)
@click.option('--log-level', type=click.STRING, default='INFO')
@click.pass_context
def embedded_dagster_single_pipeline_execute_command(cxt, input, through, log_level):  # pylint: disable=W0622
    pipeline = check.inst(cxt.obj['pipeline'], DagsterPipeline)
    context = create_dagster_context(log_level=LOGGING_DICT[log_level])
    run_pipeline_execute_command(input, through, log_level, pipeline, context)


@click.command(name='execute')
@click.argument('pipeline_name')
@click.option('--input', multiple=True)
@click.option('--through', multiple=True)
@click.option('--log-level', type=click.STRING, default='INFO')
@click.pass_context
def embedded_dagster_multi_pipeline_execute_command(cxt, pipeline_name, input, through, log_level):  # pylint: disable=W0622
    check.str_param(pipeline_name, 'pipeline_name')
    pipelines = check.inst(cxt.obj['pipelines'], list)
    check.list_param(pipelines, 'pipelines', of_type=DagsterPipeline)
    pipeline = _pipeline_named(pipelines, pipeline_name)
    if 'execution_context' in cxt.obj:
        context = cxt.obj['execution_context']
    else:
        context = create_dagster_context(log_level=LOGGING_DICT[log_level])
    run_pipeline_execute_command(input, through, log_level, pipeline, context)


def run_pipeline_execute_command(input_tuple, through, log_level, pipeline, context):
    check.tuple_param(input_tuple, 'input_tuple')
    check.tuple_param(through, 'through')
    check.opt_str_param(log_level, 'log_level')

    input_list = list(input_tuple)
    through_list = list(through)

    input_arg_dicts = construct_arg_dicts(input_list)

    process_results_for_console(
        execute_pipeline_iterator(
            context,
            pipeline,
            environment=create_pipeline_env_from_arg_dicts(pipeline, input_arg_dicts),
            through_solids=through_list,
        ), context
    )


def print_metrics_to_console(results, context):
    for result in results:
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


def construct_arg_dicts(input_list):
    structured_flags = structure_flags(input_list)

    if structured_flags is None:
        return {}

    if structured_flags.single_argument or structured_flags.named_arguments:
        check.failed('only supporting named key arguments right now')

    input_arg_dicts = defaultdict(lambda: {})

    for nka in structured_flags.named_key_arguments:
        input_arg_dicts[nka.name][nka.key] = nka.value
    return input_arg_dicts


def embedded_dagster_single_pipeline_cli_main(argv, pipeline):
    check.list_param(argv, 'argv', of_type=str)
    check.inst_param(pipeline, 'pipeline', DagsterPipeline)

    dagster_command_group = click.Group(name='dagster')
    dagster_command_group.add_command(embedded_dagster_single_pipeline_graphviz_command)
    dagster_command_group.add_command(embedded_dagster_single_pipeline_execute_command)
    dagster_command_group.add_command(embedded_dagster_single_pipeline_output_command)
    dagster_command_group.add_command(embedded_dagster_single_pipeline_meta_command)
    dagster_command_group(argv[1:], obj={'pipeline': pipeline})


def embedded_dagster_multi_pipeline_cli_main(argv, pipelines, execution_context=None):
    check.list_param(argv, 'argv', of_type=str)
    check.list_param(pipelines, 'pipelines', of_type=DagsterPipeline)

    for pipeline in pipelines:
        check.param_invariant(bool(pipeline.name), 'pipelines', 'all pipelines must have names')

    dagster_command_group = click.Group(name='dagster')
    dagster_command_group.add_command(embedded_dagster_multi_pipeline_graphviz_command)
    dagster_command_group.add_command(embedded_dagster_multi_pipeline_pipelines_command)
    dagster_command_group.add_command(embedded_dagster_multi_pipeline_output_command)
    dagster_command_group.add_command(embedded_dagster_multi_pipeline_execute_command)

    obj = {
        'pipelines': pipelines,
    }

    if execution_context is not None:
        obj['execution_context'] = execution_context

    dagster_command_group(argv[1:], obj=obj)
