import json

import click

from graphql import graphql
from graphql.execution.executors.gevent import GeventExecutor as Executor

from dagster import check, seven
from dagster.cli.dynamic_loader import (
    RepositoryContainer,
    load_target_info_from_cli_args,
    repository_target_argument,
)
from dagster.utils.logging import get_stack_trace_array

from .implementation.context import DagsterGraphQLContext
from .implementation.pipeline_execution_manager import SynchronousExecutionManager
from .implementation.pipeline_run_storage import InMemoryPipelineRun, PipelineRunStorage

from .schema import create_schema
from .version import __version__


# TODO we may want to start extracting shared copy like this to some central location.
REPO_TARGET_WARNING = (
    'Can only use ONE of --repository-yaml/-y, --python-file/-f, --module-name/-m.'
)


def create_dagster_graphql_cli():
    return ui


def execute_query_from_cli(repository_container, query, variables):
    check.str_param(query, 'query')
    check.opt_str_param(variables, 'variables')

    query = query.strip('\'" \n\t')

    create_pipeline_run = InMemoryPipelineRun
    pipeline_run_storage = PipelineRunStorage(create_pipeline_run=create_pipeline_run)
    execution_manager = SynchronousExecutionManager()

    context = DagsterGraphQLContext(
        repository_container=repository_container,
        pipeline_runs=pipeline_run_storage,
        execution_manager=execution_manager,
        version=__version__,
    )

    # import pdb; pdb.set_trace()

    result = graphql(
        request_string=query,
        schema=create_schema(),
        context=context,
        variables=json.loads(variables) if variables else None,
        executor=Executor(),
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

    str_res = seven.json.dumps(result_dict)

    print(str_res)
    return str_res


@repository_target_argument
@click.command(
    name='ui',
    help=(
        'Run a GraphQL query against the dagster interface to a specified repository or pipeline.'
        '\n\n{warning}'.format(warning=REPO_TARGET_WARNING)
    )
    + '\n\n Examples:'
    '\n\n1. dagit'
    '\n\n2. dagit -y path/to/repository.yml'
    '\n\n3. dagit -f path/to/file.py -n define_repo'
    '\n\n4. dagit -m some_module -n define_repo'
    '\n\n5. dagit -f path/to/file.py -n define_pipeline'
    '\n\n6. dagit -m some_module -n define_pipeline',
)
@click.option('--variables', '-v', type=click.STRING)
@click.version_option(version=__version__)
@click.argument('query', type=click.STRING)
def ui(variables, query, **kwargs):
    repository_target_info = load_target_info_from_cli_args(kwargs)

    repository_container = RepositoryContainer(repository_target_info)

    query = query.strip('\'" \n\t')

    execute_query_from_cli(repository_container, query, variables)


def main():
    cli = create_dagster_graphql_cli()
    # click magic
    cli(obj={})  # pylint:disable=E1120
