from dagster_graphql.implementation.context import (
    DagsterGraphQLContext,
    InProcessRepositoryLocation,
)

from dagster.core.definitions.reconstructable import ReconstructableRepository
from dagster.core.instance import DagsterInstance


def define_examples_context():
    return DagsterGraphQLContext(
        locations=[
            InProcessRepositoryLocation(
                ReconstructableRepository.for_module(
                    'dagster_examples', 'define_internal_dagit_repository'
                ),
            )
        ],
        instance=DagsterInstance.ephemeral(),
    )
