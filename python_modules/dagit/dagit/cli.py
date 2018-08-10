import click
import os
import sys
from waitress import serve

from dagster.cli.context import Config

from .app import create_app


def create_dagit_cli():
    group = click.group()(dagster_cli)
    group.add_command(ui)
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


@click.command(name='ui', help='run web ui')
@click.option('--host', '-h', type=click.STRING, default='127.0.0.1', help="Host to run server on")
@click.option('--port', '-p', type=click.INT, default=3000, help="Port to run server on")
@Config.pass_object
def ui(config, host, port):
    app = create_app(config)

    serve(app, host=host, port=port)
