# pylint: disable=missing-graphene-docstring
import graphene

import dagster._check as check
from dagster.core.definitions.events import AssetKey
from dagster.utils.error import SerializableErrorInfo

from .util import non_null_list


class GrapheneError(graphene.Interface):
    message = graphene.String(required=True)

    class Meta:
        name = "Error"


class GraphenePythonError(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneError,)
        name = "PythonError"

    className = graphene.Field(graphene.String)
    stack = non_null_list(graphene.String)
    cause = graphene.Field(lambda: GraphenePythonError)

    def __init__(self, error_info):
        super().__init__()
        check.inst_param(error_info, "error_info", SerializableErrorInfo)
        self.message = error_info.message
        self.stack = error_info.stack
        self.cause = error_info.cause
        self.className = error_info.cls_name


class GrapheneSchedulerNotDefinedError(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneError,)
        name = "SchedulerNotDefinedError"

    def __init__(self):
        super().__init__()
        self.message = "Scheduler is not defined for the currently loaded repository."


class GraphenePipelineSnapshotNotFoundError(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneError,)
        name = "PipelineSnapshotNotFoundError"

    snapshot_id = graphene.NonNull(graphene.String)

    def __init__(self, snapshot_id):
        super().__init__()
        self.snapshot_id = check.str_param(snapshot_id, "snapshot_id")
        self.message = f"Pipeline snapshot {snapshot_id} is not present in the current instance."


class GrapheneReloadNotSupported(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneError,)
        name = "ReloadNotSupported"

    def __init__(self, location_name):
        super().__init__()
        self.message = f"Location {location_name} does not support reloading."


class GrapheneRepositoryLocationNotFound(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneError,)
        name = "RepositoryLocationNotFound"

    def __init__(self, location_name):
        super().__init__()
        self.message = f"Location {location_name} does not exist."


class GraphenePipelineNotFoundError(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneError,)
        name = "PipelineNotFoundError"

    pipeline_name = graphene.NonNull(graphene.String)
    repository_name = graphene.NonNull(graphene.String)
    repository_location_name = graphene.NonNull(graphene.String)

    def __init__(self, selector):
        from ..implementation.utils import PipelineSelector

        super().__init__()
        check.inst_param(selector, "selector", PipelineSelector)
        self.pipeline_name = selector.pipeline_name
        self.repository_name = selector.repository_name
        self.repository_location_name = selector.location_name
        self.message = (
            "Could not find Pipeline "
            f"{selector.location_name}.{selector.repository_name}.{selector.pipeline_name}"
        )


class GrapheneGraphNotFoundError(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneError,)
        name = "GraphNotFoundError"

    graph_name = graphene.NonNull(graphene.String)
    repository_name = graphene.NonNull(graphene.String)
    repository_location_name = graphene.NonNull(graphene.String)

    def __init__(self, selector):
        from ..implementation.utils import GraphSelector

        super().__init__()
        check.inst_param(selector, "selector", GraphSelector)
        self.graph_name = selector.graph_name
        self.repository_name = selector.repository_name
        self.repository_location_name = selector.location_name
        self.message = (
            "Could not find Graph "
            f"{selector.location_name}.{selector.repository_name}.{selector.graph_name}"
        )


class GraphenePipelineRunNotFoundError(graphene.Interface):
    class Meta:
        interfaces = (GrapheneError,)
        name = "PipelineRunNotFoundError"

    run_id = graphene.NonNull(graphene.String)
    message = graphene.String(required=True)


class GrapheneRunNotFoundError(graphene.ObjectType):
    class Meta:
        interfaces = (GraphenePipelineRunNotFoundError, GrapheneError)
        name = "RunNotFoundError"

    run_id = graphene.NonNull(graphene.String)

    def __init__(self, run_id):
        super().__init__()
        self.run_id = check.str_param(run_id, "run_id")
        self.message = f"Pipeline run {run_id} could not be found."


class GrapheneInvalidPipelineRunsFilterError(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneError,)
        name = "InvalidPipelineRunsFilterError"

    def __init__(self, message):
        super().__init__()
        self.message = check.str_param(message, "message")


class GrapheneRunGroupNotFoundError(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneError,)
        name = "RunGroupNotFoundError"

    run_id = graphene.NonNull(graphene.String)

    def __init__(self, run_id):
        super().__init__()
        self.run_id = check.str_param(run_id, "run_id")
        self.message = f"Run group of run {run_id} could not be found."


class GraphenePresetNotFoundError(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneError,)
        name = "PresetNotFoundError"

    preset = graphene.NonNull(graphene.String)

    def __init__(self, preset, selector):
        super().__init__()
        self.preset = check.str_param(preset, "preset")
        self.message = f"Preset {preset} not found in pipeline {selector.pipeline_name}."


class GrapheneConflictingExecutionParamsError(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneError,)
        name = "ConflictingExecutionParamsError"

    def __init__(self, conflicting_param):
        super().__init__()
        self.message = (
            f"Invalid ExecutionParams. Cannot define {conflicting_param} when using a preset."
        )


class GrapheneModeNotFoundError(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneError,)
        name = "ModeNotFoundError"

    mode = graphene.NonNull(graphene.String)

    def __init__(self, mode, selector):
        super().__init__()
        self.mode = check.str_param(mode, "mode")
        self.message = f"Mode {mode} not found in pipeline {selector.pipeline_name}."


class GrapheneNoModeProvidedError(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneError,)
        name = "NoModeProvidedError"

    pipeline_name = graphene.NonNull(graphene.String)

    def __init__(self, pipeline_name, mode_list):
        super().__init__()
        mode_list = check.list_param(mode_list, "mode_list", of_type=str)
        pipeline_name = check.str_param(pipeline_name, "pipeline_name")
        self.message = f"No mode provided for pipeline '{pipeline_name}', which has multiple modes. Available modes: {mode_list}"


class GrapheneInvalidStepError(graphene.ObjectType):
    invalid_step_key = graphene.NonNull(graphene.String)

    class Meta:
        name = "InvalidStepError"


class GrapheneInvalidOutputError(graphene.ObjectType):
    step_key = graphene.NonNull(graphene.String)
    invalid_output_name = graphene.NonNull(graphene.String)

    class Meta:
        name = "InvalidOutputError"


class GraphenePipelineRunConflict(graphene.Interface):
    message = graphene.NonNull(graphene.String)

    class Meta:
        name = "PipelineRunConflict"


class GrapheneRunConflict(graphene.ObjectType):
    message = graphene.NonNull(graphene.String)

    class Meta:
        interfaces = (GrapheneError, GraphenePipelineRunConflict)
        name = "RunConflict"


create_execution_params_error_types = (
    GraphenePresetNotFoundError,
    GrapheneConflictingExecutionParamsError,
    GrapheneNoModeProvidedError,
)


class GrapheneDagsterTypeNotFoundError(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneError,)
        name = "DagsterTypeNotFoundError"

    dagster_type_name = graphene.NonNull(graphene.String)


class GrapheneScheduleNotFoundError(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneError,)
        name = "ScheduleNotFoundError"

    schedule_name = graphene.NonNull(graphene.String)

    def __init__(self, schedule_name):
        super().__init__()
        self.schedule_name = check.str_param(schedule_name, "schedule_name")
        self.message = f"Schedule {self.schedule_name} could not be found."


class GrapheneSensorNotFoundError(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneError,)
        name = "SensorNotFoundError"

    sensor_name = graphene.NonNull(graphene.String)

    def __init__(self, sensor_name):
        super().__init__()
        self.name = check.str_param(sensor_name, "sensor_name")
        self.message = f"Could not find `{sensor_name}` in the currently loaded repository."


class GraphenePartitionSetNotFoundError(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneError,)
        name = "PartitionSetNotFoundError"

    partition_set_name = graphene.NonNull(graphene.String)

    def __init__(self, partition_set_name):
        super().__init__()
        self.partition_set_name = check.str_param(partition_set_name, "partition_set_name")
        self.message = f"Partition set {self.partition_set_name} could not be found."


class GrapheneRepositoryNotFoundError(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneError,)
        name = "RepositoryNotFoundError"

    repository_name = graphene.NonNull(graphene.String)
    repository_location_name = graphene.NonNull(graphene.String)

    def __init__(self, repository_location_name, repository_name):
        super().__init__()
        self.repository_name = check.str_param(repository_name, "repository_name")
        self.repository_location_name = check.str_param(
            repository_location_name, "repository_location_name"
        )
        self.message = f"Could not find Repository {repository_location_name}.{repository_name}"


class GrapheneAssetNotFoundError(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneError,)
        name = "AssetNotFoundError"

    def __init__(self, asset_key):
        super().__init__()
        self.asset_key = check.inst_param(asset_key, "asset_key", AssetKey)
        self.message = f"Asset key {asset_key.to_string()} not found."


class GrapheneUnauthorizedError(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneError,)
        name = "UnauthorizedError"

    def __init__(self, message=None):
        super().__init__()
        self.message = message if message else "Authorization failed"


types = [
    GrapheneAssetNotFoundError,
    GrapheneConflictingExecutionParamsError,
    GrapheneDagsterTypeNotFoundError,
    GrapheneError,
    GrapheneInvalidOutputError,
    GrapheneInvalidPipelineRunsFilterError,
    GrapheneInvalidStepError,
    GrapheneModeNotFoundError,
    GrapheneNoModeProvidedError,
    GraphenePartitionSetNotFoundError,
    GraphenePipelineNotFoundError,
    GraphenePipelineRunConflict,
    GrapheneRunConflict,
    GraphenePipelineRunNotFoundError,
    GraphenePipelineSnapshotNotFoundError,
    GraphenePresetNotFoundError,
    GraphenePythonError,
    GrapheneUnauthorizedError,
    GrapheneReloadNotSupported,
    GrapheneRepositoryLocationNotFound,
    GrapheneRepositoryNotFoundError,
    GrapheneRunGroupNotFoundError,
    GrapheneRunNotFoundError,
    GrapheneScheduleNotFoundError,
    GrapheneSchedulerNotDefinedError,
    GrapheneSensorNotFoundError,
]
