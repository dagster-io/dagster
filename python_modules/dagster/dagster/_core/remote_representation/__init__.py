"""This subpackage contains all classes that host processes (e.g. dagster-webserver)
use to manipulate and represent definitions that are resident
in user processes and containers.  e.g. ExternalPipeline.

It also contains classes that represent historical representations
that have been persisted. e.g. HistoricalPipeline
"""

from dagster._core.remote_representation.external import (
    RemoteExecutionPlan as RemoteExecutionPlan,
    RemoteJob as RemoteJob,
    RemotePartitionSet as RemotePartitionSet,
    RemoteRepository as RemoteRepository,
    RemoteSchedule as RemoteSchedule,
    RemoteSensor as RemoteSensor,
)
from dagster._core.remote_representation.external_data import (
    ExecutionParamsErrorSnap as ExecutionParamsErrorSnap,
    ExecutionParamsSnap as ExecutionParamsSnap,
    JobDataSnap as JobDataSnap,
    JobRefSnap as JobRefSnap,
    PartitionConfigSnap as PartitionConfigSnap,
    PartitionExecutionErrorSnap as PartitionExecutionErrorSnap,
    PartitionNamesSnap as PartitionNamesSnap,
    PartitionSetExecutionParamSnap as PartitionSetExecutionParamSnap,
    PartitionSetSnap as PartitionSetSnap,
    PartitionTagsSnap as PartitionTagsSnap,
    PresetSnap as PresetSnap,
    RemoteJobSubsetResult as RemoteJobSubsetResult,
    RepositoryErrorSnap as RepositoryErrorSnap,
    RepositorySnap as RepositorySnap,
    ScheduleExecutionErrorSnap as ScheduleExecutionErrorSnap,
    ScheduleSnap as ScheduleSnap,
    SensorExecutionErrorSnap as SensorExecutionErrorSnap,
    SensorSnap as SensorSnap,
    TargetSnap as TargetSnap,
)
from dagster._core.remote_representation.handle import (
    JobHandle as JobHandle,
    RepositoryHandle as RepositoryHandle,
)
from dagster._core.remote_representation.historical import HistoricalJob as HistoricalJob
from dagster._core.remote_representation.origin import (
    IN_PROCESS_NAME as IN_PROCESS_NAME,
    CodeLocationOrigin as CodeLocationOrigin,
    GrpcServerCodeLocationOrigin as GrpcServerCodeLocationOrigin,
    InProcessCodeLocationOrigin as InProcessCodeLocationOrigin,
    ManagedGrpcPythonEnvCodeLocationOrigin as ManagedGrpcPythonEnvCodeLocationOrigin,
    RemoteInstigatorOrigin as RemoteInstigatorOrigin,
    RemoteJobOrigin as RemoteJobOrigin,
    RemoteRepositoryOrigin as RemoteRepositoryOrigin,
)

# ruff: isort: split
from dagster._core.remote_representation.code_location import (
    CodeLocation as CodeLocation,
    GrpcServerCodeLocation as GrpcServerCodeLocation,
    InProcessCodeLocation as InProcessCodeLocation,
)
from dagster._core.remote_representation.job_index import JobIndex as JobIndex
from dagster._core.remote_representation.represented import RepresentedJob as RepresentedJob
