"""This subpackage contains all classes that host processes (e.g. dagster-webserver)
use to manipulate and represent definitions that are resident
in user processes and containers.  e.g. ExternalPipeline.

It also contains classes that represent historical representations
that have been persisted. e.g. HistoricalPipeline
"""

from .handle import (
    JobHandle as JobHandle,
    RepositoryHandle as RepositoryHandle,
)
from .origin import (
    IN_PROCESS_NAME as IN_PROCESS_NAME,
    RemoteJobOrigin as RemoteJobOrigin,
    CodeLocationOrigin as CodeLocationOrigin,
    RemoteInstigatorOrigin as RemoteInstigatorOrigin,
    RemoteRepositoryOrigin as RemoteRepositoryOrigin,
    InProcessCodeLocationOrigin as InProcessCodeLocationOrigin,
    GrpcServerCodeLocationOrigin as GrpcServerCodeLocationOrigin,
    ManagedGrpcPythonEnvCodeLocationOrigin as ManagedGrpcPythonEnvCodeLocationOrigin,
)
from .external import (
    ExternalJob as ExternalJob,
    ExternalSensor as ExternalSensor,
    ExternalSchedule as ExternalSchedule,
    ExternalRepository as ExternalRepository,
    ExternalPartitionSet as ExternalPartitionSet,
    ExternalExecutionPlan as ExternalExecutionPlan,
)
from .historical import HistoricalJob as HistoricalJob
from .external_data import (
    SensorSnap as SensorSnap,
    ScheduleSnap as ScheduleSnap,
    ExternalJobRef as ExternalJobRef,
    ExternalJobData as ExternalJobData,
    PartitionSetSnap as PartitionSetSnap,
    ExternalPresetData as ExternalPresetData,
    ExternalTargetData as ExternalTargetData,
    ExternalRepositoryData as ExternalRepositoryData,
    ExternalJobSubsetResult as ExternalJobSubsetResult,
    ExternalPartitionTagsData as ExternalPartitionTagsData,
    ExternalPartitionNamesData as ExternalPartitionNamesData,
    ExternalExecutionParamsData as ExternalExecutionParamsData,
    ExternalPartitionConfigData as ExternalPartitionConfigData,
    ExternalRepositoryErrorData as ExternalRepositoryErrorData,
    ExternalExecutionParamsErrorData as ExternalExecutionParamsErrorData,
    ExternalSensorExecutionErrorData as ExternalSensorExecutionErrorData,
    ExternalScheduleExecutionErrorData as ExternalScheduleExecutionErrorData,
    ExternalPartitionExecutionErrorData as ExternalPartitionExecutionErrorData,
    ExternalPartitionSetExecutionParamData as ExternalPartitionSetExecutionParamData,
    external_job_data_from_def as external_job_data_from_def,
    external_repository_data_from_def as external_repository_data_from_def,
)

# ruff: isort: split
from .job_index import JobIndex as JobIndex
from .represented import RepresentedJob as RepresentedJob
from .code_location import (
    CodeLocation as CodeLocation,
    InProcessCodeLocation as InProcessCodeLocation,
    GrpcServerCodeLocation as GrpcServerCodeLocation,
)
