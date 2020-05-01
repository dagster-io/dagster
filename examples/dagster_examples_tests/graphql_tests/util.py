from dagster_graphql.implementation.context import DagsterGraphQLInProcessRepositoryContext
from dagster_graphql.implementation.pipeline_execution_manager import SynchronousExecutionManager

from dagster.core.definitions.reconstructable import ReconstructableRepository
from dagster.core.instance import DagsterInstance


def define_examples_context():
    return DagsterGraphQLInProcessRepositoryContext(
        recon_repo=ReconstructableRepository.for_module('dagster_examples', 'define_demo_repo'),
        instance=DagsterInstance.ephemeral(),
        execution_manager=SynchronousExecutionManager(),
    )
