from dagster_graphql.implementation.context import (
    DagsterGraphQLContext,
    InProcessRepositoryLocation,
)
from dagster_graphql.implementation.pipeline_execution_manager import (
    SubprocessExecutionManager,
    SynchronousExecutionManager,
)
from dagster_graphql.schema import create_schema
from graphql import graphql

from dagster import check
from dagster.core.definitions.reconstructable import ReconstructableRepository
from dagster.core.instance import DagsterInstance


def execute_dagster_graphql(context, query, variables=None):
    result = graphql(
        create_schema(),
        query,
        context=context,
        variables=variables,
        allow_subscriptions=True,
        return_promise=False,
    )

    # has to check attr because in subscription case it returns AnonymousObservable
    if hasattr(result, 'errors') and result.errors:
        first_error = result.errors[0]
        if hasattr(first_error, 'original_error') and first_error.original_error:
            raise result.errors[0].original_error

        raise result.errors[0]

    return result


def define_context_for_file(python_file, fn_name, instance):
    check.inst_param(instance, 'instance', DagsterInstance)
    return DagsterGraphQLContext(
        locations=[
            InProcessRepositoryLocation(
                ReconstructableRepository.for_file(python_file, fn_name),
                execution_manager=SynchronousExecutionManager(),
            )
        ],
        instance=instance,
    )


def define_subprocess_context_for_file(python_file, fn_name, instance):
    check.inst_param(instance, 'instance', DagsterInstance)
    return DagsterGraphQLContext(
        locations=[
            InProcessRepositoryLocation(
                ReconstructableRepository.for_file(python_file, fn_name),
                execution_manager=SubprocessExecutionManager(instance),
            )
        ],
        instance=instance,
    )


def define_context_for_repository_yaml(path, instance):
    check.inst_param(instance, 'instance', DagsterInstance)
    return DagsterGraphQLContext(
        locations=[
            InProcessRepositoryLocation(
                ReconstructableRepository.from_yaml(path),
                execution_manager=SynchronousExecutionManager(),
            )
        ],
        instance=instance,
    )
