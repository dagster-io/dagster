from dagster import ExecutionTargetHandle
from dagster_graphql.implementation.context import DagsterGraphQLContext
from dagster_graphql.implementation.pipeline_execution_manager import SynchronousExecutionManager
from dagster_graphql.implementation.pipeline_run_storage import InMemoryRunStorage


def define_examples_context(raise_on_error=True):
    return DagsterGraphQLContext(
        handle=ExecutionTargetHandle.for_repo_module('dagster_examples', 'define_demo_repo'),
        pipeline_runs=InMemoryRunStorage(),
        execution_manager=SynchronousExecutionManager(),
        raise_on_error=raise_on_error,
    )
