import os
import sys

import click

from .context import Config
from .pipeline import create_pipeline_cli


def create_dagster_cli():
    group = click.group()(dagster_cli)
    group.add_command(create_pipeline_cli())
    return group


@click.option(
    '--config',
    '-c',
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        resolve_path=True,
    ),
    default='pipelines.yml',
    help="Path to config file. Defaults to ./pipelines.yml."
)
@click.pass_context
def dagster_cli(ctx, config):
    ctx.obj = Config.from_file(config)
    sys.path.append(os.getcwd())
