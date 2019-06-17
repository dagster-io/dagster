import json

import click

from graphql import graphql
from graphql.execution.executors.gevent import GeventExecutor
from graphql.execution.executors.sync import SyncExecutor

from dagster import check, seven, ExecutionTargetHandle
from dagster.cli.pipeline import repository_target_argument
from dagster.cli.load_handle import handle_for_repo_cli_args
from dagster.utils import DEFAULT_REPOSITORY_YAML_FILENAME
from dagster.utils.log import get_stack_trace_array

from .implementation.context import DagsterGraphQLContext
from .implementation.pipeline_execution_manager import SynchronousExecutionManager
from .implementation.pipeline_run_storage import PipelineRunStorage

from .schema import create_schema
from .version import __version__


# TODO we may want to start extracting shared copy like this to some central location.
REPO_TARGET_WARNING = (
    'Can only use ONE of --repository-yaml/-y, --python-file/-f, --module-name/-m.'
)


def create_dagster_graphql_cli():
    return ui


def execute_query(
    handle,
    query,
    variables=None,
    pipeline_run_storage=None,
    raise_on_error=False,
    use_sync_executor=False,
):
    check.inst_param(handle, 'handle', ExecutionTargetHandle)
    check.str_param(query, 'query')
    check.opt_dict_param(variables, 'variables')
    check.opt_inst_param(pipeline_run_storage, 'pipeline_run_storage', PipelineRunStorage)
    check.bool_param(raise_on_error, 'raise_on_error')
    check.bool_param(use_sync_executor, 'use_sync_executor')

    query = query.strip('\'" \n\t')

    # We allow external creation of the pipeline_run_storage to support testing contexts where we
    # need access to the underlying run storage
    pipeline_run_storage = pipeline_run_storage or PipelineRunStorage()

    execution_manager = SynchronousExecutionManager()

    context = DagsterGraphQLContext(
        handle=handle,
        pipeline_runs=pipeline_run_storage,
        execution_manager=execution_manager,
        raise_on_error=raise_on_error,
        version=__version__,
    )

    executor = SyncExecutor() if use_sync_executor else GeventExecutor()

    result = graphql(
        request_string=query,
        schema=create_schema(),
        context=context,
        variables=variables,
        executor=executor,
    )

    result_dict = result.to_dict()

    # Here we detect if this is in fact an error response
    # If so, we iterate over the result_dict and the original result
    # which contains a GraphQLError. If that GraphQL error contains
    # an original_error property (which is the exception the resolver
    # has thrown, typically) we serialize the stack trace of that exception
    # in the 'stack_trace' property of each error to ease debugging

    if 'errors' in result_dict:
        check.invariant(len(result_dict['errors']) == len(result.errors))
        for python_error, error_dict in zip(result.errors, result_dict['errors']):
            if hasattr(python_error, 'original_error') and python_error.original_error:
                error_dict['stack_trace'] = get_stack_trace_array(python_error.original_error)

    return result_dict


def execute_query_from_cli(handle, query, variables=None):
    check.inst_param(handle, 'handle', ExecutionTargetHandle)
    check.str_param(query, 'query')
    check.opt_str_param(variables, 'variables')

    query = query.strip('\'" \n\t')

    result_dict = execute_query(handle, query, json.loads(variables) if variables else None)
    str_res = seven.json.dumps(result_dict)

    # Since this the entry point for CLI execution, some tests depend on us putting the result on
    # stdout
    print(str_res)

    return str_res


@repository_target_argument
@click.command(
    name='ui',
    help=(
        'Run a GraphQL query against the dagster interface to a specified repository or pipeline.'
        '\n\n{warning}'.format(warning=REPO_TARGET_WARNING)
    )
    + (
        '\n\n Examples:'
        '\n\n1. dagster-graphql'
        '\n\n2. dagster-graphql -y path/to/{default_filename}'
        '\n\n3. dagster-graphql -f path/to/file.py -n define_repo'
        '\n\n4. dagster-graphql -m some_module -n define_repo'
        '\n\n5. dagster-graphql -f path/to/file.py -n define_pipeline'
        '\n\n6. dagster-graphql -m some_module -n define_pipeline'
    ).format(default_filename=DEFAULT_REPOSITORY_YAML_FILENAME),
)
@click.option('--variables', '-v', type=click.STRING)
@click.version_option(version=__version__)
@click.argument('query', type=click.STRING)
def ui(variables, query, **kwargs):
    handle = handle_for_repo_cli_args(kwargs)

    query = query.strip('\'" \n\t')

    execute_query_from_cli(handle, query, variables)


def main():
    cli = create_dagster_graphql_cli()
    # click magic
    cli(obj={})  # pylint:disable=E1120
