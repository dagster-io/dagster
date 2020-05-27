from dagster_graphql.implementation.context import (
    DagsterGraphQLContext,
    InProcessRepositoryLocation,
)
from dagster_graphql.implementation.pipeline_execution_manager import SynchronousExecutionManager

from dagster.core.definitions.reconstructable import ReconstructableRepository
from dagster.core.instance import DagsterInstance


def define_examples_context():
    return DagsterGraphQLContext(
        locations=[
            InProcessRepositoryLocation(
                ReconstructableRepository.for_module('dagster_examples', 'define_demo_repo'),
                execution_manager=SynchronousExecutionManager(),
            )
        ],
        instance=DagsterInstance.ephemeral(),
    )
