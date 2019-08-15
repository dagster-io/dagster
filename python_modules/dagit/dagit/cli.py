import os
import sys

import click
import six
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler

from dagster import ExecutionTargetHandle, check
from dagster.cli.load_handle import handle_for_repo_cli_args
from dagster.cli.pipeline import repository_target_argument
from dagster.utils import (
    DEFAULT_REPOSITORY_YAML_FILENAME,
    Features,
    dagster_logs_dir_for_handle,
    dagster_schedule_dir_for_handle,
    is_dagster_home_set,
)
from dagster_graphql.implementation.pipeline_run_storage import (
    FilesystemRunStorage,
    InMemoryRunStorage,
)
from dagster_graphql.implementation.scheduler import SystemCronScheduler

from .app import create_app
from .version import __version__


def create_dagit_cli():
    return ui(auto_envvar_prefix='DAGIT')  # pylint: disable=no-value-for-parameter


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
@click.option('--sync', is_flag=True, help='Use the synchronous execution manager')
@click.option(
    '--log',
    is_flag=True,
    help=(
        'Record logs of pipeline runs. Use --log-dir to specify the directory to record logs to. '
        'By default, logs will be stored under $DAGSTER_HOME.'
    ),
)
@click.option('--log-dir', help="Directory to record logs to", default=None)
@click.option('--schedule-dir', help="Directory to record logs to", default=None)
@click.option(
    '--no-watch',
    is_flag=True,
    help='Disable autoreloading when there are changes to the repo/pipeline being served',
)
@click.version_option(version=__version__, prog_name='dagit')
def ui(host, port, sync, log, log_dir, schedule_dir, no_watch=False, **kwargs):
    handle = handle_for_repo_cli_args(kwargs)

    # add the path for the cwd so imports in dynamically loaded code work correctly
    sys.path.append(os.getcwd())

    if log and not log_dir:
        if not is_dagster_home_set():
            raise click.UsageError(
                '$DAGSTER_HOME is not set and log-dir is not provided. '
                'Set the home directory for dagster by exporting DAGSTER_HOME in your '
                '.bashrc or .bash_profile, or pass in a default directory using the --log-dir flag '
                '\nExamples:'
                '\n  1. export DAGSTER_HOME="~/dagster"'
                '\n  2. --log --logdir="/dagster_logs"'
            )

        log_dir = dagster_logs_dir_for_handle(handle)

    if Features.SCHEDULER.is_enabled:
        # Don't error if $DAGSTER_HOME is not set
        if not schedule_dir and is_dagster_home_set():
            schedule_dir = dagster_schedule_dir_for_handle(handle)

    check.invariant(
        not no_watch,
        'Do not set no_watch when calling the Dagit Python CLI directly -- this flag is a no-op '
        'at this level and should be set only when invoking dagit/bin/dagit.',
    )
    host_dagit_ui(log, log_dir, schedule_dir, handle, sync, host, port)


def host_dagit_ui(log, log_dir, schedule_dir, handle, use_sync, host, port):
    check.inst_param(handle, 'handle', ExecutionTargetHandle)

    pipeline_run_storage = FilesystemRunStorage(log_dir) if log else InMemoryRunStorage()

    if Features.SCHEDULER.is_enabled:
        scheduler = SystemCronScheduler(schedule_dir)
        app = create_app(
            handle, pipeline_run_storage, scheduler, use_synchronous_execution_manager=use_sync
        )
    else:
        app = create_app(handle, pipeline_run_storage, use_synchronous_execution_manager=use_sync)

    server = pywsgi.WSGIServer((host, port), app, handler_class=WebSocketHandler)
    print('Serving on http://{host}:{port}'.format(host=host, port=port))
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


def main():
    cli = create_dagit_cli()
    # click magic
    cli(obj={})  # pylint:disable=E1120
