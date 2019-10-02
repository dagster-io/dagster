from dagster_graphql.implementation.context import DagsterGraphQLContext
from dagster_graphql.implementation.pipeline_execution_manager import SynchronousExecutionManager

from dagster import ExecutionTargetHandle
from dagster.core.instance import DagsterInstance


def define_examples_context():
    return DagsterGraphQLContext(
        handle=ExecutionTargetHandle.for_repo_module('dagster_examples', 'define_demo_repo'),
        instance=DagsterInstance.ephemeral(),
        execution_manager=SynchronousExecutionManager(),
    )
