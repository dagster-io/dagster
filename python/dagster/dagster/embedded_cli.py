from collections import defaultdict

import click

import check
from solidic.execution import (SolidExecutionContext, SolidPipeline, execute_pipeline)

from .graphviz import build_graphviz_graph
from .structured_flags import structure_flags


@click.command(name='graphviz')
@click.pass_context
def embedded_dagster_graphviz_command(cxt):
    pipeline = check.inst(cxt.obj['pipeline'], SolidPipeline)
    build_graphviz_graph(pipeline).view(cleanup=True)


@click.command(name='execute')
@click.option('--input', multiple=True)
@click.option('--output', multiple=True)
@click.pass_context
def embedded_dagster_execute_command(cxt, input, output):  # pylint: disable=W0622
    check.tuple_param(input, 'input')
    check.tuple_param(output, 'output')

    input_list = list(input)
    output_list = list(output)

    pipeline = check.inst(cxt.obj['pipeline'], SolidPipeline)

    structured_flags = structure_flags(input_list)

    if structured_flags.single_argument or structured_flags.named_arguments:
        check.failed('only supporting named key arguments right now')

    input_arg_dicts = defaultdict(lambda: {})

    for nka in structured_flags.named_key_arguments:
        input_arg_dicts[nka.name][nka.key] = nka.value

    # input_arg_dicts = {'qhp_json_input': {'path': 'providers-771.json'}}

    for result in execute_pipeline(
        SolidExecutionContext(), pipeline, input_arg_dicts, through_solids=output_list
    ):
        if not result.success:
            raise result.exception

        print(f'processed {result.name}')


def embedded_dagster_cli_main(argv, pipeline):
    check.list_param(argv, 'argv', of_type=str)
    check.inst_param(pipeline, 'pipeline', SolidPipeline)

    dagster_command_group = click.Group(name='dagster')
    dagster_command_group.add_command(embedded_dagster_graphviz_command)
    dagster_command_group.add_command(embedded_dagster_execute_command)
    dagster_command_group(argv[1:], obj={'pipeline': pipeline})
