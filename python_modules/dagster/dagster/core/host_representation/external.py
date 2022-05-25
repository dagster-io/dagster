import warnings
from collections import OrderedDict
from typing import TYPE_CHECKING, List, Optional, Sequence, Union

import dagster._check as check
from dagster.core.definitions.events import AssetKey
from dagster.core.definitions.run_request import InstigatorType
from dagster.core.definitions.schedule_definition import DefaultScheduleStatus
from dagster.core.definitions.sensor_definition import (
    DEFAULT_SENSOR_DAEMON_INTERVAL,
    DefaultSensorStatus,
)
from dagster.core.execution.plan.handle import ResolvedFromDynamicStepHandle, StepHandle
from dagster.core.origin import PipelinePythonOrigin
from dagster.core.snap import ExecutionPlanSnapshot
from dagster.core.utils import toposort
from dagster.serdes import create_snapshot_id
from dagster.utils.schedules import schedule_execution_time_iterator

from .external_data import (
    ExternalAssetNode,
    ExternalPartitionSetData,
    ExternalPipelineData,
    ExternalRepositoryData,
    ExternalScheduleData,
    ExternalSensorData,
)
from .handle import InstigatorHandle, PartitionSetHandle, PipelineHandle, RepositoryHandle
from .pipeline_index import PipelineIndex
from .represented import RepresentedPipeline
from .selector import InstigatorSelector, RepositorySelector

if TYPE_CHECKING:
    from dagster.core.scheduler.instigation import InstigatorState


class ExternalRepository:
    """
    ExternalRepository is a object that represents a loaded repository definition that
    is resident in another process or container. Host processes such as dagit use
    objects such as these to interact with user-defined artifacts.
    """

    def __init__(
        self, external_repository_data: ExternalRepositoryData, repository_handle: RepositoryHandle
    ):
        self.external_repository_data = check.inst_param(
            external_repository_data, "external_repository_data", ExternalRepositoryData
        )
        self._pipeline_index_map = OrderedDict()
        self._job_index_map = OrderedDict()
        for external_pipeline_data in external_repository_data.external_pipeline_datas:
            key = external_pipeline_data.pipeline_snapshot.name
            index = PipelineIndex(
                external_pipeline_data.pipeline_snapshot,
                external_pipeline_data.parent_pipeline_snapshot,
            )
            self._pipeline_index_map[key] = index
            if external_pipeline_data.is_job:
                self._job_index_map[key] = index

        self._handle = check.inst_param(repository_handle, "repository_handle", RepositoryHandle)

        # mypy doesn't understand splat
        instigation_list: Sequence[Union[ExternalScheduleData, ExternalSensorData]] = [
            *external_repository_data.external_schedule_datas,  # type: ignore
            *external_repository_data.external_sensor_datas,  # type: ignore
        ]
        self._instigation_map = OrderedDict(
            (instigation_data.name, instigation_data) for instigation_data in instigation_list
        )
        self._partition_set_map = OrderedDict(
            (external_partition_set_data.name, external_partition_set_data)
            for external_partition_set_data in external_repository_data.external_partition_set_datas
        )

        # pylint: disable=unsubscriptable-object
        _asset_jobs: OrderedDict[str, List[ExternalAssetNode]] = OrderedDict()
        for asset_node in external_repository_data.external_asset_graph_data:
            for job_name in asset_node.job_names:
                if job_name not in _asset_jobs:
                    _asset_jobs[job_name] = [asset_node]
                else:
                    _asset_jobs[job_name].append(asset_node)
        # pylint: disable=unsubscriptable-object
        self._asset_jobs: OrderedDict[str, Sequence[ExternalAssetNode]] = OrderedDict(_asset_jobs)

    @property
    def name(self):
        return self.external_repository_data.name

    def get_pipeline_index(self, pipeline_name):
        return self._pipeline_index_map[pipeline_name]

    def has_pipeline(self, pipeline_name):
        return pipeline_name in self._pipeline_index_map

    def get_pipeline_indices(self):
        return self._pipeline_index_map.values()

    def has_external_pipeline(self, pipeline_name):
        return pipeline_name in self._pipeline_index_map

    def get_external_schedule(self, schedule_name):
        return ExternalSchedule(
            self.external_repository_data.get_external_schedule_data(schedule_name), self._handle
        )

    def get_external_schedules(self):
        return [
            ExternalSchedule(external_schedule_data, self._handle)
            for external_schedule_data in self.external_repository_data.external_schedule_datas
        ]

    def get_external_sensor(self, sensor_name):
        return ExternalSensor(
            self.external_repository_data.get_external_sensor_data(sensor_name), self._handle
        )

    def get_external_sensors(self):
        return [
            ExternalSensor(external_sensor_data, self._handle)
            for external_sensor_data in self.external_repository_data.external_sensor_datas
        ]

    def has_external_schedule(self, schedule_name):
        return isinstance(self._instigation_map.get(schedule_name), ExternalScheduleData)

    def has_external_sensor(self, sensor_name):
        return isinstance(self._instigation_map.get(sensor_name), ExternalSensorData)

    def has_external_partition_set(self, partition_set_name):
        return partition_set_name in self._partition_set_map

    def get_external_partition_set(self, partition_set_name):
        return ExternalPartitionSet(
            self.external_repository_data.get_external_partition_set_data(partition_set_name),
            self._handle,
        )

    def get_external_partition_sets(self):
        return [
            ExternalPartitionSet(external_partition_set_data, self._handle)
            for external_partition_set_data in self.external_repository_data.external_partition_set_datas
        ]

    def get_full_external_pipeline(self, pipeline_name: str) -> "ExternalPipeline":
        check.str_param(pipeline_name, "pipeline_name")
        return ExternalPipeline(
            self.external_repository_data.get_external_pipeline_data(pipeline_name),
            repository_handle=self.handle,
            pipeline_index=self.get_pipeline_index(pipeline_name),
        )

    def get_all_external_pipelines(self):
        return [self.get_full_external_pipeline(pn) for pn in self._pipeline_index_map]

    def has_external_job(self, job_name):
        return job_name in self._job_index_map

    def get_external_job(self, job_name) -> "ExternalPipeline":
        check.str_param(job_name, "job_name")

        if not self.has_external_job(job_name):
            check.failed(f"Could not find job data for {job_name}")

        return ExternalPipeline(
            self.external_repository_data.get_external_pipeline_data(job_name),
            repository_handle=self.handle,
            pipeline_index=self.get_pipeline_index(job_name),
        )

    def get_external_jobs(self) -> List["ExternalPipeline"]:
        return [self.get_external_job(pn) for pn in self._job_index_map]

    @property
    def handle(self):
        return self._handle

    @property
    def selector_id(self):
        return create_snapshot_id(
            RepositorySelector(self._handle.location_name, self._handle.repository_name)
        )

    def get_external_origin(self):
        return self.handle.get_external_origin()

    def get_python_origin(self):
        return self.handle.get_python_origin()

    def get_external_origin_id(self):
        """
        A means of identifying the repository this ExternalRepository represents based on
        where it came from.
        """
        return self.get_external_origin().get_id()

    def get_external_asset_nodes(self, job_name=None) -> Sequence[ExternalAssetNode]:
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

    def get_display_metadata(self):
        return self.handle.display_metadata


class ExternalPipeline(RepresentedPipeline):
    """
    ExternalPipeline is a object that represents a loaded pipeline definition that
    is resident in another process or container. Host processes such as dagit use
    objects such as these to interact with user-defined artifacts.
    """

    def __init__(self, external_pipeline_data, repository_handle, pipeline_index=None):
        check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
        check.inst_param(external_pipeline_data, "external_pipeline_data", ExternalPipelineData)
        check.opt_inst_param(pipeline_index, "pipeline_index", PipelineIndex)

        if pipeline_index is None:
            pipeline_index = PipelineIndex(
                external_pipeline_data.pipeline_snapshot,
                external_pipeline_data.parent_pipeline_snapshot,
            )

        super(ExternalPipeline, self).__init__(pipeline_index=pipeline_index)
        self._external_pipeline_data = external_pipeline_data
        self._repository_handle = repository_handle
        self._active_preset_dict = {ap.name: ap for ap in external_pipeline_data.active_presets}
        self._handle = PipelineHandle(self._pipeline_index.name, repository_handle)

    @property
    def name(self):
        return self._pipeline_index.pipeline_snapshot.name

    @property
    def description(self):
        return self._pipeline_index.pipeline_snapshot.description

    @property
    def solid_names_in_topological_order(self):
        return self._pipeline_index.pipeline_snapshot.solid_names_in_topological_order

    @property
    def external_pipeline_data(self):
        return self._external_pipeline_data

    @property
    def repository_handle(self):
        return self._repository_handle

    @property
    def solid_selection(self):
        return (
            self._pipeline_index.pipeline_snapshot.lineage_snapshot.solid_selection
            if self._pipeline_index.pipeline_snapshot.lineage_snapshot
            else None
        )

    @property
    def solids_to_execute(self):
        return (
            self._pipeline_index.pipeline_snapshot.lineage_snapshot.solids_to_execute
            if self._pipeline_index.pipeline_snapshot.lineage_snapshot
            else None
        )

    @property
    def asset_selection(self):
        return (
            self._pipeline_index.pipeline_snapshot.lineage_snapshot.asset_selection
            if self._pipeline_index.pipeline_snapshot.lineage_snapshot
            else None
        )

    @property
    def active_presets(self):
        return list(self._active_preset_dict.values())

    @property
    def solid_names(self):
        return self._pipeline_index.pipeline_snapshot.solid_names

    def has_solid_invocation(self, solid_name):
        check.str_param(solid_name, "solid_name")
        return self._pipeline_index.has_solid_invocation(solid_name)

    def has_preset(self, preset_name):
        check.str_param(preset_name, "preset_name")
        return preset_name in self._active_preset_dict

    def get_preset(self, preset_name):
        check.str_param(preset_name, "preset_name")
        return self._active_preset_dict[preset_name]

    @property
    def available_modes(self):
        return self._pipeline_index.available_modes

    def has_mode(self, mode_name):
        check.str_param(mode_name, "mode_name")
        return self._pipeline_index.has_mode_def(mode_name)

    def root_config_key_for_mode(self, mode_name):
        check.opt_str_param(mode_name, "mode_name")
        return self.get_mode_def_snap(
            mode_name if mode_name else self.get_default_mode_name()
        ).root_config_key

    def get_default_mode_name(self) -> str:
        return self._pipeline_index.get_default_mode_name()

    @property
    def tags(self):
        return self._pipeline_index.pipeline_snapshot.tags

    @property
    def computed_pipeline_snapshot_id(self):
        return self._pipeline_index.pipeline_snapshot_id

    @property
    def identifying_pipeline_snapshot_id(self):
        return self._pipeline_index.pipeline_snapshot_id

    @property
    def handle(self):
        return self._handle

    def get_origin(self):
        # Returns a PipelinePythonOrigin - maintained for backwards compatibility since this
        # is called in several run launchers to start execution
        warnings.warn(
            "ExternalPipeline.get_origin() is deprecated. Use get_python_origin() if you want "
            "an origin to use for pipeline execution, or get_external_origin if you want an origin "
            "to load an ExternalPipeline."
        )
        return self.get_python_origin()

    def get_python_origin(self):
        repository_python_origin = self.repository_handle.get_python_origin()
        return PipelinePythonOrigin(self.name, repository_python_origin)

    def get_external_origin(self):
        return self.handle.get_external_origin()

    def get_external_origin_id(self):
        return self.get_external_origin().get_id()

    @property
    def pipeline_snapshot(self):
        return self._pipeline_index.pipeline_snapshot

    @property
    def is_job(self):
        return self._external_pipeline_data.is_job


class ExternalExecutionPlan:
    """
    ExternalExecution is a object that represents an execution plan that
    was compiled in another process or persisted in an instance.
    """

    def __init__(self, execution_plan_snapshot):
        self.execution_plan_snapshot = check.inst_param(
            execution_plan_snapshot, "execution_plan_snapshot", ExecutionPlanSnapshot
        )

        self._step_index = {step.key: step for step in self.execution_plan_snapshot.steps}

        self._step_keys_in_plan = (
            set(execution_plan_snapshot.step_keys_to_execute)
            if execution_plan_snapshot.step_keys_to_execute
            else set(self._step_index.keys())
        )

        self._deps = None
        self._topological_steps = None
        self._topological_step_levels = None

    @property
    def step_keys_in_plan(self):
        return list(self._step_keys_in_plan)

    def has_step(self, key):
        check.str_param(key, "key")
        handle = StepHandle.parse_from_key(key)
        if isinstance(handle, ResolvedFromDynamicStepHandle):
            return handle.unresolved_form.to_key() in self._step_index
        return key in self._step_index

    def get_step_by_key(self, key):
        check.str_param(key, "key")
        return self._step_index[key]

    def get_steps_in_plan(self):
        return [self._step_index[sk] for sk in self._step_keys_in_plan]

    def key_in_plan(self, key):
        return key in self._step_keys_in_plan

    # Everything below this line is a near-copy of the equivalent methods on
    # ExecutionPlan. We should resolve this, probably eventually by using the
    # snapshots to support the existing ExecutionPlan methods.
    # https://github.com/dagster-io/dagster/issues/2462
    def execution_deps(self):
        if self._deps is None:
            deps = OrderedDict()

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


class ExternalSchedule:
    def __init__(self, external_schedule_data, handle):
        self._external_schedule_data = check.inst_param(
            external_schedule_data, "external_schedule_data", ExternalScheduleData
        )
        self._handle = InstigatorHandle(
            self._external_schedule_data.name, check.inst_param(handle, "handle", RepositoryHandle)
        )

    @property
    def name(self):
        return self._external_schedule_data.name

    @property
    def cron_schedule(self):
        return self._external_schedule_data.cron_schedule

    @property
    def execution_timezone(self):
        return self._external_schedule_data.execution_timezone

    @property
    def solid_selection(self):
        return self._external_schedule_data.solid_selection

    @property
    def pipeline_name(self):
        return self._external_schedule_data.pipeline_name

    @property
    def mode(self):
        return self._external_schedule_data.mode

    @property
    def description(self):
        return self._external_schedule_data.description

    @property
    def partition_set_name(self):
        return self._external_schedule_data.partition_set_name

    @property
    def environment_vars(self):
        return self._external_schedule_data.environment_vars

    @property
    def handle(self):
        return self._handle

    def get_external_origin(self):
        return self.handle.get_external_origin()

    def get_external_origin_id(self):
        return self.get_external_origin().get_id()

    @property
    def selector_id(self):
        return create_snapshot_id(
            InstigatorSelector(
                self.handle.location_name,
                self.handle.repository_name,
                self._external_schedule_data.name,
            )
        )

    @property
    def default_status(self) -> DefaultScheduleStatus:
        return (
            self._external_schedule_data.default_status
            if self._external_schedule_data.default_status
            else DefaultScheduleStatus.STOPPED
        )

    def get_current_instigator_state(self, stored_state: Optional["InstigatorState"]):
        from dagster.core.scheduler.instigation import (
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
                InstigatorStatus.AUTOMATICALLY_RUNNING,
                ScheduleInstigatorData(self.cron_schedule, start_timestamp=None),
            )
        else:
            # Ignore AUTOMATICALLY_RUNNING states in the DB if the default status
            # isn't DefaultScheduleStatus.RUNNING - this would indicate that the schedule's
            # default has been changed in code but there's still a lingering AUTOMATICALLY_RUNNING
            # row in the database that can be ignored
            if stored_state and stored_state.status != InstigatorStatus.AUTOMATICALLY_RUNNING:
                return stored_state

            return InstigatorState(
                self.get_external_origin(),
                InstigatorType.SCHEDULE,
                InstigatorStatus.STOPPED,
                ScheduleInstigatorData(self.cron_schedule, start_timestamp=None),
            )

    def execution_time_iterator(self, start_timestamp):
        return schedule_execution_time_iterator(
            start_timestamp, self.cron_schedule, self.execution_timezone
        )


class ExternalSensor:
    def __init__(self, external_sensor_data, handle):
        self._external_sensor_data = check.inst_param(
            external_sensor_data, "external_sensor_data", ExternalSensorData
        )
        self._handle = InstigatorHandle(
            self._external_sensor_data.name, check.inst_param(handle, "handle", RepositoryHandle)
        )

    @property
    def name(self):
        return self._external_sensor_data.name

    @property
    def handle(self):
        return self._handle

    @property
    def pipeline_name(self):
        target = self._get_single_target()
        return target.pipeline_name if target else None

    @property
    def mode(self):
        target = self._get_single_target()
        return target.mode if target else None

    @property
    def solid_selection(self):
        target = self._get_single_target()
        return target.solid_selection if target else None

    def _get_single_target(self):
        if self._external_sensor_data.target_dict:
            return list(self._external_sensor_data.target_dict.values())[0]
        else:
            return None

    def get_target_data(self, pipeline_name: Optional[str] = None):
        if pipeline_name:
            return self._external_sensor_data.target_dict[pipeline_name]
        else:
            return self._get_single_target()

    def get_external_targets(self):
        return self._external_sensor_data.target_dict.values()

    @property
    def description(self):
        return self._external_sensor_data.description

    @property
    def min_interval_seconds(self):
        if (
            isinstance(self._external_sensor_data, ExternalSensorData)
            and self._external_sensor_data.min_interval
        ):
            return self._external_sensor_data.min_interval
        return DEFAULT_SENSOR_DAEMON_INTERVAL

    def get_external_origin(self):
        return self._handle.get_external_origin()

    def get_external_origin_id(self):
        return self.get_external_origin().get_id()

    @property
    def selector_id(self):
        return create_snapshot_id(
            InstigatorSelector(
                self.handle.location_name,
                self.handle.repository_name,
                self._external_sensor_data.name,
            )
        )

    def get_current_instigator_state(self, stored_state: Optional["InstigatorState"]):
        from dagster.core.scheduler.instigation import (
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
                    InstigatorStatus.AUTOMATICALLY_RUNNING,
                    SensorInstigatorData(min_interval=self.min_interval_seconds),
                )
            )
        else:
            # Ignore AUTOMATICALLY_RUNNING states in the DB if the default status
            # isn't DefaultSensorStatus.RUNNING - this would indicate that the schedule's
            # default has changed
            if stored_state and stored_state.status != InstigatorStatus.AUTOMATICALLY_RUNNING:
                return stored_state

            return InstigatorState(
                self.get_external_origin(),
                InstigatorType.SENSOR,
                InstigatorStatus.STOPPED,
                SensorInstigatorData(min_interval=self.min_interval_seconds),
            )

    @property
    def metadata(self):
        return self._external_sensor_data.metadata

    @property
    def default_status(self) -> DefaultSensorStatus:
        return (
            self._external_sensor_data.default_status
            if self._external_sensor_data
            else DefaultSensorStatus.STOPPED
        )


class ExternalPartitionSet:
    def __init__(self, external_partition_set_data, handle):
        self._external_partition_set_data = check.inst_param(
            external_partition_set_data, "external_partition_set_data", ExternalPartitionSetData
        )
        self._handle = PartitionSetHandle(
            external_partition_set_data.name, check.inst_param(handle, "handle", RepositoryHandle)
        )

    @property
    def name(self):
        return self._external_partition_set_data.name

    @property
    def solid_selection(self):
        return self._external_partition_set_data.solid_selection

    @property
    def mode(self):
        return self._external_partition_set_data.mode

    @property
    def pipeline_name(self):
        return self._external_partition_set_data.pipeline_name

    @property
    def repository_handle(self):
        return self._handle.repository_handle

    def get_external_origin(self):
        return self._handle.get_external_origin()

    def get_external_origin_id(self):
        return self.get_external_origin().get_id()
