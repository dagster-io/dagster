from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_graphql.client import (
    DagsterGraphQLClient as DagsterGraphQLClient,
    DagsterGraphQLClientError as DagsterGraphQLClientError,
    InvalidOutputErrorInfo as InvalidOutputErrorInfo,
    ReloadRepositoryLocationInfo as ReloadRepositoryLocationInfo,
    ReloadRepositoryLocationStatus as ReloadRepositoryLocationStatus,
    ShutdownRepositoryLocationInfo as ShutdownRepositoryLocationInfo,
    ShutdownRepositoryLocationStatus as ShutdownRepositoryLocationStatus,
)
from dagster_graphql.version import __version__ as __version__

DagsterLibraryRegistry.register("dagster-graphql", __version__)
