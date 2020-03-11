import os
import sys
import threading

import click
import six
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler

from dagster import ExecutionTargetHandle, check, seven
from dagster.cli.load_handle import handle_for_repo_cli_args
from dagster.cli.pipeline import repository_target_argument
from dagster.core.instance import DagsterInstance
from dagster.core.telemetry import upload_logs
from dagster.utils import DEFAULT_REPOSITORY_YAML_FILENAME, pushd

from .app import create_app
from .reloader import DagitReloader
from .version import __version__


def create_dagit_cli():
    return ui  # pylint: disable=no-value-for-parameter


REPO_TARGET_WARNING = (
    'Can only use ONE of --repository-yaml/-y, --python-file/-f, --module-name/-m.'
)

DEFAULT_DAGIT_HOST = '127.0.0.1'
DEFAULT_DAGIT_PORT = 3000


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
@click.option(
    '--host',
    '-h',
    type=click.STRING,
    default=DEFAULT_DAGIT_HOST,
    help="Host to run server on, default is {default_host}".format(default_host=DEFAULT_DAGIT_HOST),
)
@click.option(
    '--port',
    '-p',
    type=click.INT,
    help="Port to run server on, default is {default_port}".format(default_port=DEFAULT_DAGIT_PORT),
)
@click.option(
    '--storage-fallback',
    help="Base directory for dagster storage if $DAGSTER_HOME is not set",
    default=None,
    type=click.Path(),
)
@click.option(
    '--reload-trigger',
    help=(
        "Optional file path being monitored by a parent process that dagit-cli can touch to "
        "re-launch itself."
    ),
    default=None,
    hidden=True,
    type=click.Path(),
)
@click.option(
    '--workdir',
    help=(
        "Set this to change the working directory before invoking dagit. Intended to support "
        "test cases"
    ),
    default=None,
    hidden=True,
    type=click.Path(),
)
@click.version_option(version=__version__, prog_name='dagit')
def ui(host, port, storage_fallback, reload_trigger, workdir, **kwargs):
    handle = handle_for_repo_cli_args(kwargs)

    # add the path for the cwd so imports in dynamically loaded code work correctly
    sys.path.append(os.getcwd())

    if port is None:
        port_lookup = True
        port = DEFAULT_DAGIT_PORT
    else:
        port_lookup = False

    # The dagit entrypoint always sets this but if someone launches dagit-cli
    # directly make sure things still works by providing a temp directory
    if storage_fallback is None:
        storage_fallback = seven.TemporaryDirectory().name

    if workdir is not None:
        with pushd(workdir):
            host_dagit_ui(handle, host, port, storage_fallback, reload_trigger, port_lookup)
    else:
        host_dagit_ui(handle, host, port, storage_fallback, reload_trigger, port_lookup)


def host_dagit_ui(handle, host, port, storage_fallback, reload_trigger=None, port_lookup=True):
    check.inst_param(handle, 'handle', ExecutionTargetHandle)

    instance = DagsterInstance.get(storage_fallback)
    reloader = DagitReloader(reload_trigger=reload_trigger)

    app = create_app(handle, instance, reloader)

    start_server(host, port, app, port_lookup)


def start_server(host, port, app, port_lookup, port_lookup_attempts=0):
    server = pywsgi.WSGIServer((host, port), app, handler_class=WebSocketHandler)

    print(
        'Serving on http://{host}:{port} in process {pid}'.format(
            host=host, port=port, pid=os.getpid()
        )
    )

    try:
        thread = threading.Thread(target=upload_logs, args=())
        thread.daemon = True
        thread.start()

        server.serve_forever()
    except OSError as os_error:
        if 'Address already in use' in str(os_error):
            if port_lookup and (
                port_lookup_attempts > 0
                or click.confirm(
                    (
                        'Another process on your machine is already listening on port {port}. '
                        'Would you like to run the app at another port instead?'
                    ).format(port=port)
                )
            ):
                port_lookup_attempts += 1
                start_server(host, port + port_lookup_attempts, app, True, port_lookup_attempts)
            else:
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
