"""Tools for accessing core Dagster APIs over a GRPC mechanism.

GRPC is intended to be used in all cases where host processes communicate with user processes, both
locally (over UDS on MacOS and Unix, and over a local port on Windows) and when communicating with
remote Dagster user proceses (e.g., containers).

The GRPC layer is not intended to supplant the dagster-graphql layer, which should still be used to
drive web frontends like the Dagster UI.
"""

# Prevents dagster._core => dagster._grpc.types => dagster._api => dagster._grpc.types circular imports
import dagster._core.remote_representation.external_data  # noqa

from dagster._grpc.types import (
    CanCancelExecutionRequest as CanCancelExecutionRequest,
    CanCancelExecutionResult as CanCancelExecutionResult,
    CancelExecutionRequest as CancelExecutionRequest,
    CancelExecutionResult as CancelExecutionResult,
    ExecuteExternalJobArgs as ExecuteExternalJobArgs,
    ExecuteRunArgs as ExecuteRunArgs,
    ExecuteStepArgs as ExecuteStepArgs,
    ExecutionPlanSnapshotArgs as ExecutionPlanSnapshotArgs,
    ExternalJobArgs as ExternalJobArgs,
    ExternalScheduleExecutionArgs as ExternalScheduleExecutionArgs,
    GetCurrentImageResult as GetCurrentImageResult,
    JobSubsetSnapshotArgs as JobSubsetSnapshotArgs,
    ListRepositoriesInput as ListRepositoriesInput,
    ListRepositoriesResponse as ListRepositoriesResponse,
    LoadableRepositorySymbol as LoadableRepositorySymbol,
    NotebookPathArgs as NotebookPathArgs,
    PartitionArgs as PartitionArgs,
    PartitionNamesArgs as PartitionNamesArgs,
    PartitionSetExecutionParamArgs as PartitionSetExecutionParamArgs,
    ResumeRunArgs as ResumeRunArgs,
    SensorExecutionArgs as SensorExecutionArgs,
    ShutdownServerResult as ShutdownServerResult,
    StartRunResult as StartRunResult,
)
from dagster._grpc.utils import get_loadable_targets as get_loadable_targets
