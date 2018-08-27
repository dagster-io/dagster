import click
import os
import sys
from waitress import serve
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from dagster.cli.context import Config

from .app import create_app


def create_dagit_cli():
    return ui


class ReloaderHandler(FileSystemEventHandler):
    def __init__(self, pipeline_config):
        super(ReloaderHandler, self).__init__()
        self.pipeline_config = pipeline_config

    def on_any_event(self, event):
        if event.src_path.endswith('.py'):
            self.pipeline_config.reload()


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
def ui(config, host, port):
    sys.path.append(os.getcwd())
    pipeline_config = Config.from_file(config)
    observer = Observer()
    handler = ReloaderHandler(pipeline_config)
    observer.schedule(handler, os.path.dirname(os.path.abspath(config)), recursive=True)
    observer.start()
    try:
        app = create_app(pipeline_config)
        serve(app, host=host, port=port)
    except KeyboardInterrupt:
        observer.stop()
