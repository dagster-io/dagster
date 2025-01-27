from typing import Optional

import dagster._check as check
import graphene
from dagster._core.definitions.events import AssetKey
from dagster._utils.error import SerializableErrorInfo

from dagster_graphql.schema.util import ResolveInfo, non_null_list


class GrapheneError(graphene.Interface):
    message = graphene.String(required=True)

    class Meta:
        name = "Error"


class GrapheneErrorChainLink(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneError,)
        name = "ErrorChainLink"

    error = graphene.NonNull(lambda: GraphenePythonError)
    isExplicitLink = graphene.NonNull(graphene.Boolean)


class GraphenePythonError(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneError,)
        name = "PythonError"

    className = graphene.Field(graphene.String)
    stack = non_null_list(graphene.String)
    cause = graphene.Field(lambda: GraphenePythonError)

    """
    A list of all recursive errors deeper in the exception stack that caused this error to be
    raised, only including explicit raises. For example, in a block of code like:
    ```
        try:
            try:
                raise Exception("Inner")
            except Exception as e:
                raise Exception("Middle") from e
        except Exception as e:
            raise Exception("Outer") from e
    ```
    The PythonError returned will correspond to Outer, with two causes - Middle and then Inner
    """
    causes = non_null_list("dagster_graphql.schema.errors.GraphenePythonError")

    """
    A list of all recursive errors deeper in the exception stack that caused this error to be
    raised, including both explicit and implicit links. For example, in a block of code like:
    ```
        try:
            try:
                raise Exception("Inner")
            except Exception as e:
                raise Exception("Middle")
        except Exception as e:
            raise Exception("Outer") from e
    ```
    The PythonError returned will correspond to Outer, with two links in the chain - one explicit (Middle) then one implicit (Inner)
    """

    errorChain = non_null_list(GrapheneErrorChainLink)

    def __init__(self, error_info):
        super().__init__()
        self._error_info = check.inst_param(error_info, "error_info", SerializableErrorInfo)
        self._message = error_info.message
        self._stack = error_info.stack
        self._className = error_info.cls_name
        self._cause = error_info.cause
        self._context = error_info.context

    def resolve_message(self, _graphene_info):
        check.invariant(
            isinstance(self, GraphenePythonError),
            f"GraphenePythonError methods called on a {type(self)} - this usually indicates"
            " that a SerializableErrorInfo was passed in where a GraphenePythonError was"
            " expected",
        )
        return self._message

    def resolve_stack(self, _graphene_info):
        check.invariant(
            isinstance(self, GraphenePythonError),
            f"GraphenePythonError methods called on a {type(self)} - this usually indicates"
            " that a SerializableErrorInfo was passed in where a GraphenePythonError was"
            " expected",
        )
        return self._stack

    def resolve_cause(self, _graphene_info):
        return GraphenePythonError(self._cause) if self._cause else None

    def resolve_context(self, _graphene_info):
        return GraphenePythonError(self._context) if self._context else None

    def resolve_className(self, _graphene_info):
        check.invariant(
            isinstance(self, GraphenePythonError),
            f"GraphenePythonError methods called on a {type(self)} - this usually indicates"
            " that a SerializableErrorInfo was passed in where a GraphenePythonError was"
            " expected",
        )
        return self._className

    def resolve_causes(self, _graphene_info: ResolveInfo):
        causes: list[GraphenePythonError] = []
        current_error = self._cause
        while current_error and len(causes) < 10:  # Sanity check the depth of the causes
            causes.append(GraphenePythonError(current_error))
            current_error = current_error.cause
        return causes

    def resolve_errorChain(self, _graphene_info):
        current_error = self._error_info
        chain = []
        while len(chain) < 10:  # Sanity check the length of the chain
            if current_error.cause:
                current_error = current_error.cause
                chain.append(
                    GrapheneErrorChainLink(
                        error=GraphenePythonError(current_error), isExplicitLink=True
                    )
                )
            elif current_error.context:
                current_error = current_error.context
                chain.append(
                    GrapheneErrorChainLink(
                        error=GraphenePythonError(current_error), isExplicitLink=False
                    )
                )
            else:
                break
        return chain


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
        from dagster_graphql.implementation.utils import JobSubsetSelector

        super().__init__()
        check.inst_param(selector, "selector", JobSubsetSelector)
        self.pipeline_name = selector.job_name
        self.repository_name = selector.repository_name
        self.repository_location_name = selector.location_name
        self.message = (
            "Could not find Pipeline "
            f"{selector.location_name}.{selector.repository_name}.{selector.job_name}"
        )


class GrapheneGraphNotFoundError(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneError,)
        name = "GraphNotFoundError"

    graph_name = graphene.NonNull(graphene.String)
    repository_name = graphene.NonNull(graphene.String)
    repository_location_name = graphene.NonNull(graphene.String)

    def __init__(self, selector):
        from dagster_graphql.implementation.utils import GraphSelector

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
        self.message = f"Preset {preset} not found in pipeline {selector.job_name}."


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
        self.message = f"Mode {mode} not found in pipeline {selector.job_name}."


class GrapheneNoModeProvidedError(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneError,)
        name = "NoModeProvidedError"

    pipeline_name = graphene.NonNull(graphene.String)

    def __init__(self, pipeline_name, mode_list):
        super().__init__()
        mode_list = check.list_param(mode_list, "mode_list", of_type=str)
        pipeline_name = check.str_param(pipeline_name, "pipeline_name")
        self.message = (
            f"No mode provided for pipeline '{pipeline_name}', which has multiple modes. Available"
            f" modes: {mode_list}"
        )


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


class GrapheneInvalidSubsetError(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneError,)
        name = "InvalidSubsetError"

    pipeline = graphene.Field(
        graphene.NonNull("dagster_graphql.schema.pipelines.pipeline.GraphenePipeline")
    )

    def __init__(self, message, pipeline):
        super().__init__()
        self.message = check.str_param(message, "message")
        self.pipeline = pipeline


class GrapheneConfigTypeNotFoundError(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneError,)
        name = "ConfigTypeNotFoundError"

    pipeline = graphene.Field(
        graphene.NonNull("dagster_graphql.schema.pipelines.pipeline.GraphenePipeline")
    )
    config_type_name = graphene.NonNull(graphene.String)


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


class GrapheneResourceNotFoundError(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneError,)
        name = "ResourceNotFoundError"

    resource_name = graphene.NonNull(graphene.String)

    def __init__(self, resource_name):
        super().__init__()
        self.resource_name = check.str_param(resource_name, "resource_name")
        self.message = f"Top-level resource {self.resource_name} could not be found."


class GrapheneSensorNotFoundError(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneError,)
        name = "SensorNotFoundError"

    sensor_name = graphene.NonNull(graphene.String)

    def __init__(self, sensor_name):
        super().__init__()
        self.sensor_name = check.str_param(sensor_name, "sensor_name")
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


class GraphenePartitionKeysNotFoundError(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneError,)
        name = "PartitionKeysNotFoundError"

    partition_keys = non_null_list(graphene.String)

    def __init__(self, partition_keys: set[str]):
        super().__init__()
        self.partition_keys = check.list_param(
            sorted(partition_keys), "partition_keys", of_type=str
        )
        self.message = f"Partition keys `{self.partition_keys}` could not be found."


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


class GrapheneDuplicateDynamicPartitionError(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneError,)
        name = "DuplicateDynamicPartitionError"

    partitions_def_name = graphene.NonNull(graphene.String)
    partition_name = graphene.NonNull(graphene.String)

    def __init__(self, partitions_def_name, partition_name):
        super().__init__()
        self.partitions_def_name = check.str_param(partitions_def_name, "partitions_def_name")
        self.partition_name = check.str_param(partition_name, "partition_name")
        self.message = (
            f"Partition {self.partition_name} already exists in dynamic partitions definition"
            f" {self.partitions_def_name}."
        )


class GrapheneUnsupportedOperationError(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneError,)
        name = "UnsupportedOperationError"

    def __init__(self, message: Optional[str] = None):
        super().__init__()
        self.message = check.str_param(message, "message") or "Unsupported operation."


types = [
    GrapheneAssetNotFoundError,
    GrapheneConflictingExecutionParamsError,
    GrapheneConfigTypeNotFoundError,
    GrapheneDagsterTypeNotFoundError,
    GrapheneError,
    GrapheneInvalidOutputError,
    GrapheneInvalidPipelineRunsFilterError,
    GrapheneInvalidStepError,
    GrapheneInvalidSubsetError,
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
    GrapheneResourceNotFoundError,
    GrapheneRunGroupNotFoundError,
    GrapheneRunNotFoundError,
    GrapheneScheduleNotFoundError,
    GrapheneSchedulerNotDefinedError,
    GrapheneSensorNotFoundError,
    GrapheneUnsupportedOperationError,
    GrapheneDuplicateDynamicPartitionError,
]
