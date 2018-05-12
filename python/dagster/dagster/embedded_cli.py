from collections import defaultdict

import click

import check
from solidic.errors import SolidExecutionFailureReason
from solidic.execution import (
    SolidExecutionContext, SolidPipeline, execute_pipeline, output_pipeline, OutputConfig
)
from solidic_utils.logging import (define_logger, INFO)

from .graphviz import build_graphviz_graph
from .structured_flags import structure_flags


def create_dagster_context():
    return SolidExecutionContext(loggers=[define_logger('dagster')], log_level=INFO)


@click.command(name='graphviz')
@click.pass_context
def embedded_dagster_graphviz_command(cxt):
    pipeline = check.inst(cxt.obj['pipeline'], SolidPipeline)
    build_graphviz_graph(pipeline).view(cleanup=True)


@click.command(name='output')
@click.option('--input', multiple=True)
@click.option('--output', multiple=True)
@click.pass_context
def embedded_dagster_output_command(cxt, input, output):  # pylint: disable=W0622
    check.tuple_param(input, 'input')
    check.tuple_param(output, 'output')

    input_list = list(input)
    output_list = list(output)
    pipeline = check.inst(cxt.obj['pipeline'], SolidPipeline)

    input_arg_dicts = construct_arg_dicts(input_list)
    output_arg_dicts = construct_arg_dicts(output_list)

    output_configs = []
    for output_name, output_arg_dict in output_arg_dicts.items():
        output_type = output_arg_dict.pop('type')
        output_configs.append(
            OutputConfig(name=output_name, output_type=output_type, output_args=output_arg_dict)
        )

    for result in output_pipeline(
        create_dagster_context(), pipeline, input_arg_dicts, output_configs
    ):
        if not result.success:
            if result.reason == SolidExecutionFailureReason.USER_CODE_ERROR:
                raise result.user_exception
            else:
                raise result.exception


@click.command(name='execute')
@click.option('--input', multiple=True)
@click.option('--through', multiple=True)
@click.pass_context
def embedded_dagster_execute_command(cxt, input, through):  # pylint: disable=W0622
    check.tuple_param(input, 'input')
    check.tuple_param(through, 'through')

    input_list = list(input)
    through_list = list(through)

    pipeline = check.inst(cxt.obj['pipeline'], SolidPipeline)

    input_arg_dicts = construct_arg_dicts(input_list)

    context = create_dagster_context()

    for result in execute_pipeline(context, pipeline, input_arg_dicts, through_solids=through_list):
        if not result.success:
            if result.reason == SolidExecutionFailureReason.USER_CODE_ERROR:
                raise result.user_exception
            else:
                raise result.exception


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
