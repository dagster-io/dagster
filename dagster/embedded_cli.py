from collections import defaultdict
import json
import logging

import click

from dagster import check
from dagster.core.errors import SolidExecutionFailureReason
from dagster.core.execution import (
    DagsterExecutionContext, DagsterPipeline, execute_pipeline_iterator, output_pipeline_iterator
)
from dagster.utils.logging import define_logger

from .graphviz import build_graphviz_graph
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


def _pipeline_named(pipelines, name):
    for pipeline in pipelines:
        if pipeline.name == name:
            return pipeline

    check.failed('Could not find pipeline named {name}'.format(name=name))


@click.command(name='pipelines')
@click.pass_context
def embedded_dagster_multi_pipeline_pipelines_command(cxt):
    pipelines = check.inst(cxt.obj['pipelines'], list)
    check.list_param(pipelines, 'pipelines', of_type=DagsterPipeline)

    indent = '    '
    print('*** All Pipelines ***')
    for pipeline in pipelines:
        print('Pipeline: {name}'.format(name=pipeline.name))
        for solid in pipeline.solids:
            print('{indent}Solid: {name}'.format(indent=indent, name=solid.name))
            print('{indent}Inputs:'.format(indent=indent * 2))
            for input_def in solid.inputs:
                arg_list = format_argument_dict(input_def.argument_def_dict)
                print(
                    '{indent}{input_name}({arg_list})'.format(
                        indent=indent * 3, input_name=input_def.name, arg_list=arg_list
                    )
                )

            print('{indent}Outputs:'.format(indent=indent * 2))
            for output_def in solid.outputs:
                arg_list = format_argument_dict(output_def.argument_def_dict)
                print(
                    '{indent}{output_name}({arg_list})'.format(
                        indent=indent * 3, output_name=output_def.name, arg_list=arg_list
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
@click.option('--json-config', type=click.Path(exists=True, dir_okay=False))
@click.option('--input', multiple=True)
@click.option('--output', multiple=True)
@click.option('--log-level', type=click.STRING, default='INFO')
@click.pass_context
def embedded_dagster_multi_pipeline_output_command(
    cxt,
    pipeline_name,
    json_config,
    input,  # pylint: disable=W0622
    output,
    log_level
):
    check.str_param(pipeline_name, 'pipeline_name')
    pipelines = check.inst(cxt.obj['pipelines'], list)
    check.list_param(pipelines, 'pipelines', of_type=DagsterPipeline)
    pipeline = _pipeline_named(pipelines, pipeline_name)
    run_pipeline_output_command(json_config, input, output, log_level, pipeline)


@click.command(name='output')
@click.option('--json-config', type=click.Path(exists=True, dir_okay=False))
@click.option('--input', multiple=True)
@click.option('--output', multiple=True)
@click.option('--log-level', type=click.STRING, default='INFO')
@click.pass_context
def embedded_dagster_single_pipeline_output_command(cxt, json_config, input, output, log_level):  # pylint: disable=W0622
    pipeline = check.inst(cxt.obj['pipeline'], DagsterPipeline)
    run_pipeline_output_command(json_config, input, output, log_level, pipeline)


def run_pipeline_output_command(json_config, input_tuple, output, log_level, pipeline):
    check.opt_str_param(json_config, 'json_config')
    check.opt_tuple_param(input_tuple, 'input_tuple')
    check.opt_tuple_param(output, 'output')
    check.opt_str_param(log_level, 'log_level')

    input_list = list(input_tuple)
    output_list = list(output)

    if json_config:
        config_object = json.load(open(json_config))
        input_arg_dicts = config_object['inputs']
        output_arg_dicts = config_object['outputs']
        log_level = config_object.get('log-level', 'INFO')
    else:
        input_arg_dicts = construct_arg_dicts(input_list)
        output_arg_dicts = _get_output_arg_dicts(output_list)

    context = create_dagster_context(log_level=LOGGING_DICT[log_level])
    pipeline_iter = output_pipeline_iterator(
        context, pipeline, input_arg_dicts, output_arg_dicts=output_arg_dicts
    )

    process_results_for_console(pipeline_iter, context)


def process_results_for_console(pipeline_iter, context):
    results = []
    for result in pipeline_iter:
        if not result.success:
            if result.reason == SolidExecutionFailureReason.USER_CODE_ERROR:
                raise result.user_exception
            else:
                raise result.exception

        results.append(result)

    print_metrics_to_console(results, context)


def _get_output_arg_dicts(output_list):
    flat_output_arg_dicts = construct_arg_dicts(output_list)

    output_arg_dicts = defaultdict(lambda: {})

    for output_name, output_arg_dict in flat_output_arg_dicts.items():
        check.invariant('type' in output_arg_dict, 'must specify output type')
        output_type = output_arg_dict.pop('type')
        output_arg_dicts[output_name][output_type] = output_arg_dict

    return output_arg_dicts


@click.command(name='execute')
@click.option('--input', multiple=True)
@click.option('--through', multiple=True)
@click.option('--log-level', type=click.STRING, default='INFO')
@click.pass_context
def embedded_dagster_single_pipeline_execute_command(cxt, input, through, log_level):  # pylint: disable=W0622
    pipeline = check.inst(cxt.obj['pipeline'], DagsterPipeline)
    run_pipeline_execute_command(input, through, log_level, pipeline)


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
    run_pipeline_execute_command(input, through, log_level, pipeline)


def run_pipeline_execute_command(input_tuple, through, log_level, pipeline):
    check.tuple_param(input_tuple, 'input_tuple')
    check.tuple_param(through, 'through')
    check.opt_str_param(log_level, 'log_level')

    input_list = list(input_tuple)
    through_list = list(through)

    input_arg_dicts = construct_arg_dicts(input_list)

    context = create_dagster_context(log_level=LOGGING_DICT[log_level])

    process_results_for_console(
        execute_pipeline_iterator(context, pipeline, input_arg_dicts, through_solids=through_list),
        context
    )


def print_metrics_to_console(results, context):
    for result in results:
        metrics_of_solid = list(context.metrics_matching_context({'solid': result.name}))

        print('Metrics for {name}'.format(name=result.name))

        for input_def in result.solid.inputs:
            metrics_for_input = list(
                context.metrics_covering_context({
                    'solid': result.name,
                    'input': input_def.name
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
    dagster_command_group(argv[1:], obj={'pipeline': pipeline})


def embedded_dagster_multi_pipeline_cli_main(argv, pipelines):
    check.list_param(argv, 'argv', of_type=str)
    check.list_param(pipelines, 'pipelines', of_type=DagsterPipeline)

    for pipeline in pipelines:
        check.param_invariant(bool(pipeline.name), 'pipelines', 'all pipelines must have names')

    dagster_command_group = click.Group(name='dagster')
    dagster_command_group.add_command(embedded_dagster_multi_pipeline_graphviz_command)
    dagster_command_group.add_command(embedded_dagster_multi_pipeline_pipelines_command)
    dagster_command_group.add_command(embedded_dagster_multi_pipeline_output_command)
    dagster_command_group.add_command(embedded_dagster_multi_pipeline_execute_command)

    dagster_command_group(argv[1:], obj={'pipelines': pipelines})
