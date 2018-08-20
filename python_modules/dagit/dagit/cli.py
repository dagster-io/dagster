import click
import os
import sys
from waitress import serve

from dagster.cli.context import Config

from .app import create_app


def create_dagit_cli():
    return ui


@click.command(name='ui', help='run web ui')
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
@click.option('--host', '-h', type=click.STRING, default='127.0.0.1', help="Host to run server on")
@click.option('--port', '-p', type=click.INT, default=3000, help="Port to run server on")
@click.pass_context
def ui(ctx, config, host, port):
    ctx.obj = Config.from_file(config)
    app = create_app(ctx.obj)

    serve(app, host=host, port=port)
