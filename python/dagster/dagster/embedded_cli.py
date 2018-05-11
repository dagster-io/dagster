import click

import check

from solidic.execution import (SolidPipeline, execute_pipeline, SolidExecutionContext)

from .graphviz import build_graphviz_graph


@click.command(name='graphviz')
@click.pass_context
def embedded_dagster_graphviz_command(cxt):
    pipeline = check.inst(cxt.obj['pipeline'], SolidPipeline)
    build_graphviz_graph(pipeline).view(cleanup=True)


@click.command(name='execute')
@click.option('--input', multiple=True)
@click.option('--output', multiple=True)
@click.pass_context
def embedded_dagster_execute_command(cxt, input, output):
    check.tuple_param(input, 'input')
    check.tuple_param(output, 'output')

    input_list = list(input)
    output_list = list(output)

    pipeline = check.inst(cxt.obj['pipeline'], SolidPipeline)

    input_arg_dicts = {'qhp_json_input': {'path': 'providers-771.json'}}

    for result in execute_pipeline(
        SolidExecutionContext(), pipeline, input_arg_dicts, through_solids=output_list
    ):
        if not result.success:
            raise result.exception

        if result.name in output_list:
            print(result.materialized_output)


def embedded_dagster_cli_main(argv, pipeline):
    check.list_param(argv, 'argv', of_type=str)
    check.inst_param(pipeline, 'pipeline', SolidPipeline)

    dagster_command_group = click.Group(name='dagster')
    dagster_command_group.add_command(embedded_dagster_graphviz_command)
    dagster_command_group.add_command(embedded_dagster_execute_command)
    dagster_command_group(argv[1:], obj={'pipeline': pipeline})
