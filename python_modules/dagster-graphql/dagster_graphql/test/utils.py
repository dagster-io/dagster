from dagster_graphql.implementation.context import DagsterGraphQLContext
from dagster_graphql.implementation.pipeline_execution_manager import (
    SubprocessExecutionManager,
    SynchronousExecutionManager,
)
from dagster_graphql.schema import create_schema
from graphql import graphql

from dagster import ExecutionTargetHandle
from dagster.core.instance import DagsterInstance


def execute_dagster_graphql(context, query, variables=None):
    result = graphql(
        create_schema(),
        query,
        context=context,
        variables=variables,
        # executor=GeventObservableExecutor(),
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


def define_context(repo_fn, instance=None):
    return DagsterGraphQLContext(
        handle=ExecutionTargetHandle.for_repo_fn(repo_fn),
        instance=instance or DagsterInstance.ephemeral(),
        execution_manager=SynchronousExecutionManager(),
    )


def define_subprocess_context(repo_fn, instance):
    return DagsterGraphQLContext(
        handle=ExecutionTargetHandle.for_repo_fn(repo_fn),
        instance=instance,
        execution_manager=SubprocessExecutionManager(instance),
    )


def define_context_for_file(python_file, fn_name, instance=None):
    return DagsterGraphQLContext(
        handle=ExecutionTargetHandle.for_repo_python_file(python_file, fn_name),
        instance=instance or DagsterInstance.ephemeral(),
        execution_manager=SynchronousExecutionManager(),
    )


def define_subprocess_context_for_file(python_file, fn_name, instance=None):
    return DagsterGraphQLContext(
        handle=ExecutionTargetHandle.for_repo_python_file(python_file, fn_name),
        instance=instance or DagsterInstance.ephemeral(),
        execution_manager=SubprocessExecutionManager(instance),
    )


def define_context_for_repository_yaml(path, instance=None):
    return DagsterGraphQLContext(
        handle=ExecutionTargetHandle.for_repo_yaml(path),
        instance=instance or DagsterInstance.ephemeral(),
        execution_manager=SynchronousExecutionManager(),
    )
