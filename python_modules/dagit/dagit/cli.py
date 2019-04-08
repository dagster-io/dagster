import json
import os
import sys

import click

from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler
from graphql import graphql
from graphql.execution.executors.gevent import GeventExecutor as Executor


from dagster import check, seven
from dagster.cli.dynamic_loader import (
    RepositoryContainer,
    load_target_info_from_cli_args,
    repository_target_argument,
)
from dagster.utils.logging import get_stack_trace_array
from dagster_graphql.implementation.context import DagsterGraphQLContext
from dagster_graphql.implementation.pipeline_execution_manager import SynchronousExecutionManager
from dagster_graphql.implementation.pipeline_run_storage import (
    PipelineRunStorage,
    LogFilePipelineRun,
    InMemoryPipelineRun,
)

from .app import create_app
from .schema import create_schema
from .version import __version__


def create_dagit_cli():
    return ui


REPO_TARGET_WARNING = (
    'Can only use ONE of --repository-yaml/-y, --python-file/-f, --module-name/-m.'
)


def execute_query_from_cli(repository_container, query, variables):
    check.str_param(query, 'query')
    check.opt_str_param(variables, 'variables')

    create_pipeline_run = InMemoryPipelineRun
    pipeline_run_storage = PipelineRunStorage(create_pipeline_run=create_pipeline_run)
    execution_manager = SynchronousExecutionManager()

    context = DagsterGraphQLContext(
        repository_container=repository_container,
        pipeline_runs=pipeline_run_storage,
        execution_manager=execution_manager,
        version=__version__,
    )

    result = graphql(
        request_string=query,
        schema=create_schema(),
        context=context,
        variables=json.loads(variables) if variables else None,
        executor=Executor(),
    )

    stack_traces = []

    has_errors = bool(result.errors)

    if has_errors:
        for error in result.errors:
            stack_traces.append(get_stack_trace_array(error))

    result_dict = result.to_dict()

    if has_errors:
        check.invariant('errors' in result_dict)
        check.invariant(len(result_dict['errors']) == len(result.errors))
        for python_error, error_dict in zip(result.errors, result_dict['errors']):
            if python_error.original_error:
                error_dict['stack_trace'] = get_stack_trace_array(python_error.original_error)

    str_res = seven.json.dumps(result_dict)

    print(str_res)
    return str_res


@click.command(
    name='ui',
    help=(
        'Run dagit. Loads a repository or pipeline.\n\n{warning}'.format(
            warning=REPO_TARGET_WARNING
        )
        + '\n\n Examples:'
        '\n\n1. dagit'
        '\n\n2. dagit -y path/to/repository.yml'
        '\n\n3. dagit -f path/to/file.py -n define_repo'
        '\n\n4. dagit -m some_module -n define_repo'
        '\n\n5. dagit -f path/to/file.py -n define_pipeline'
        '\n\n6. dagit -m some_module -n define_pipeline'
    ),
)
@repository_target_argument
@click.option('--host', '-h', type=click.STRING, default='127.0.0.1', help="Host to run server on")
@click.option('--port', '-p', type=click.INT, default=3000, help="Port to run server on")
@click.option('--sync', is_flag=True, help='Use the synchronous execution manager')
@click.option('--log', is_flag=False, help='Record logs of pipeline runs')
@click.option('--log-dir', help="Directory to record logs to", default='dagit_run_logs/')
@click.option('--query', '-q', type=click.STRING)
@click.option('--variables', '-v', type=click.STRING)
@click.option(
    '--no-watch',
    is_flag=True,
    help='Disable autoreloading when there are changes to the repo/pipeline being served',
)
@click.version_option(version=__version__)
def ui(host, port, sync, log, log_dir, query, variables, no_watch=False, **kwargs):
    repository_target_info = load_target_info_from_cli_args(kwargs)

    sys.path.append(os.getcwd())
    repository_container = RepositoryContainer(repository_target_info)

    if query:
        return execute_query_from_cli(repository_container, query, variables)
    else:
        if variables:
            raise Exception('if you specify --variables/-v you need to specify --query/-q')

    check.invariant(
        not no_watch,
        'Do not set no_watch when calling the Dagit Python CLI directly -- this flag is a no-op'
        'at this level and should be set only when invoking dagit/bin/dagit.',
    )
    host_dagit_ui(log, log_dir, repository_container, sync, host, port)


def host_dagit_ui(log, log_dir, repository_container, sync, host, port):
    if log:

        def create_pipeline_run(*args, **kwargs):
            return LogFilePipelineRun(log_dir, *args, **kwargs)

    else:
        create_pipeline_run = InMemoryPipelineRun

    pipeline_run_storage = PipelineRunStorage(create_pipeline_run=create_pipeline_run)

    app = create_app(
        repository_container, pipeline_run_storage, use_synchronous_execution_manager=sync
    )
    server = pywsgi.WSGIServer((host, port), app, handler_class=WebSocketHandler)
    print('Serving on http://{host}:{port}'.format(host=host, port=port))
    server.serve_forever()


def main():
    cli = create_dagit_cli()
    # click magic
    cli(obj={})  # pylint:disable=E1120
