import asyncio
from collections import defaultdict
from collections.abc import Iterable, Iterator, Mapping, Sequence, Set
from datetime import datetime
from functools import cached_property
from threading import RLock
from typing import TYPE_CHECKING, AbstractSet, Callable, Optional, Union  # noqa: UP035

from dagster_shared.error import DagsterError

import dagster._check as check
from dagster._config.snap import ConfigFieldSnap, ConfigSchemaSnapshot
from dagster._core.definitions.asset_checks.asset_check_spec import AssetCheckKey
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.assets.job.asset_job import IMPLICIT_ASSET_JOB_NAME
from dagster._core.definitions.automation_condition_sensor_definition import (
    DEFAULT_AUTOMATION_CONDITION_SENSOR_NAME,
)
from dagster._core.definitions.backfill_policy import BackfillPolicy
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.metadata import MetadataValue
from dagster._core.definitions.partitions.definition import PartitionsDefinition
from dagster._core.definitions.run_request import InstigatorType
from dagster._core.definitions.schedule_definition import DefaultScheduleStatus
from dagster._core.definitions.selector import (
    InstigatorSelector,
    JobSubsetSelector,
    RepositorySelector,
    ScheduleSelector,
    SensorSelector,
)
from dagster._core.definitions.sensor_definition import (
    DEFAULT_SENSOR_DAEMON_INTERVAL,
    DefaultSensorStatus,
    SensorType,
)
from dagster._core.definitions.utils import get_default_automation_condition_sensor_selection
from dagster._core.execution.plan.handle import ResolvedFromDynamicStepHandle, StepHandle
from dagster._core.instance import DagsterInstance
from dagster._core.loader import LoadableBy
from dagster._core.origin import JobPythonOrigin, RepositoryPythonOrigin
from dagster._core.remote_origin import (
    RemoteInstigatorOrigin,
    RemoteJobOrigin,
    RemotePartitionSetOrigin,
    RemoteRepositoryOrigin,
)
from dagster._core.remote_representation.external_data import (
    DEFAULT_MODE_NAME,
    AssetCheckNodeSnap,
    AssetNodeSnap,
    EnvVarConsumer,
    JobDataSnap,
    JobRefSnap,
    NestedResource,
    PartitionSetSnap,
    PresetSnap,
    RepositorySnap,
    ResourceJobUsageEntry,
    ResourceSnap,
    ResourceValueSnap,
    ScheduleSnap,
    SensorMetadataSnap,
    SensorSnap,
    TargetSnap,
)
from dagster._core.remote_representation.handle import (
    CompoundID,
    InstigatorHandle,
    JobHandle,
    PartitionSetHandle,
    RepositoryHandle,
)
from dagster._core.remote_representation.job_index import JobIndex
from dagster._core.remote_representation.represented import RepresentedJob
from dagster._core.snap import ExecutionPlanSnapshot
from dagster._core.snap.job_snapshot import JobSnap
from dagster._core.storage.tags import EXTERNAL_JOB_SOURCE_TAG_KEY
from dagster._core.utils import toposort
from dagster._serdes import create_snapshot_id
from dagster._utils.cached_method import cached_method
from dagster._utils.schedules import schedule_execution_time_iterator

if TYPE_CHECKING:
    from dagster._core.definitions.assets.graph.remote_asset_graph import RemoteRepositoryAssetGraph
    from dagster._core.scheduler.instigation import InstigatorState
    from dagster._core.snap.execution_plan_snapshot import ExecutionStepSnap
    from dagster._core.workspace.context import BaseWorkspaceRequestContext


_empty_set = frozenset()


class RemoteRepository:
    """RemoteRepository is a object that represents a loaded repository definition that
    is resident in another process or container. Host processes such as dagster-webserver use
    objects such as these to interact with user-defined artifacts.
    """

    def __init__(
        self,
        repository_snap: RepositorySnap,
        repository_handle: RepositoryHandle,
        auto_materialize_use_sensors: bool,
        ref_to_data_fn: Optional[Callable[[JobRefSnap], JobDataSnap]] = None,
    ):
        self.repository_snap = check.inst_param(repository_snap, "repository_snap", RepositorySnap)

        self._auto_materialize_use_sensors = auto_materialize_use_sensors

        if repository_snap.job_datas is not None:
            self._job_map: dict[str, Union[JobDataSnap, JobRefSnap]] = {
                d.name: d for d in repository_snap.job_datas
            }
            self._deferred_snapshots: bool = False
            self._ref_to_data_fn = None
        elif repository_snap.job_refs is not None:
            self._job_map = {r.name: r for r in repository_snap.job_refs}
            self._deferred_snapshots = True
            if ref_to_data_fn is None:
                check.failed(
                    "ref_to_data_fn is required when RepositorySnap is loaded with deferred"
                    " snapshots"
                )

            self._ref_to_data_fn = ref_to_data_fn
        else:
            check.failed("invalid state - expected job data or refs")

        self._handle = check.inst_param(repository_handle, "repository_handle", RepositoryHandle)

        self._asset_jobs: dict[str, list[AssetNodeSnap]] = {}
        for asset_node in repository_snap.asset_nodes:
            for job_name in asset_node.job_names:
                self._asset_jobs.setdefault(job_name, []).append(asset_node)

        self._asset_check_jobs: dict[str, list[AssetCheckNodeSnap]] = {}
        for asset_check_node_snap in repository_snap.asset_check_nodes or []:
            for job_name in asset_check_node_snap.job_names:
                self._asset_check_jobs.setdefault(job_name, []).append(asset_check_node_snap)

        # memoize job instances to share instances
        self._memo_lock: RLock = RLock()
        self._cached_jobs: dict[str, RemoteJob] = {}

    @property
    def name(self) -> str:
        return self.repository_snap.name

    @property
    @cached_method
    def _schedules(self) -> dict[str, "RemoteSchedule"]:
        return {
            schedule_snap.name: RemoteSchedule(schedule_snap, self._handle)
            for schedule_snap in self.repository_snap.schedules
        }

    def has_schedule(self, schedule_name: str) -> bool:
        return schedule_name in self._schedules

    def get_schedule(self, schedule_name: str) -> "RemoteSchedule":
        return self._schedules[schedule_name]

    def get_schedules(self) -> Sequence["RemoteSchedule"]:
        return list(self._schedules.values())

    @property
    @cached_method
    def _resources(self) -> dict[str, "RemoteResource"]:
        return {
            resource_snap.name: RemoteResource(resource_snap, self._handle)
            for resource_snap in (self.repository_snap.resources or [])
        }

    def has_resource(self, resource_name: str) -> bool:
        return resource_name in self._resources

    def get_resource(self, resource_name: str) -> "RemoteResource":
        return self._resources[resource_name]

    def get_resources(self) -> Iterable["RemoteResource"]:
        return self._resources.values()

    @property
    def _utilized_env_vars(self) -> Mapping[str, Sequence[EnvVarConsumer]]:
        return self.repository_snap.utilized_env_vars or {}

    def get_utilized_env_vars(self) -> Mapping[str, Sequence[EnvVarConsumer]]:
        return self._utilized_env_vars

    @property
    @cached_method
    def _sensors(self) -> dict[str, "RemoteSensor"]:
        sensor_datas = {
            sensor_snap.name: RemoteSensor(sensor_snap, self._handle)
            for sensor_snap in self.repository_snap.sensors
        }

        if not self._auto_materialize_use_sensors:
            return sensor_datas

        # if necessary, create a default automation condition sensor
        # NOTE: if a user's code location is at a version >= 1.9, then this step should
        # never be necessary, as this will be added in Definitions construction process
        default_sensor_selection = get_default_automation_condition_sensor_selection(
            sensors=[data for data in sensor_datas.values()],
            asset_graph=self.asset_graph,
        )
        if default_sensor_selection is not None:
            default_sensor_data = SensorSnap(
                name=DEFAULT_AUTOMATION_CONDITION_SENSOR_NAME,
                job_name=None,
                op_selection=None,
                asset_selection=default_sensor_selection,
                mode=None,
                min_interval=30,
                description=None,
                target_dict={},
                metadata=None,
                default_status=None,
                sensor_type=SensorType.AUTO_MATERIALIZE,
                run_tags=None,
            )
            sensor_datas[default_sensor_data.name] = RemoteSensor(default_sensor_data, self._handle)

        return sensor_datas

    def has_sensor(self, sensor_name: str) -> bool:
        return sensor_name in self._sensors

    def get_sensor(self, sensor_name: str) -> "RemoteSensor":
        return self._sensors[sensor_name]

    def get_sensors(self) -> Sequence["RemoteSensor"]:
        return list(self._sensors.values())

    @property
    @cached_method
    def _partition_sets(self) -> dict[str, "RemotePartitionSet"]:
        return {
            partition_set_snap.name: RemotePartitionSet(partition_set_snap, self._handle)
            for partition_set_snap in self.repository_snap.partition_sets
        }

    def has_partition_set(self, partition_set_name: str) -> bool:
        return partition_set_name in self._partition_sets

    def get_partition_set(self, partition_set_name: str) -> "RemotePartitionSet":
        return self._partition_sets[partition_set_name]

    def get_partition_sets(self) -> Sequence["RemotePartitionSet"]:
        return list(self._partition_sets.values())

    def has_job(self, job_name: str) -> bool:
        return job_name in self._job_map

    def get_full_job(self, job_name: str) -> "RemoteJob":
        check.str_param(job_name, "job_name")
        check.invariant(self.has_job(job_name), f'No remote job named "{job_name}" found')
        with self._memo_lock:
            if job_name not in self._cached_jobs:
                job_item = self._job_map[job_name]
                if self._deferred_snapshots:
                    if not isinstance(job_item, JobRefSnap):
                        check.failed("unexpected job item")
                    job_ref = job_item
                    job_data_snap: Optional[JobDataSnap] = None
                else:
                    if not isinstance(job_item, JobDataSnap):
                        check.failed("unexpected job item")
                    job_data_snap = job_item
                    job_ref = None

                self._cached_jobs[job_name] = RemoteJob(
                    job_data_snap=job_data_snap,
                    repository_handle=self.handle,
                    job_ref_snap=job_ref,
                    ref_to_data_fn=self._ref_to_data_fn,
                )

            return self._cached_jobs[job_name]

    def get_all_jobs(self) -> Sequence["RemoteJob"]:
        return [self.get_full_job(pn) for pn in self._job_map]

    @property
    def handle(self) -> RepositoryHandle:
        return self._handle

    @property
    def selector(self) -> RepositorySelector:
        return RepositorySelector(
            location_name=self._handle.location_name,
            repository_name=self._handle.repository_name,
        )

    @property
    def selector_id(self) -> str:
        return create_snapshot_id(self.selector)

    def get_compound_id(self) -> CompoundID:
        return CompoundID(
            remote_origin_id=self.get_remote_origin_id(),
            selector_id=self.selector_id,
        )

    def get_remote_origin(self) -> RemoteRepositoryOrigin:
        return self.handle.get_remote_origin()

    def get_python_origin(self) -> RepositoryPythonOrigin:
        return self.handle.get_python_origin()

    def get_remote_origin_id(self) -> str:
        """A means of identifying the repository this RemoteRepository represents based on
        where it came from.
        """
        return self.get_remote_origin().get_id()

    def get_asset_node_snaps(self, job_name: Optional[str] = None) -> Sequence[AssetNodeSnap]:
        return (
            self.repository_snap.asset_nodes
            if job_name is None
            else self._asset_jobs.get(job_name, [])
        )

    @cached_property
    def _asset_snaps_by_key(self) -> Mapping[AssetKey, AssetNodeSnap]:
        mapping = {}
        for asset_snap in self.repository_snap.asset_nodes:
            mapping[asset_snap.asset_key] = asset_snap
        return mapping

    def get_asset_node_snap(self, asset_key: AssetKey) -> Optional[AssetNodeSnap]:
        return self._asset_snaps_by_key.get(asset_key)

    def get_asset_check_node_snaps(
        self, job_name: Optional[str] = None
    ) -> Sequence[AssetCheckNodeSnap]:
        if job_name:
            return self._asset_check_jobs.get(job_name, [])
        else:
            return self.repository_snap.asset_check_nodes or []

    def get_display_metadata(self) -> Mapping[str, str]:
        return self.handle.display_metadata

    @cached_property
    def asset_graph(self) -> "RemoteRepositoryAssetGraph":
        """Returns a repository scoped RemoteAssetGraph."""
        from dagster._core.definitions.assets.graph.remote_asset_graph import (
            RemoteRepositoryAssetGraph,
        )

        return RemoteRepositoryAssetGraph.build(self)

    def get_partition_names_for_asset_job(
        self,
        job_name: str,
        selected_asset_keys: Optional[AbstractSet[AssetKey]],
        instance: DagsterInstance,
    ) -> Sequence[str]:
        partitions_def = self._get_partitions_def_for_job(
            job_name=job_name, selected_asset_keys=selected_asset_keys
        )
        if not partitions_def:
            return []
        return partitions_def.get_partition_keys(dynamic_partitions_store=instance)

    def get_partition_tags_for_implicit_asset_job(
        self,
        job_name: str,
        selected_asset_keys: Optional[AbstractSet[AssetKey]],
        instance: DagsterInstance,
        partition_name: str,
    ) -> Mapping[str, str]:
        return check.not_none(
            self._get_partitions_def_for_job(
                job_name=job_name, selected_asset_keys=selected_asset_keys
            )
        ).get_tags_for_partition_key(partition_name)

    def _get_partitions_def_for_job(
        self,
        job_name: str,
        selected_asset_keys: Optional[AbstractSet[AssetKey]],
    ) -> Optional[PartitionsDefinition]:
        asset_nodes = self.get_asset_node_snaps(job_name)
        unique_partitions_defs: set[PartitionsDefinition] = set()
        for asset_node in asset_nodes:
            if selected_asset_keys is not None and asset_node.asset_key not in selected_asset_keys:
                continue

            if asset_node.partitions is not None:
                unique_partitions_defs.add(asset_node.partitions.get_partitions_definition())

        if len(unique_partitions_defs) == 0:
            # Assets are all unpartitioned
            return None
        if len(unique_partitions_defs) == 1:
            return next(iter(unique_partitions_defs))
        else:
            check.failed(
                "There is no PartitionsDefinition shared by all the provided assets."
                f" {len(unique_partitions_defs)} unique PartitionsDefinitions."
            )

    @cached_property
    def _sensor_mappings(
        self,
    ) -> tuple[
        Mapping[str, Sequence["RemoteSensor"]],
        Mapping[AssetKey, Sequence["RemoteSensor"]],
    ]:
        asset_key_mapping = defaultdict(list)
        job_name_mapping = defaultdict(list)
        for sensor in self.get_sensors():
            for target in sensor.get_targets():
                job_name_mapping[target.job_name].append(sensor)

            if sensor and sensor.asset_selection:
                try:
                    keys = sensor.asset_selection.resolve(self.asset_graph)
                    for key in keys:
                        # only count an asset as targeted by an automation condition sensor if it
                        # has an automation condition
                        if sensor.sensor_type in (
                            SensorType.AUTO_MATERIALIZE,
                            SensorType.AUTOMATION,
                        ):
                            node_snap = self.get_asset_node_snap(key)
                            if not node_snap or not (
                                node_snap.automation_condition
                                or node_snap.automation_condition_snapshot
                            ):
                                continue
                        asset_key_mapping[key].append(sensor)
                except DagsterError:
                    pass

        return job_name_mapping, asset_key_mapping

    @property
    def sensors_by_job_name(self) -> Mapping[str, Sequence["RemoteSensor"]]:
        return self._sensor_mappings[0]

    @property
    def _sensors_by_asset_key(self) -> Mapping[AssetKey, Sequence["RemoteSensor"]]:
        return self._sensor_mappings[1]

    @cached_property
    def schedules_by_job_name(self) -> Mapping[str, Sequence["RemoteSchedule"]]:
        mapping = defaultdict(list)
        for schedule in self.get_schedules():
            mapping[schedule.job_name].append(schedule)

        return mapping

    def get_sensors_targeting(self, asset_key: AssetKey) -> AbstractSet["RemoteSensor"]:
        asset_snap = self.get_asset_node_snap(asset_key)
        if not asset_snap:
            return _empty_set

        sensors = set()
        if asset_key in self._sensors_by_asset_key:
            sensors.update(self._sensors_by_asset_key[asset_key])

        for job_name in asset_snap.job_names:
            if job_name != IMPLICIT_ASSET_JOB_NAME and job_name in self.sensors_by_job_name:
                sensors.update(self.sensors_by_job_name[job_name])

        return sensors

    def get_schedules_targeting(self, asset_key: AssetKey) -> AbstractSet["RemoteSchedule"]:
        asset_snap = self.get_asset_node_snap(asset_key)
        if not asset_snap:
            return _empty_set

        schedules = set()
        for job_name in asset_snap.job_names:
            if job_name != IMPLICIT_ASSET_JOB_NAME and job_name in self.schedules_by_job_name:
                schedules.update(self.schedules_by_job_name[job_name])

        return schedules


class RemoteJob(RepresentedJob, LoadableBy[JobSubsetSelector, "BaseWorkspaceRequestContext"]):
    """RemoteJob is a object that represents a loaded job definition that
    is resident in another process or container. Host processes such as dagster-webserver use
    objects such as these to interact with user-defined artifacts.
    """

    def __init__(
        self,
        job_data_snap: Optional[JobDataSnap],
        repository_handle: RepositoryHandle,
        job_ref_snap: Optional[JobRefSnap] = None,
        ref_to_data_fn: Optional[Callable[[JobRefSnap], JobDataSnap]] = None,
    ):
        check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
        check.opt_inst_param(job_data_snap, "job_data", JobDataSnap)

        self._repository_handle = repository_handle

        self._memo_lock = RLock()
        self._index: Optional[JobIndex] = None

        self._job_data_snap = job_data_snap
        self._job_ref_snap = job_ref_snap
        self._ref_to_data_fn = ref_to_data_fn

        if job_data_snap:
            self._active_preset_dict = {ap.name: ap for ap in job_data_snap.active_presets}
            self._name = job_data_snap.name

        elif job_ref_snap:
            self._active_preset_dict = {ap.name: ap for ap in job_ref_snap.active_presets}
            self._name = job_ref_snap.name
            if ref_to_data_fn is None:
                check.failed("ref_to_data_fn must be passed when using deferred snapshots")

        else:
            check.failed("Expected either job data or ref, got neither")

        self._handle = JobHandle(
            job_name=self._name,
            repository_handle=repository_handle,
        )

    @classmethod
    async def _batch_load(
        cls, keys: Iterable[JobSubsetSelector], context: "BaseWorkspaceRequestContext"
    ) -> Iterable[Optional["RemoteJob"]]:
        unique_keys = {key for key in keys}
        tasks = [context.gen_job(unique_key) for unique_key in unique_keys]
        results = await asyncio.gather(*tasks)

        results_by_key = {unique_key: result for unique_key, result in zip(unique_keys, results)}
        return [results_by_key[key] for key in keys]

    @classmethod
    def _blocking_batch_load(
        cls, keys: Iterable[JobSubsetSelector], context: "BaseWorkspaceRequestContext"
    ) -> Iterable[Optional["RemoteJob"]]:
        raise NotImplementedError

    @property
    def _job_index(self) -> JobIndex:
        with self._memo_lock:
            if self._index is None:
                self._index = JobIndex(
                    self.job_data_snap.job,
                    self.job_data_snap.parent_job,
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
    def job_data_snap(self) -> JobDataSnap:
        with self._memo_lock:
            if self._job_data_snap is None:
                if self._job_ref_snap is None or self._ref_to_data_fn is None:
                    check.failed("unexpected state - unable to load data from ref")
                self._job_data_snap = self._ref_to_data_fn(self._job_ref_snap)

            return self._job_data_snap

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
    def active_presets(self) -> Sequence[PresetSnap]:
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

    def get_preset(self, preset_name: str) -> PresetSnap:
        check.str_param(preset_name, "preset_name")
        return self._active_preset_dict[preset_name]

    @property
    def root_config_key(self) -> Optional[str]:
        return self.get_mode_def_snap(DEFAULT_MODE_NAME).root_config_key

    @property
    def tags(self) -> Mapping[str, str]:
        return self._job_index.job_snapshot.tags

    @property
    def run_tags(self) -> Mapping[str, str]:
        snapshot_tags = self._job_index.job_snapshot.run_tags
        # Snapshot tags will be None for snapshots originating from old code servers before the
        # introduction of run tags. In these cases, the job definition tags are treated as run tags
        # to maintain backcompat.
        return snapshot_tags if snapshot_tags is not None else self.tags

    @property
    def metadata(self) -> Mapping[str, MetadataValue]:
        return self._job_index.job_snapshot.metadata

    @property
    def job_snapshot(self) -> JobSnap:
        return self._job_index.job_snapshot

    @property
    def _snapshot_id(self) -> str:
        if self._job_ref_snap:
            return self._job_ref_snap.snapshot_id

        return self._job_index.job_snapshot_id

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

    def get_remote_origin(self) -> RemoteJobOrigin:
        return self.handle.get_remote_origin()

    def get_remote_origin_id(self) -> str:
        return self.get_remote_origin().get_id()

    def get_external_job_source(self) -> Optional[str]:
        """Retrieve the external job source from the job.

        Prefers retrieval from the JobRefSnap, to avoid an expensive retrieval of the JobDataSnap.
        """
        if self._job_ref_snap is not None:
            return self._job_ref_snap.get_preview_tags().get(EXTERNAL_JOB_SOURCE_TAG_KEY)
        # If JobRefSnap is not available, fall back to the JobDataSnap.
        return self.tags.get(EXTERNAL_JOB_SOURCE_TAG_KEY)

    def get_subset_selector(
        self, asset_selection: Set[AssetKey], asset_check_selection: Set[AssetCheckKey]
    ) -> JobSubsetSelector:
        """Returns a JobSubsetSelector to select a subset of this RemoteJob."""
        return JobSubsetSelector(
            location_name=self.handle.location_name,
            repository_name=self.handle.repository_name,
            job_name=self.name,
            op_selection=self.op_selection,
            asset_selection=asset_selection,
            asset_check_selection=asset_check_selection,
        )


class RemoteExecutionPlan(LoadableBy[JobSubsetSelector, "BaseWorkspaceRequestContext"]):
    """RemoteExecutionPlan is a object that represents an execution plan that
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

    @classmethod
    async def _batch_load(
        cls, keys: Iterable[JobSubsetSelector], context: "BaseWorkspaceRequestContext"
    ) -> Iterable[Optional["RemoteExecutionPlan"]]:
        remote_jobs = await RemoteJob.gen_many(context, keys)
        remote_jobs_by_key = {key: job for key, job in zip(keys, remote_jobs)}
        unique_keys = {key for key in keys}

        tasks = [
            context.gen_execution_plan(
                check.not_none(remote_jobs_by_key[key]),
                run_config=key.run_config or {},
                step_keys_to_execute=None,
                known_state=None,
            )
            for key in unique_keys
            if remote_jobs_by_key[key] is not None
        ]

        if tasks:
            results = await asyncio.gather(*tasks)
        else:
            results = []
        results_by_key = {unique_key: result for unique_key, result in zip(unique_keys, results)}

        return [results_by_key.get(key) for key in keys]

    @classmethod
    def _blocking_batch_load(
        cls, keys: Iterable[JobSubsetSelector], context: "BaseWorkspaceRequestContext"
    ) -> Iterable[Optional["RemoteExecutionPlan"]]:
        raise NotImplementedError

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


class RemoteResource:
    """Represents a top-level resource in a repository, e.g. one passed through the Definitions API."""

    def __init__(self, resource_snap: ResourceSnap, handle: RepositoryHandle):
        self._resource_snap = check.inst_param(resource_snap, "resource_snap", ResourceSnap)
        self._handle = InstigatorHandle(
            instigator_name=self._resource_snap.name,
            repository_handle=check.inst_param(handle, "handle", RepositoryHandle),
        )

    @property
    def name(self) -> str:
        return self._resource_snap.name

    @property
    def description(self) -> Optional[str]:
        return self._resource_snap.resource_snapshot.description

    @property
    def config_field_snaps(self) -> list[ConfigFieldSnap]:
        return self._resource_snap.config_field_snaps

    @property
    def configured_values(self) -> dict[str, ResourceValueSnap]:
        return self._resource_snap.configured_values

    @property
    def config_schema_snap(self) -> ConfigSchemaSnapshot:
        return self._resource_snap.config_schema_snap

    @property
    def nested_resources(self) -> dict[str, NestedResource]:
        return self._resource_snap.nested_resources

    @property
    def parent_resources(self) -> dict[str, str]:
        return self._resource_snap.parent_resources

    @property
    def resource_type(self) -> str:
        return self._resource_snap.resource_type

    @property
    def is_top_level(self) -> bool:
        return self._resource_snap.is_top_level

    @property
    def asset_keys_using(self) -> list[AssetKey]:
        return self._resource_snap.asset_keys_using

    @property
    def job_ops_using(self) -> list[ResourceJobUsageEntry]:
        return self._resource_snap.job_ops_using

    @property
    def schedules_using(self) -> list[str]:
        return self._resource_snap.schedules_using

    @property
    def sensors_using(self) -> list[str]:
        return self._resource_snap.sensors_using

    @property
    def is_dagster_maintained(self) -> bool:
        return self._resource_snap.dagster_maintained


class RemoteSchedule:
    def __init__(self, schedule_snap: ScheduleSnap, handle: RepositoryHandle):
        self._schedule_snap = check.inst_param(schedule_snap, "schedule_snap", ScheduleSnap)
        self._handle = InstigatorHandle(
            self._schedule_snap.name,
            check.inst_param(handle, "handle", RepositoryHandle),
        )

    @property
    def name(self) -> str:
        return self._schedule_snap.name

    @property
    def cron_schedule(self) -> Union[str, Sequence[str]]:
        return self._schedule_snap.cron_schedule

    @property
    def execution_timezone(self) -> Optional[str]:
        return self._schedule_snap.execution_timezone

    @property
    def op_selection(self) -> Optional[Sequence[str]]:
        return self._schedule_snap.op_selection

    @property
    def job_name(self) -> str:
        return self._schedule_snap.job_name

    @property
    def asset_selection(self) -> Optional[AssetSelection]:
        return self._schedule_snap.asset_selection

    @property
    def mode(self) -> Optional[str]:
        return self._schedule_snap.mode

    @property
    def description(self) -> Optional[str]:
        return self._schedule_snap.description

    @property
    def partition_set_name(self) -> Optional[str]:
        return self._schedule_snap.partition_set_name

    @property
    def environment_vars(self) -> Optional[Mapping[str, str]]:
        return self._schedule_snap.environment_vars

    @property
    def handle(self) -> InstigatorHandle:
        return self._handle

    @property
    def tags(self) -> Mapping[str, str]:
        return self._schedule_snap.tags

    @property
    def metadata(self) -> Mapping[str, MetadataValue]:
        return self._schedule_snap.metadata

    def get_remote_origin(self) -> RemoteInstigatorOrigin:
        return self.handle.get_remote_origin()

    def get_remote_origin_id(self) -> str:
        return self.get_remote_origin().get_id()

    @property
    def selector(self) -> InstigatorSelector:
        return InstigatorSelector(
            location_name=self.handle.location_name,
            repository_name=self.handle.repository_name,
            name=self._schedule_snap.name,
        )

    @property
    def schedule_selector(self) -> ScheduleSelector:
        return ScheduleSelector(
            location_name=self.handle.location_name,
            repository_name=self.handle.repository_name,
            schedule_name=self._schedule_snap.name,
        )

    @cached_property
    def selector_id(self) -> str:
        return create_snapshot_id(self.selector)

    def get_compound_id(self) -> CompoundID:
        return CompoundID(
            remote_origin_id=self.get_remote_origin_id(),
            selector_id=self.selector_id,
        )

    @property
    def default_status(self) -> DefaultScheduleStatus:
        return self._schedule_snap.default_status or DefaultScheduleStatus.STOPPED

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
                self.get_remote_origin(),
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
                self.get_remote_origin(),
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


class RemoteSensor:
    def __init__(self, sensor_snap: SensorSnap, handle: RepositoryHandle):
        self._sensor_snap = check.inst_param(sensor_snap, "sensor_snap", SensorSnap)
        self._handle = InstigatorHandle(
            self._sensor_snap.name, check.inst_param(handle, "handle", RepositoryHandle)
        )

    @property
    def name(self) -> str:
        return self._sensor_snap.name

    @property
    def handle(self) -> InstigatorHandle:
        return self._handle

    @property
    def job_name(self) -> Optional[str]:
        target = self._get_single_target()
        return target.job_name if target else None

    @property
    def asset_selection(self) -> Optional[AssetSelection]:
        return self._sensor_snap.asset_selection

    @property
    def mode(self) -> Optional[str]:
        target = self._get_single_target()
        return target.mode if target else None

    @property
    def op_selection(self) -> Optional[Sequence[str]]:
        target = self._get_single_target()
        return target.op_selection if target else None

    def _get_single_target(self) -> Optional[TargetSnap]:
        if self._sensor_snap.target_dict:
            return next(iter(self._sensor_snap.target_dict.values()))
        else:
            return None

    def get_target(self, job_name: Optional[str] = None) -> Optional[TargetSnap]:
        if job_name:
            return self._sensor_snap.target_dict[job_name]
        else:
            return self._get_single_target()

    def get_targets(self) -> Sequence[TargetSnap]:
        return list(self._sensor_snap.target_dict.values())

    @property
    def description(self) -> Optional[str]:
        return self._sensor_snap.description

    @property
    def min_interval_seconds(self) -> int:
        if isinstance(self._sensor_snap, SensorSnap) and self._sensor_snap.min_interval:
            return self._sensor_snap.min_interval
        return DEFAULT_SENSOR_DAEMON_INTERVAL

    @property
    def run_tags(self) -> Mapping[str, str]:
        return self._sensor_snap.run_tags

    def get_remote_origin(self) -> RemoteInstigatorOrigin:
        return self._handle.get_remote_origin()

    def get_remote_origin_id(self) -> str:
        return self.get_remote_origin().get_id()

    @property
    def selector(self) -> InstigatorSelector:
        return InstigatorSelector(
            location_name=self.handle.location_name,
            repository_name=self.handle.repository_name,
            name=self._sensor_snap.name,
        )

    @property
    def sensor_selector(self) -> SensorSelector:
        return SensorSelector(
            location_name=self.handle.location_name,
            repository_name=self.handle.repository_name,
            sensor_name=self._sensor_snap.name,
        )

    @cached_property
    def selector_id(self) -> str:
        return create_snapshot_id(self.selector)

    def get_compound_id(self) -> CompoundID:
        return CompoundID(
            remote_origin_id=self.get_remote_origin_id(),
            selector_id=self.selector_id,
        )

    @property
    def sensor_type(self) -> SensorType:
        return self._sensor_snap.sensor_type or SensorType.UNKNOWN

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
                    self.get_remote_origin(),
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
                self.get_remote_origin(),
                InstigatorType.SENSOR,
                InstigatorStatus.STOPPED,
                SensorInstigatorData(
                    min_interval=self.min_interval_seconds,
                    sensor_type=self.sensor_type,
                ),
            )

    @property
    def metadata(self) -> Optional[SensorMetadataSnap]:
        return self._sensor_snap.metadata

    @property
    def tags(self) -> Mapping[str, str]:
        return self._sensor_snap.tags

    @property
    def default_status(self) -> DefaultSensorStatus:
        return self._sensor_snap.default_status or DefaultSensorStatus.STOPPED


class RemotePartitionSet:
    def __init__(self, partition_set_snap: PartitionSetSnap, handle: RepositoryHandle):
        self._partition_set_snap = check.inst_param(
            partition_set_snap, "partition_set_snap", PartitionSetSnap
        )
        self._handle = PartitionSetHandle(
            partition_set_name=partition_set_snap.name,
            repository_handle=check.inst_param(handle, "handle", RepositoryHandle),
        )

    @property
    def name(self) -> str:
        return self._partition_set_snap.name

    @property
    def op_selection(self) -> Optional[Sequence[str]]:
        return self._partition_set_snap.op_selection

    @property
    def mode(self) -> Optional[str]:
        return self._partition_set_snap.mode

    @property
    def job_name(self) -> str:
        return self._partition_set_snap.job_name

    @property
    def backfill_policy(self) -> Optional[BackfillPolicy]:
        return self._partition_set_snap.backfill_policy

    @property
    def repository_handle(self) -> RepositoryHandle:
        return self._handle.repository_handle

    def get_remote_origin(self) -> RemotePartitionSetOrigin:
        return self._handle.get_remote_origin()

    def get_remote_origin_id(self) -> str:
        return self.get_remote_origin().get_id()

    def has_partition_name_data(self) -> bool:
        # Partition sets from older versions of Dagster as well as partition sets using
        # a DynamicPartitionsDefinition require calling out to user code to compute the partition
        # names
        return self._partition_set_snap.partitions is not None

    def has_partitions_definition(self) -> bool:
        # Partition sets from older versions of Dagster as well as partition sets using
        # a DynamicPartitionsDefinition require calling out to user code to get the
        # partitions definition
        return self._partition_set_snap.partitions is not None

    def get_partitions_definition(self) -> PartitionsDefinition:
        partitions_data = self._partition_set_snap.partitions
        if partitions_data is None:
            check.failed(
                "Partition set does not have partition data, cannot get partitions definition"
            )
        return partitions_data.get_partitions_definition()

    def get_partition_names(self, instance: DagsterInstance) -> Sequence[str]:
        partitions = self._partition_set_snap.partitions
        if partitions is None:
            check.failed(
                "Partition set does not have partition data, cannot get partitions definition"
            )
        return self.get_partitions_definition().get_partition_keys(
            dynamic_partitions_store=instance
        )
