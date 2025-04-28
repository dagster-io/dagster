from collections.abc import Sequence
from typing import Optional

import dagster._check as check
import graphene
from dagster import DefaultSensorStatus
from dagster._core.definitions.selector import SensorSelector
from dagster._core.definitions.sensor_definition import SensorType
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.remote_representation import RemoteSensor, TargetSnap
from dagster._core.remote_representation.external import CompoundID
from dagster._core.scheduler.instigation import InstigatorState, InstigatorStatus
from dagster._core.workspace.permissions import Permissions

from dagster_graphql.implementation.events import iterate_metadata_entries
from dagster_graphql.implementation.fetch_sensors import (
    get_sensor_next_tick,
    reset_sensor,
    set_sensor_cursor,
    start_sensor,
    stop_sensor,
)
from dagster_graphql.implementation.loader import RepositoryScopedBatchLoader
from dagster_graphql.implementation.utils import (
    assert_permission_for_location,
    capture_error,
    require_permission_check,
)
from dagster_graphql.schema.asset_selections import GrapheneAssetSelection
from dagster_graphql.schema.entity_key import GrapheneAssetKey
from dagster_graphql.schema.errors import (
    GraphenePythonError,
    GrapheneRepositoryNotFoundError,
    GrapheneSensorNotFoundError,
    GrapheneUnauthorizedError,
)
from dagster_graphql.schema.inputs import GrapheneSensorSelector
from dagster_graphql.schema.instigation import (
    GrapheneDryRunInstigationTick,
    GrapheneInstigationState,
    GrapheneInstigationStatus,
)
from dagster_graphql.schema.metadata import GrapheneMetadataEntry
from dagster_graphql.schema.tags import GrapheneDefinitionTag
from dagster_graphql.schema.util import ResolveInfo, non_null_list


class GrapheneTarget(graphene.ObjectType):
    pipelineName = graphene.NonNull(graphene.String)
    mode = graphene.NonNull(graphene.String)
    solidSelection = graphene.List(graphene.NonNull(graphene.String))

    class Meta:
        name = "Target"

    def __init__(self, target_snap: TargetSnap):
        self._target_snap = check.inst_param(target_snap, "target_snap", TargetSnap)
        super().__init__(
            pipelineName=target_snap.job_name,
            mode=target_snap.mode,
            solidSelection=target_snap.op_selection,
        )


class GrapheneSensorMetadata(graphene.ObjectType):
    assetKeys = graphene.List(graphene.NonNull(GrapheneAssetKey))

    class Meta:
        name = "SensorMetadata"


GrapheneSensorType = graphene.Enum.from_enum(SensorType)


class GrapheneSensor(graphene.ObjectType):
    id = graphene.NonNull(graphene.ID)
    jobOriginId = graphene.NonNull(graphene.String)
    name = graphene.NonNull(graphene.String)
    targets = graphene.List(graphene.NonNull(GrapheneTarget))
    defaultStatus = graphene.NonNull(GrapheneInstigationStatus)
    canReset = graphene.NonNull(graphene.Boolean)
    sensorState = graphene.NonNull(GrapheneInstigationState)
    minIntervalSeconds = graphene.NonNull(graphene.Int)
    description = graphene.String()
    nextTick = graphene.Field(GrapheneDryRunInstigationTick)
    metadata = graphene.NonNull(GrapheneSensorMetadata)
    sensorType = graphene.NonNull(GrapheneSensorType)
    assetSelection = graphene.Field(GrapheneAssetSelection)
    tags = non_null_list(GrapheneDefinitionTag)
    metadataEntries = non_null_list(GrapheneMetadataEntry)

    class Meta:
        name = "Sensor"

    def __init__(
        self,
        remote_sensor: RemoteSensor,
        sensor_state: Optional[InstigatorState],
        batch_loader: Optional[RepositoryScopedBatchLoader] = None,
    ):
        self._remote_sensor = check.inst_param(remote_sensor, "remote_sensor", RemoteSensor)

        # optional run loader, provided by a parent GrapheneRepository object that instantiates
        # multiple sensors
        self._batch_loader = check.opt_inst_param(
            batch_loader, "batch_loader", RepositoryScopedBatchLoader
        )

        self._stored_state = sensor_state
        self._sensor_state = self._remote_sensor.get_current_instigator_state(sensor_state)

        super().__init__(
            name=remote_sensor.name,
            jobOriginId=remote_sensor.get_remote_origin_id(),
            minIntervalSeconds=remote_sensor.min_interval_seconds,
            description=remote_sensor.description,
            targets=[GrapheneTarget(target) for target in remote_sensor.get_targets()],
            metadata=GrapheneSensorMetadata(
                assetKeys=remote_sensor.metadata.asset_keys if remote_sensor.metadata else None
            ),
            sensorType=remote_sensor.sensor_type.value,
            assetSelection=GrapheneAssetSelection(
                asset_selection=remote_sensor.asset_selection,
                repository_handle=remote_sensor.handle.repository_handle,
            )
            if remote_sensor.asset_selection
            else None,
        )

    def resolve_id(self, _) -> str:
        return self._remote_sensor.get_compound_id().to_string()

    def resolve_defaultStatus(self, _graphene_info: ResolveInfo):
        default_sensor_status = self._remote_sensor.default_status

        if default_sensor_status == DefaultSensorStatus.RUNNING:
            return GrapheneInstigationStatus.RUNNING
        elif default_sensor_status == DefaultSensorStatus.STOPPED:
            return GrapheneInstigationStatus.STOPPED

    def resolve_canReset(self, _graphene_info: ResolveInfo):
        return bool(
            self._stored_state and self._stored_state.status != InstigatorStatus.DECLARED_IN_CODE
        )

    def resolve_sensorState(self, _graphene_info: ResolveInfo):
        # forward the batch run loader to the instigation state, which provides the sensor runs
        return GrapheneInstigationState(self._sensor_state, self._batch_loader)

    def resolve_nextTick(self, graphene_info: ResolveInfo):
        return get_sensor_next_tick(graphene_info, self._sensor_state)

    def resolve_tags(self, _graphene_info: ResolveInfo) -> Sequence[GrapheneDefinitionTag]:
        return [
            GrapheneDefinitionTag(key, value)
            for key, value in (self._remote_sensor.tags or {}).items()
        ]

    def resolve_metadataEntries(
        self, _graphene_info: ResolveInfo
    ) -> Sequence[GrapheneMetadataEntry]:
        # Standard metadata is nested under the non-standard ExternalSensorMetadata object for
        # backcompat reasons.
        sensor_metadata = self._remote_sensor.metadata
        if sensor_metadata and sensor_metadata.standard_metadata:
            return list(iterate_metadata_entries(sensor_metadata.standard_metadata))
        else:
            return []


class GrapheneSensorOrError(graphene.Union):
    class Meta:
        types = (
            GrapheneSensor,
            GrapheneSensorNotFoundError,
            GrapheneUnauthorizedError,
            GraphenePythonError,
        )
        name = "SensorOrError"


class GrapheneSensors(graphene.ObjectType):
    results = non_null_list(GrapheneSensor)

    class Meta:
        name = "Sensors"


class GrapheneSensorsOrError(graphene.Union):
    class Meta:
        types = (GrapheneSensors, GrapheneRepositoryNotFoundError, GraphenePythonError)
        name = "SensorsOrError"


class GrapheneStartSensorMutation(graphene.Mutation):
    """Enable a sensor to launch runs for a job based on external state change."""

    Output = graphene.NonNull(GrapheneSensorOrError)

    class Arguments:
        sensor_selector = graphene.NonNull(GrapheneSensorSelector)

    class Meta:
        name = "StartSensorMutation"

    @capture_error
    @require_permission_check(Permissions.UPDATE_SENSOR_CURSOR)
    def mutate(self, graphene_info: ResolveInfo, sensor_selector):
        selector = SensorSelector.from_graphql_input(sensor_selector)
        assert_permission_for_location(
            graphene_info, Permissions.UPDATE_SENSOR_CURSOR, selector.location_name
        )
        return start_sensor(graphene_info, selector)


class GrapheneStopSensorMutationResult(graphene.ObjectType):
    instigationState = graphene.Field(GrapheneInstigationState)

    class Meta:
        name = "StopSensorMutationResult"

    def __init__(self, instigator_state):
        super().__init__()
        self._instigator_state = check.inst_param(
            instigator_state, "instigator_state", InstigatorState
        )

    def resolve_instigationState(self, _graphene_info: ResolveInfo):
        return GrapheneInstigationState(instigator_state=self._instigator_state)


class GrapheneStopSensorMutationResultOrError(graphene.Union):
    class Meta:
        types = (GrapheneStopSensorMutationResult, GrapheneUnauthorizedError, GraphenePythonError)
        name = "StopSensorMutationResultOrError"


class GrapheneStopSensorMutation(graphene.Mutation):
    """Disable a sensor from launching runs for a job."""

    Output = graphene.NonNull(GrapheneStopSensorMutationResultOrError)

    class Arguments:
        id = graphene.Argument(graphene.String)  # Sensor / InstigationState id

        # "job" legacy name for instigators, predates current Job
        job_origin_id = graphene.Argument(graphene.String)
        job_selector_id = graphene.Argument(graphene.String)

    class Meta:
        name = "StopSensorMutation"

    @capture_error
    @require_permission_check(Permissions.EDIT_SENSOR)
    def mutate(
        self,
        graphene_info: ResolveInfo,
        id: Optional[str] = None,
        job_origin_id: Optional[str] = None,
        job_selector_id: Optional[str] = None,
    ):
        if id:
            cid = CompoundID.from_string(id)
            sensor_origin_id = cid.remote_origin_id
            sensor_selector_id = cid.selector_id
        elif job_origin_id and CompoundID.is_valid_string(job_origin_id):
            # cross-push handle if InstigationState.id being passed through as origin id
            cid = CompoundID.from_string(job_origin_id)
            sensor_origin_id = cid.remote_origin_id
            sensor_selector_id = cid.selector_id
        elif job_origin_id is None or job_selector_id is None:
            raise DagsterInvariantViolationError("Must specify id or jobOriginId and jobSelectorId")
        else:
            sensor_origin_id = job_origin_id
            sensor_selector_id = job_selector_id

        return stop_sensor(graphene_info, sensor_origin_id, sensor_selector_id)


class GrapheneResetSensorMutation(graphene.Mutation):
    """Reset a sensor to its status defined in code, otherwise disable it from launching runs for a job."""

    Output = graphene.NonNull(GrapheneSensorOrError)

    class Arguments:
        sensor_selector = graphene.NonNull(GrapheneSensorSelector)

    class Meta:
        name = "ResetSensorMutation"

    @capture_error
    @require_permission_check(Permissions.EDIT_SENSOR)
    def mutate(self, graphene_info: ResolveInfo, sensor_selector):
        selector = SensorSelector.from_graphql_input(sensor_selector)

        assert_permission_for_location(
            graphene_info, Permissions.EDIT_SENSOR, selector.location_name
        )

        return reset_sensor(graphene_info, selector)


class GrapheneSetSensorCursorMutation(graphene.Mutation):
    """Set a cursor for a sensor to track state across evaluations."""

    Output = graphene.NonNull(GrapheneSensorOrError)

    class Arguments:
        sensor_selector = graphene.NonNull(GrapheneSensorSelector)
        cursor = graphene.String()

    class Meta:
        name = "SetSensorCursorMutation"

    @capture_error
    def mutate(self, graphene_info: ResolveInfo, sensor_selector, cursor=None):
        selector = SensorSelector.from_graphql_input(sensor_selector)
        assert_permission_for_location(
            graphene_info, Permissions.UPDATE_SENSOR_CURSOR, selector.location_name
        )
        return set_sensor_cursor(graphene_info, selector, cursor)


types = [
    GrapheneSensor,
    GrapheneSensorOrError,
    GrapheneSensors,
    GrapheneSensorsOrError,
    GrapheneStopSensorMutation,
    GrapheneStopSensorMutationResult,
    GrapheneStopSensorMutationResultOrError,
    GrapheneStopSensorMutation,
    GrapheneSetSensorCursorMutation,
    GrapheneResetSensorMutation,
]
