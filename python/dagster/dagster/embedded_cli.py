import click

import check

from solidic.execution import SolidPipeline

from .graphviz import build_graphviz_graph


@click.command(name='graphviz')
@click.pass_context
def embedded_dagster_graphviz_command(cxt):
    pipeline = check.inst(cxt.obj['pipeline'], SolidPipeline)
    build_graphviz_graph(pipeline).view(cleanup=True)


def embedded_dagster_cli_main(argv, pipeline):
    check.list_param(argv, 'argv', of_type=str)
    check.inst_param(pipeline, 'pipeline', SolidPipeline)

    dagster_command_group = click.Group(name='dagster')
    dagster_command_group.add_command(embedded_dagster_graphviz_command)
    dagster_command_group(argv[1:], obj={'pipeline': pipeline})