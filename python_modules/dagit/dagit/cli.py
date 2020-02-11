import os
import sys

import click
import six
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler

from dagster import ExecutionTargetHandle, check
from dagster.cli.load_handle import handle_for_repo_cli_args
from dagster.cli.pipeline import repository_target_argument
from dagster.core.instance import DagsterInstance
from dagster.utils import DEFAULT_REPOSITORY_YAML_FILENAME

from .app import create_app
from .reloader import DagitReloader
from .version import __version__


def create_dagit_cli():
    return ui  # pylint: disable=no-value-for-parameter


REPO_TARGET_WARNING = (
    'Can only use ONE of --repository-yaml/-y, --python-file/-f, --module-name/-m.'
)


@click.command(
    name='ui',
    help=(
        'Run dagit. Loads a repository or pipeline.\n\n{warning}'.format(
            warning=REPO_TARGET_WARNING
        )
        + (
            '\n\n Examples:'
            '\n\n1. dagit'
            '\n\n2. dagit -y path/to/{default_filename}'
            '\n\n3. dagit -f path/to/file.py -n define_repo'
            '\n\n4. dagit -m some_module -n define_repo'
            '\n\n5. dagit -f path/to/file.py -n define_pipeline'
            '\n\n6. dagit -m some_module -n define_pipeline'
            '\n\n7. dagit -p 3333'
            '\n\nOptions Can also provide arguments via environment variables prefixed with DAGIT_'
            '\n\n    DAGIT_PORT=3333 dagit'
        ).format(default_filename=DEFAULT_REPOSITORY_YAML_FILENAME)
    ),
)
@repository_target_argument
@click.option('--host', '-h', type=click.STRING, default='127.0.0.1', help="Host to run server on")
@click.option('--port', '-p', type=click.INT, default=3000, help="Port to run server on")
@click.option(
    '--storage-fallback',
    help="Base directory for dagster storage if $DAGSTER_HOME is not set",
    default=None,
    type=click.Path(),
)
@click.option(
    '--reload-trigger',
    help="Optional file path being monitored by a parent process that dagit-cli can touch to re-launch itself.",
    default=None,
    hidden=True,
    type=click.Path(),
)
@click.version_option(version=__version__, prog_name='dagit')
def ui(host, port, storage_fallback, reload_trigger, **kwargs):
    handle = handle_for_repo_cli_args(kwargs)

    # add the path for the cwd so imports in dynamically loaded code work correctly
    sys.path.append(os.getcwd())

    host_dagit_ui(handle, host, port, storage_fallback, reload_trigger)


def host_dagit_ui(handle, host, port, storage_fallback=None, reload_trigger=None):
    check.inst_param(handle, 'handle', ExecutionTargetHandle)

    instance = DagsterInstance.get(storage_fallback)
    reloader = DagitReloader(reload_trigger=reload_trigger)

    app = create_app(handle, instance, reloader)

    server = pywsgi.WSGIServer((host, port), app, handler_class=WebSocketHandler)
    print(
        'Serving on http://{host}:{port} in process {pid}'.format(
            host=host, port=port, pid=os.getpid()
        )
    )
    try:
        server.serve_forever()
    except OSError as os_error:
        if 'Address already in use' in str(os_error):
            six.raise_from(
                Exception(
                    (
                        'Another process on your machine is already listening on port {port}. '
                        'It is possible that you have another instance of dagit '
                        'running somewhere using the same port. Or it could be another '
                        'random process. Either kill that process or use the -p option to '
                        'select another port.'
                    ).format(port=port)
                ),
                os_error,
            )
        else:
            raise os_error


cli = create_dagit_cli()


def main():
    # click magic
    cli(auto_envvar_prefix='DAGIT')  # pylint:disable=E1120
