from collections import defaultdict
import json
import logging

import click

import check
from solidic.errors import SolidExecutionFailureReason
from solidic.execution import (
    SolidExecutionContext, SolidPipeline, execute_pipeline, output_pipeline
)
from solidic_utils.logging import define_logger

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
    return SolidExecutionContext(loggers=[define_logger('dagster')], log_level=log_level)


@click.command(name='graphviz')
@click.pass_context
def embedded_dagster_graphviz_command(cxt):
    pipeline = check.inst(cxt.obj['pipeline'], SolidPipeline)
    build_graphviz_graph(pipeline).view(cleanup=True)


@click.command(name='output')
@click.option('--json-config', type=click.Path(exists=True, dir_okay=False))
@click.option('--input', multiple=True)
@click.option('--output', multiple=True)
@click.option('--log-level', type=click.STRING, default='INFO')
@click.pass_context
def embedded_dagster_output_command(cxt, json_config, input, output, log_level):  # pylint: disable=W0622
    check.opt_str_param(json_config, 'json_config')
    check.opt_tuple_param(input, 'input')
    check.opt_tuple_param(output, 'output')
    check.opt_str_param(log_level, 'log_level')

    input_list = list(input)
    output_list = list(output)

    if json_config:
        config_object = json.load(open(json_config))
        input_arg_dicts = config_object['inputs']
        output_arg_dicts = config_object['outputs']
        log_level = config_object.get('log-level', 'INFO')
    else:
        input_arg_dicts = construct_arg_dicts(input_list)
        output_arg_dicts = _get_output_arg_dicts(output_list)

    pipeline = check.inst(cxt.obj['pipeline'], SolidPipeline)

    context = create_dagster_context(log_level=LOGGING_DICT[log_level])
    pipeline_iter = output_pipeline(
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
def embedded_dagster_execute_command(cxt, input, through, log_level):  # pylint: disable=W0622
    check.tuple_param(input, 'input')
    check.tuple_param(through, 'through')
    check.opt_str_param(log_level, 'log_level')

    input_list = list(input)
    through_list = list(through)

    pipeline = check.inst(cxt.obj['pipeline'], SolidPipeline)

    input_arg_dicts = construct_arg_dicts(input_list)

    context = create_dagster_context(log_level=LOGGING_DICT[log_level])

    process_results_for_console(
        execute_pipeline(context, pipeline, input_arg_dicts, through_solids=through_list), context
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


def embedded_dagster_cli_main(argv, pipeline):
    check.list_param(argv, 'argv', of_type=str)
    check.inst_param(pipeline, 'pipeline', SolidPipeline)

    dagster_command_group = click.Group(name='dagster')
    dagster_command_group.add_command(embedded_dagster_graphviz_command)
    dagster_command_group.add_command(embedded_dagster_execute_command)
    dagster_command_group.add_command(embedded_dagster_output_command)
    dagster_command_group(argv[1:], obj={'pipeline': pipeline})
