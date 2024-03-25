from datetime import datetime
from functools import cached_property
from threading import RLock
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Callable,
    Dict,
    Iterable,
    Iterator,
    List,
    Mapping,
    Optional,
    Sequence,
    Union,
)

import dagster._check as check
from dagster import AssetSelection
from dagster._config.snap import ConfigFieldSnap, ConfigSchemaSnapshot
from dagster._core.definitions.asset_check_spec import AssetCheckKey
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.metadata import (
    MetadataValue,
)
from dagster._core.definitions.run_request import InstigatorType
from dagster._core.definitions.schedule_definition import DefaultScheduleStatus
from dagster._core.definitions.selector import (
    InstigatorSelector,
    RepositorySelector,
    ScheduleSelector,
    SensorSelector,
)
from dagster._core.definitions.sensor_definition import (
    DEFAULT_SENSOR_DAEMON_INTERVAL,
    DefaultSensorStatus,
    SensorType,
)
from dagster._core.execution.plan.handle import ResolvedFromDynamicStepHandle, StepHandle
from dagster._core.instance import DagsterInstance
from dagster._core.origin import JobPythonOrigin, RepositoryPythonOrigin
from dagster._core.remote_representation.origin import (
    ExternalInstigatorOrigin,
    ExternalJobOrigin,
    ExternalPartitionSetOrigin,
    ExternalRepositoryOrigin,
)
from dagster._core.snap import ExecutionPlanSnapshot
from dagster._core.snap.job_snapshot import JobSnapshot
from dagster._core.utils import toposort
from dagster._serdes import create_snapshot_id
from dagster._utils.cached_method import cached_method
from dagster._utils.schedules import schedule_execution_time_iterator

from .external_data import (
    DEFAULT_MODE_NAME,
    EnvVarConsumer,
    ExternalAssetCheck,
    ExternalAssetNode,
    ExternalJobData,
    ExternalJobRef,
    ExternalPartitionSetData,
    ExternalPresetData,
    ExternalRepositoryData,
    ExternalResourceData,
    ExternalResourceValue,
    ExternalScheduleData,
    ExternalSensorData,
    ExternalSensorMetadata,
    ExternalTargetData,
    NestedResource,
    ResourceJobUsageEntry,
)
from .handle import InstigatorHandle, JobHandle, PartitionSetHandle, RepositoryHandle
from .job_index import JobIndex
from .represented import RepresentedJob

if TYPE_CHECKING:
    from dagster._core.definitions.remote_asset_graph import RemoteAssetGraph
    from dagster._core.scheduler.instigation import InstigatorState
    from dagster._core.snap.execution_plan_snapshot import ExecutionStepSnap


class ExternalRepository:
    """ExternalRepository is a object that represents a loaded repository definition that
    is resident in another process or container. Host processes such as dagster-webserver use
    objects such as these to interact with user-defined artifacts.
    """

    def __init__(
        self,
        external_repository_data: ExternalRepositoryData,
        repository_handle: RepositoryHandle,
        instance: DagsterInstance,
        ref_to_data_fn: Optional[Callable[[ExternalJobRef], ExternalJobData]] = None,
    ):
        self.external_repository_data = check.inst_param(
            external_repository_data, "external_repository_data", ExternalRepositoryData
        )

        self._instance = instance

        if external_repository_data.external_job_datas is not None:
            self._job_map: Dict[str, Union[ExternalJobData, ExternalJobRef]] = {
                d.name: d for d in external_repository_data.external_job_datas
            }
            self._deferred_snapshots: bool = False
            self._ref_to_data_fn = None
        elif external_repository_data.external_job_refs is not None:
            self._job_map = {r.name: r for r in external_repository_data.external_job_refs}
            self._deferred_snapshots = True
            if ref_to_data_fn is None:
                check.failed(
                    "ref_to_data_fn is required when ExternalRepositoryData is loaded with deferred"
                    " snapshots"
                )

            self._ref_to_data_fn = ref_to_data_fn
        else:
            check.failed("invalid state - expected job data or refs")

        self._handle = check.inst_param(repository_handle, "repository_handle", RepositoryHandle)

        self._asset_jobs: Dict[str, List[ExternalAssetNode]] = {}
        for asset_node in external_repository_data.external_asset_graph_data:
            for job_name in asset_node.job_names:
                self._asset_jobs.setdefault(job_name, []).append(asset_node)

        self._asset_check_jobs: Dict[str, List[ExternalAssetCheck]] = {}
        for asset_check in external_repository_data.external_asset_checks or []:
            for job_name in asset_check.job_names:
                self._asset_check_jobs.setdefault(job_name, []).append(asset_check)

        # memoize job instances to share instances
        self._memo_lock: RLock = RLock()
        self._cached_jobs: Dict[str, ExternalJob] = {}

    @property
    def name(self) -> str:
        return self.external_repository_data.name

    @property
    @cached_method
    def _external_schedules(self) -> Dict[str, "ExternalSchedule"]:
        return {
            external_schedule_data.name: ExternalSchedule(external_schedule_data, self._handle)
            for external_schedule_data in self.external_repository_data.external_schedule_datas
        }

    def has_external_schedule(self, schedule_name: str) -> bool:
        return schedule_name in self._external_schedules

    def get_external_schedule(self, schedule_name: str) -> "ExternalSchedule":
        return self._external_schedules[schedule_name]

    def get_external_schedules(self) -> Sequence["ExternalSchedule"]:
        return list(self._external_schedules.values())

    @property
    @cached_method
    def _external_resources(self) -> Dict[str, "ExternalResource"]:
        return {
            external_resource_data.name: ExternalResource(external_resource_data, self._handle)
            for external_resource_data in (
                self.external_repository_data.external_resource_data or []
            )
        }

    def has_external_resource(self, resource_name: str) -> bool:
        return resource_name in self._external_resources

    def get_external_resource(self, resource_name: str) -> "ExternalResource":
        return self._external_resources[resource_name]

    def get_external_resources(self) -> Iterable["ExternalResource"]:
        return self._external_resources.values()

    @property
    def _utilized_env_vars(self) -> Mapping[str, Sequence[EnvVarConsumer]]:
        return self.external_repository_data.utilized_env_vars or {}

    def get_utilized_env_vars(self) -> Mapping[str, Sequence[EnvVarConsumer]]:
        return self._utilized_env_vars

    def get_default_auto_materialize_sensor_name(self):
        return "default_auto_materialize_sensor"

    @property
    @cached_method
    def _external_sensors(self) -> Dict[str, "ExternalSensor"]:
        sensor_datas = {
            external_sensor_data.name: ExternalSensor(external_sensor_data, self._handle)
            for external_sensor_data in self.external_repository_data.external_sensor_datas
        }

        if self._instance.auto_materialize_use_sensors:
            asset_graph = self.asset_graph

            has_any_auto_observe_source_assets = False

            existing_auto_materialize_sensors = {
                sensor_name: sensor
                for sensor_name, sensor in sensor_datas.items()
                if sensor.sensor_type == SensorType.AUTO_MATERIALIZE
            }

            covered_asset_keys = set()
            for sensor in existing_auto_materialize_sensors.values():
                covered_asset_keys = covered_asset_keys.union(
                    check.not_none(sensor.asset_selection).resolve(asset_graph)
                )

            default_sensor_asset_keys = set()

            for asset_key in asset_graph.materializable_asset_keys:
                if not asset_graph.get(asset_key).auto_materialize_policy:
                    continue

                if asset_key not in covered_asset_keys:
                    default_sensor_asset_keys.add(asset_key)

            for asset_key in asset_graph.observable_asset_keys:
                if asset_graph.get(asset_key).auto_observe_interval_minutes is None:
                    continue

                has_any_auto_observe_source_assets = True

                if asset_key not in covered_asset_keys:
                    default_sensor_asset_keys.add(asset_key)

            if default_sensor_asset_keys:
                # Use AssetSelection.all if the default sensor is the only sensor - otherwise
                # enumerate the assets that are not already included in some other
                # non-default sensor
                default_sensor_asset_selection = AssetSelection.all(
                    include_sources=has_any_auto_observe_source_assets
                )

                for sensor in existing_auto_materialize_sensors.values():
                    default_sensor_asset_selection = (
                        default_sensor_asset_selection - check.not_none(sensor.asset_selection)
                    )

                default_sensor_data = ExternalSensorData(
                    name=self.get_default_auto_materialize_sensor_name(),
                    job_name=None,
                    op_selection=None,
                    asset_selection=default_sensor_asset_selection,
                    mode=None,
                    min_interval=30,
                    description=None,
                    target_dict={},
                    metadata=None,
                    default_status=None,
                    sensor_type=SensorType.AUTO_MATERIALIZE,
                    run_tags=None,
                )
                sensor_datas[default_sensor_data.name] = ExternalSensor(
                    default_sensor_data, self._handle
                )

        return sensor_datas

    def has_external_sensor(self, sensor_name: str) -> bool:
        return sensor_name in self._external_sensors

    def get_external_sensor(self, sensor_name: str) -> "ExternalSensor":
        return self._external_sensors[sensor_name]

    def get_external_sensors(self) -> Sequence["ExternalSensor"]:
        return list(self._external_sensors.values())

    @property
    @cached_method
    def _external_partition_sets(self) -> Dict[str, "ExternalPartitionSet"]:
        return {
            external_partition_set_data.name: ExternalPartitionSet(
                external_partition_set_data, self._handle
            )
            for external_partition_set_data in self.external_repository_data.external_partition_set_datas
        }

    def has_external_partition_set(self, partition_set_name: str) -> bool:
        return partition_set_name in self._external_partition_sets

    def get_external_partition_set(self, partition_set_name: str) -> "ExternalPartitionSet":
        return self._external_partition_sets[partition_set_name]

    def get_external_partition_sets(self) -> Sequence["ExternalPartitionSet"]:
        return list(self._external_partition_sets.values())

    def has_external_job(self, job_name: str) -> bool:
        return job_name in self._job_map

    def get_full_external_job(self, job_name: str) -> "ExternalJob":
        check.str_param(job_name, "job_name")
        check.invariant(
            self.has_external_job(job_name), f'No external job named "{job_name}" found'
        )
        with self._memo_lock:
            if job_name not in self._cached_jobs:
                job_item = self._job_map[job_name]
                if self._deferred_snapshots:
                    if not isinstance(job_item, ExternalJobRef):
                        check.failed("unexpected job item")
                    external_ref = job_item
                    external_data: Optional[ExternalJobData] = None
                else:
                    if not isinstance(job_item, ExternalJobData):
                        check.failed("unexpected job item")
                    external_data = job_item
                    external_ref = None

                self._cached_jobs[job_name] = ExternalJob(
                    external_job_data=external_data,
                    repository_handle=self.handle,
                    external_job_ref=external_ref,
                    ref_to_data_fn=self._ref_to_data_fn,
                )

            return self._cached_jobs[job_name]

    def get_all_external_jobs(self) -> Sequence["ExternalJob"]:
        return [self.get_full_external_job(pn) for pn in self._job_map]

    @property
    def handle(self) -> RepositoryHandle:
        return self._handle

    @property
    def selector_id(self) -> str:
        return create_snapshot_id(
            RepositorySelector(self._handle.location_name, self._handle.repository_name)
        )

    def get_external_origin(self) -> ExternalRepositoryOrigin:
        return self.handle.get_external_origin()

    def get_python_origin(self) -> RepositoryPythonOrigin:
        return self.handle.get_python_origin()

    def get_external_origin_id(self) -> str:
        """A means of identifying the repository this ExternalRepository represents based on
        where it came from.
        """
        return self.get_external_origin().get_id()

    def get_external_asset_nodes(
        self, job_name: Optional[str] = None
    ) -> Sequence[ExternalAssetNode]:
        return (
            self.external_repository_data.external_asset_graph_data
            if job_name is None
            else self._asset_jobs.get(job_name, [])
        )

    def get_external_asset_node(self, asset_key: AssetKey) -> Optional[ExternalAssetNode]:
        matching = [
            asset_node
            for asset_node in self.external_repository_data.external_asset_graph_data
            if asset_node.asset_key == asset_key
        ]
        return matching[0] if matching else None

    def get_external_asset_checks(
        self, job_name: Optional[str] = None
    ) -> Sequence[ExternalAssetCheck]:
        if job_name:
            return self._asset_check_jobs.get(job_name, [])
        else:
            return self.external_repository_data.external_asset_checks or []

    def get_display_metadata(self) -> Mapping[str, str]:
        return self.handle.display_metadata

    @cached_property
    def asset_graph(self) -> "RemoteAssetGraph":
        """Returns a repository scoped RemoteAssetGraph."""
        from dagster._core.definitions.remote_asset_graph import RemoteAssetGraph

        return RemoteAssetGraph.from_repository_handles_and_external_asset_nodes(
            repo_handle_external_asset_nodes=[
                (self.handle, asset_node) for asset_node in self.get_external_asset_nodes()
            ],
            external_asset_checks=self.get_external_asset_checks(),
        )


class ExternalJob(RepresentedJob):
    """ExternalJob is a object that represents a loaded job definition that
    is resident in another process or container. Host processes such as dagster-webserver use
    objects such as these to interact with user-defined artifacts.
    """

    def __init__(
        self,
        external_job_data: Optional[ExternalJobData],
        repository_handle: RepositoryHandle,
        external_job_ref: Optional[ExternalJobRef] = None,
        ref_to_data_fn: Optional[Callable[[ExternalJobRef], ExternalJobData]] = None,
    ):
        check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
        check.opt_inst_param(external_job_data, "external_job_data", ExternalJobData)

        self._repository_handle = repository_handle

        self._memo_lock = RLock()
        self._index: Optional[JobIndex] = None

        self._data = external_job_data
        self._ref = external_job_ref
        self._ref_to_data_fn = ref_to_data_fn

        if external_job_data:
            self._active_preset_dict = {ap.name: ap for ap in external_job_data.active_presets}
            self._name = external_job_data.name
            self._snapshot_id = self._job_index.job_snapshot_id

        elif external_job_ref:
            self._active_preset_dict = {ap.name: ap for ap in external_job_ref.active_presets}
            self._name = external_job_ref.name
            if ref_to_data_fn is None:
                check.failed("ref_to_data_fn must be passed when using deferred snapshots")
            self._snapshot_id = external_job_ref.snapshot_id
        else:
            check.failed("Expected either job data or ref, got neither")

        self._handle = JobHandle(self._name, repository_handle)

    @property
    def _job_index(self) -> JobIndex:
        with self._memo_lock:
            if self._index is None:
                self._index = JobIndex(
                    self.external_job_data.job_snapshot,
                    self.external_job_data.parent_job_snapshot,
                )
            return self._index

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self):
        return self._job_index.job_snapshot.description

    @property
    def node_names_in_topological_order(self):
        return self._job_index.job_snapshot.node_names_in_topological_order

    @property
    def external_job_data(self):
        with self._memo_lock:
            if self._data is None:
                if self._ref is None or self._ref_to_data_fn is None:
                    check.failed("unexpected state - unable to load data from ref")
                self._data = self._ref_to_data_fn(self._ref)

            return self._data

    @property
    def repository_handle(self) -> RepositoryHandle:
        return self._repository_handle

    @property
    def op_selection(self) -> Optional[Sequence[str]]:
        return (
            self._job_index.job_snapshot.lineage_snapshot.op_selection
            if self._job_index.job_snapshot.lineage_snapshot
            else None
        )

    @property
    def resolved_op_selection(self) -> Optional[AbstractSet[str]]:
        return (
            self._job_index.job_snapshot.lineage_snapshot.resolved_op_selection
            if self._job_index.job_snapshot.lineage_snapshot
            else None
        )

    @property
    def asset_selection(self) -> Optional[AbstractSet[AssetKey]]:
        return (
            self._job_index.job_snapshot.lineage_snapshot.asset_selection
            if self._job_index.job_snapshot.lineage_snapshot
            else None
        )

    @property
    def asset_check_selection(self) -> Optional[AbstractSet[AssetCheckKey]]:
        return (
            self._job_index.job_snapshot.lineage_snapshot.asset_check_selection
            if self._job_index.job_snapshot.lineage_snapshot
            else None
        )

    @property
    def active_presets(self) -> Sequence[ExternalPresetData]:
        return list(self._active_preset_dict.values())

    @property
    def node_names(self) -> Sequence[str]:
        return self._job_index.job_snapshot.node_names

    def has_node_invocation(self, node_name: str):
        check.str_param(node_name, "node_name")
        return self._job_index.has_node_invocation(node_name)

    def has_preset(self, preset_name: str) -> bool:
        check.str_param(preset_name, "preset_name")
        return preset_name in self._active_preset_dict

    def get_preset(self, preset_name: str) -> ExternalPresetData:
        check.str_param(preset_name, "preset_name")
        return self._active_preset_dict[preset_name]

    @property
    def root_config_key(self) -> Optional[str]:
        return self.get_mode_def_snap(DEFAULT_MODE_NAME).root_config_key

    @property
    def tags(self) -> Mapping[str, object]:
        return self._job_index.job_snapshot.tags

    @property
    def metadata(self) -> Mapping[str, MetadataValue]:
        return self._job_index.job_snapshot.metadata

    @property
    def job_snapshot(self) -> JobSnapshot:
        return self._job_index.job_snapshot

    @property
    def computed_job_snapshot_id(self) -> str:
        return self._snapshot_id

    @property
    def identifying_job_snapshot_id(self) -> str:
        return self._snapshot_id

    @property
    def handle(self) -> JobHandle:
        return self._handle

    def get_python_origin(self) -> JobPythonOrigin:
        repository_python_origin = self.repository_handle.get_python_origin()
        return JobPythonOrigin(self.name, repository_python_origin)

    def get_external_origin(self) -> ExternalJobOrigin:
        return self.handle.get_external_origin()

    def get_external_origin_id(self) -> str:
        return self.get_external_origin().get_id()


class ExternalExecutionPlan:
    """ExternalExecution is a object that represents an execution plan that
    was compiled in another process or persisted in an instance.
    """

    def __init__(self, execution_plan_snapshot: ExecutionPlanSnapshot):
        self.execution_plan_snapshot = check.inst_param(
            execution_plan_snapshot, "execution_plan_snapshot", ExecutionPlanSnapshot
        )

        self._step_index: Mapping[str, ExecutionStepSnap] = {
            step.key: step for step in self.execution_plan_snapshot.steps
        }

        self._step_keys_in_plan: AbstractSet[str] = (
            set(execution_plan_snapshot.step_keys_to_execute)
            if execution_plan_snapshot.step_keys_to_execute
            else set(self._step_index.keys())
        )

        self._deps = None
        self._topological_steps = None
        self._topological_step_levels = None

    @property
    def step_keys_in_plan(self) -> Sequence[str]:
        return list(self._step_keys_in_plan)

    def has_step(self, key: str) -> bool:
        check.str_param(key, "key")
        handle = StepHandle.parse_from_key(key)
        if isinstance(handle, ResolvedFromDynamicStepHandle):
            return handle.unresolved_form.to_key() in self._step_index
        return key in self._step_index

    def get_step_by_key(self, key: str):
        check.str_param(key, "key")
        return self._step_index[key]

    def get_steps_in_plan(self):
        return [self._step_index[sk] for sk in self._step_keys_in_plan]

    def key_in_plan(self, key: str):
        return key in self._step_keys_in_plan

    # Everything below this line is a near-copy of the equivalent methods on
    # ExecutionPlan. We should resolve this, probably eventually by using the
    # snapshots to support the existing ExecutionPlan methods.
    # https://github.com/dagster-io/dagster/issues/2462
    def execution_deps(self):
        if self._deps is None:
            deps = {}

            for key in self._step_keys_in_plan:
                deps[key] = set()

            for key in self._step_keys_in_plan:
                step = self._step_index[key]
                for step_input in step.inputs:
                    deps[step.key].update(
                        {
                            output_handle.step_key
                            for output_handle in step_input.upstream_output_handles
                        }.intersection(self._step_keys_in_plan)
                    )
            self._deps = deps

        return self._deps

    def topological_steps(self):
        if self._topological_steps is None:
            self._topological_steps = [
                step for step_level in self.topological_step_levels() for step in step_level
            ]

        return self._topological_steps

    def topological_step_levels(self):
        if self._topological_step_levels is None:
            self._topological_step_levels = [
                [self._step_index[step_key] for step_key in sorted(step_key_level)]
                for step_key_level in toposort(self.execution_deps())
            ]

        return self._topological_step_levels


class ExternalResource:
    """Represents a top-level resource in a repository, e.g. one passed through the Definitions API."""

    def __init__(self, external_resource_data: ExternalResourceData, handle: RepositoryHandle):
        self._external_resource_data = check.inst_param(
            external_resource_data, "external_resource_data", ExternalResourceData
        )
        self._handle = InstigatorHandle(
            self._external_resource_data.name, check.inst_param(handle, "handle", RepositoryHandle)
        )

    @property
    def name(self) -> str:
        return self._external_resource_data.name

    @property
    def description(self) -> Optional[str]:
        return self._external_resource_data.resource_snapshot.description

    @property
    def config_field_snaps(self) -> List[ConfigFieldSnap]:
        return self._external_resource_data.config_field_snaps

    @property
    def configured_values(self) -> Dict[str, ExternalResourceValue]:
        return self._external_resource_data.configured_values

    @property
    def config_schema_snap(self) -> ConfigSchemaSnapshot:
        return self._external_resource_data.config_schema_snap

    @property
    def nested_resources(self) -> Dict[str, NestedResource]:
        return self._external_resource_data.nested_resources

    @property
    def parent_resources(self) -> Dict[str, str]:
        return self._external_resource_data.parent_resources

    @property
    def resource_type(self) -> str:
        return self._external_resource_data.resource_type

    @property
    def is_top_level(self) -> bool:
        return self._external_resource_data.is_top_level

    @property
    def asset_keys_using(self) -> List[AssetKey]:
        return self._external_resource_data.asset_keys_using

    @property
    def job_ops_using(self) -> List[ResourceJobUsageEntry]:
        return self._external_resource_data.job_ops_using

    @property
    def schedules_using(self) -> List[str]:
        return self._external_resource_data.schedules_using

    @property
    def sensors_using(self) -> List[str]:
        return self._external_resource_data.sensors_using

    @property
    def is_dagster_maintained(self) -> bool:
        return self._external_resource_data.dagster_maintained


class ExternalSchedule:
    def __init__(self, external_schedule_data: ExternalScheduleData, handle: RepositoryHandle):
        self._external_schedule_data = check.inst_param(
            external_schedule_data, "external_schedule_data", ExternalScheduleData
        )
        self._handle = InstigatorHandle(
            self._external_schedule_data.name, check.inst_param(handle, "handle", RepositoryHandle)
        )

    @property
    def name(self) -> str:
        return self._external_schedule_data.name

    @property
    def cron_schedule(self) -> Union[str, Sequence[str]]:
        return self._external_schedule_data.cron_schedule

    @property
    def execution_timezone(self) -> Optional[str]:
        return self._external_schedule_data.execution_timezone

    @property
    def op_selection(self) -> Optional[Sequence[str]]:
        return self._external_schedule_data.op_selection

    @property
    def job_name(self) -> str:
        return self._external_schedule_data.job_name

    @property
    def mode(self) -> Optional[str]:
        return self._external_schedule_data.mode

    @property
    def description(self) -> Optional[str]:
        return self._external_schedule_data.description

    @property
    def partition_set_name(self) -> Optional[str]:
        return self._external_schedule_data.partition_set_name

    @property
    def environment_vars(self) -> Optional[Mapping[str, str]]:
        return self._external_schedule_data.environment_vars

    @property
    def handle(self) -> InstigatorHandle:
        return self._handle

    def get_external_origin(self) -> ExternalInstigatorOrigin:
        return self.handle.get_external_origin()

    def get_external_origin_id(self) -> str:
        return self.get_external_origin().get_id()

    @property
    def selector(self) -> InstigatorSelector:
        return InstigatorSelector(
            self.handle.location_name,
            self.handle.repository_name,
            self._external_schedule_data.name,
        )

    @property
    def schedule_selector(self) -> ScheduleSelector:
        return ScheduleSelector(
            self.handle.location_name,
            self.handle.repository_name,
            self._external_schedule_data.name,
        )

    @property
    def selector_id(self) -> str:
        return create_snapshot_id(self.selector)

    @property
    def default_status(self) -> DefaultScheduleStatus:
        return self._external_schedule_data.default_status or DefaultScheduleStatus.STOPPED

    def get_current_instigator_state(
        self, stored_state: Optional["InstigatorState"]
    ) -> "InstigatorState":
        from dagster._core.scheduler.instigation import (
            InstigatorState,
            InstigatorStatus,
            ScheduleInstigatorData,
        )

        if self.default_status == DefaultScheduleStatus.RUNNING:
            if stored_state:
                return stored_state

            return InstigatorState(
                self.get_external_origin(),
                InstigatorType.SCHEDULE,
                InstigatorStatus.DECLARED_IN_CODE,
                ScheduleInstigatorData(self.cron_schedule, start_timestamp=None),
            )
        else:
            # Ignore DECLARED_IN_CODE states in the DB if the default status
            # isn't DefaultScheduleStatus.RUNNING - this would indicate that the schedule's
            # default has been changed in code but there's still a lingering DECLARED_IN_CODE
            # row in the database that can be ignored
            if stored_state:
                return (
                    stored_state.with_status(InstigatorStatus.STOPPED)
                    if stored_state.status == InstigatorStatus.DECLARED_IN_CODE
                    else stored_state
                )

            return InstigatorState(
                self.get_external_origin(),
                InstigatorType.SCHEDULE,
                InstigatorStatus.STOPPED,
                ScheduleInstigatorData(self.cron_schedule, start_timestamp=None),
            )

    def execution_time_iterator(
        self, start_timestamp: float, ascending: bool = True
    ) -> Iterator[datetime]:
        return schedule_execution_time_iterator(
            start_timestamp, self.cron_schedule, self.execution_timezone, ascending
        )


class ExternalSensor:
    def __init__(self, external_sensor_data: ExternalSensorData, handle: RepositoryHandle):
        self._external_sensor_data = check.inst_param(
            external_sensor_data, "external_sensor_data", ExternalSensorData
        )
        self._handle = InstigatorHandle(
            self._external_sensor_data.name, check.inst_param(handle, "handle", RepositoryHandle)
        )

    @property
    def name(self) -> str:
        return self._external_sensor_data.name

    @property
    def handle(self) -> InstigatorHandle:
        return self._handle

    @property
    def job_name(self) -> Optional[str]:
        target = self._get_single_target()
        return target.job_name if target else None

    @property
    def asset_selection(self) -> Optional[AssetSelection]:
        return self._external_sensor_data.asset_selection

    @property
    def mode(self) -> Optional[str]:
        target = self._get_single_target()
        return target.mode if target else None

    @property
    def op_selection(self) -> Optional[Sequence[str]]:
        target = self._get_single_target()
        return target.op_selection if target else None

    def _get_single_target(self) -> Optional[ExternalTargetData]:
        if self._external_sensor_data.target_dict:
            return next(iter(self._external_sensor_data.target_dict.values()))
        else:
            return None

    def get_target_data(self, job_name: Optional[str] = None) -> Optional[ExternalTargetData]:
        if job_name:
            return self._external_sensor_data.target_dict[job_name]
        else:
            return self._get_single_target()

    def get_external_targets(self) -> Sequence[ExternalTargetData]:
        return list(self._external_sensor_data.target_dict.values())

    @property
    def description(self) -> Optional[str]:
        return self._external_sensor_data.description

    @property
    def min_interval_seconds(self) -> int:
        if (
            isinstance(self._external_sensor_data, ExternalSensorData)
            and self._external_sensor_data.min_interval
        ):
            return self._external_sensor_data.min_interval
        return DEFAULT_SENSOR_DAEMON_INTERVAL

    @property
    def run_tags(self) -> Mapping[str, str]:
        return self._external_sensor_data.run_tags

    def get_external_origin(self) -> ExternalInstigatorOrigin:
        return self._handle.get_external_origin()

    def get_external_origin_id(self) -> str:
        return self.get_external_origin().get_id()

    @property
    def selector(self) -> InstigatorSelector:
        return InstigatorSelector(
            self.handle.location_name,
            self.handle.repository_name,
            self._external_sensor_data.name,
        )

    @property
    def sensor_selector(self) -> SensorSelector:
        return SensorSelector(
            self.handle.location_name,
            self.handle.repository_name,
            self._external_sensor_data.name,
        )

    @property
    def selector_id(self) -> str:
        return create_snapshot_id(self.selector)

    @property
    def sensor_type(self) -> SensorType:
        return self._external_sensor_data.sensor_type or SensorType.UNKNOWN

    def get_current_instigator_state(
        self, stored_state: Optional["InstigatorState"]
    ) -> "InstigatorState":
        from dagster._core.scheduler.instigation import (
            InstigatorState,
            InstigatorStatus,
            SensorInstigatorData,
        )

        if self.default_status == DefaultSensorStatus.RUNNING:
            return (
                stored_state
                if stored_state
                else InstigatorState(
                    self.get_external_origin(),
                    InstigatorType.SENSOR,
                    InstigatorStatus.DECLARED_IN_CODE,
                    SensorInstigatorData(
                        min_interval=self.min_interval_seconds,
                        sensor_type=self.sensor_type,
                    ),
                )
            )
        else:
            # Ignore DECLARED_IN_CODE states in the DB if the default status
            # isn't DefaultSensorStatus.RUNNING - this would indicate that the schedule's
            # default has changed
            if stored_state:
                return (
                    stored_state.with_status(InstigatorStatus.STOPPED)
                    if stored_state.status == InstigatorStatus.DECLARED_IN_CODE
                    else stored_state
                )

            return InstigatorState(
                self.get_external_origin(),
                InstigatorType.SENSOR,
                InstigatorStatus.STOPPED,
                SensorInstigatorData(
                    min_interval=self.min_interval_seconds,
                    sensor_type=self.sensor_type,
                ),
            )

    @property
    def metadata(self) -> Optional[ExternalSensorMetadata]:
        return self._external_sensor_data.metadata

    @property
    def default_status(self) -> DefaultSensorStatus:
        return self._external_sensor_data.default_status or DefaultSensorStatus.STOPPED


class ExternalPartitionSet:
    def __init__(
        self, external_partition_set_data: ExternalPartitionSetData, handle: RepositoryHandle
    ):
        self._external_partition_set_data = check.inst_param(
            external_partition_set_data, "external_partition_set_data", ExternalPartitionSetData
        )
        self._handle = PartitionSetHandle(
            external_partition_set_data.name, check.inst_param(handle, "handle", RepositoryHandle)
        )

    @property
    def name(self) -> str:
        return self._external_partition_set_data.name

    @property
    def op_selection(self) -> Optional[Sequence[str]]:
        return self._external_partition_set_data.op_selection

    @property
    def mode(self) -> Optional[str]:
        return self._external_partition_set_data.mode

    @property
    def job_name(self) -> str:
        return self._external_partition_set_data.job_name

    @property
    def repository_handle(self) -> RepositoryHandle:
        return self._handle.repository_handle

    def get_external_origin(self) -> ExternalPartitionSetOrigin:
        return self._handle.get_external_origin()

    def get_external_origin_id(self) -> str:
        return self.get_external_origin().get_id()

    def has_partition_name_data(self) -> bool:
        # Partition sets from older versions of Dagster as well as partition sets using
        # a DynamicPartitionsDefinition require calling out to user code to compute the partition
        # names
        return self._external_partition_set_data.external_partitions_data is not None

    def get_partition_names(self, instance: DagsterInstance) -> Sequence[str]:
        check.invariant(self.has_partition_name_data())
        partitions = (
            self._external_partition_set_data.external_partitions_data.get_partitions_definition()  # type: ignore
        )
        return partitions.get_partition_keys(dynamic_partitions_store=instance)
