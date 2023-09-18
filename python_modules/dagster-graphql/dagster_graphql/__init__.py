from dagster._core.libraries import DagsterLibraryRegistry

from .client import (
    AssetMetric as AssetMetric,
    DagsterGraphQLClient as DagsterGraphQLClient,
    DagsterGraphQLClientError as DagsterGraphQLClientError,
    InvalidOutputErrorInfo as InvalidOutputErrorInfo,
    JobMetric as JobMetric,
    ReloadRepositoryLocationInfo as ReloadRepositoryLocationInfo,
    ReloadRepositoryLocationStatus as ReloadRepositoryLocationStatus,
    ShutdownRepositoryLocationInfo as ShutdownRepositoryLocationInfo,
    ShutdownRepositoryLocationStatus as ShutdownRepositoryLocationStatus,
)
from .version import __version__ as __version__

DagsterLibraryRegistry.register("dagster-graphql", __version__)
