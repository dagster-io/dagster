from collections import defaultdict

import click

import check
from solidic.execution import (SolidExecutionContext, SolidPipeline, execute_pipeline)
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

    structured_flags = structure_flags(input_list)

    if structured_flags.single_argument or structured_flags.named_arguments:
        check.failed('only supporting named key arguments right now')

    input_arg_dicts = defaultdict(lambda: {})

    for nka in structured_flags.named_key_arguments:
        input_arg_dicts[nka.name][nka.key] = nka.value

    for result in execute_pipeline(
        create_dagster_context(), pipeline, input_arg_dicts, through_solids=through_list
    ):
        if not result.success:
            raise result.exception


def embedded_dagster_cli_main(argv, pipeline):
    check.list_param(argv, 'argv', of_type=str)
    check.inst_param(pipeline, 'pipeline', SolidPipeline)

    dagster_command_group = click.Group(name='dagster')
    dagster_command_group.add_command(embedded_dagster_graphviz_command)
    dagster_command_group.add_command(embedded_dagster_execute_command)
    dagster_command_group(argv[1:], obj={'pipeline': pipeline})
