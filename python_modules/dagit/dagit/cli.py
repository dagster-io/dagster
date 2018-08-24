import os
import sys

import click
from waitress import serve
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from dagster import check

from dagster.cli.context import (
    RepositoryInfo,
    load_repository_from_file,
    repository_config_argument,
    reload_repository_info,
)

from .app import create_app


def create_dagit_cli():
    return ui


class ReloaderHandler(FileSystemEventHandler):
    def __init__(self, repository_container):
        super(ReloaderHandler, self).__init__()
        self.repository_container = repository_container

    def on_any_event(self, event):
        if event.src_path.endswith('.py'):
            self.repository_container.reload()


class RepositoryContainer:
    '''
    This class solely exists to implement reloading semantics. We need to have a single object
    that the graphql server has access that stays the same object between reload. This container
    object allows the RepositoryInfo to be written in an immutable fashion.
    '''

    def __init__(self, repository_info):
        self.repository_info = check.inst_param(repository_info, 'repository_info', RepositoryInfo)

    def reload(self):
        self.repository_info = reload_repository_info(self.repository_info)

    @property
    def repository(self):
        return self.repository_info.repository


@click.command(name='ui', help='run web ui')
@repository_config_argument
@click.option('--host', '-h', type=click.STRING, default='127.0.0.1', help="Host to run server on")
@click.option('--port', '-p', type=click.INT, default=3000, help="Port to run server on")
def ui(conf, host, port):
    sys.path.append(os.getcwd())
    repository_container = RepositoryContainer(load_repository_from_file(conf))
    observer = Observer()
    handler = ReloaderHandler(repository_container)
    observer.schedule(handler, os.path.dirname(os.path.abspath(conf)), recursive=True)
    observer.start()
    try:
        app = create_app(repository_container)
        serve(app, host=host, port=port)
    except KeyboardInterrupt:
        observer.stop()
