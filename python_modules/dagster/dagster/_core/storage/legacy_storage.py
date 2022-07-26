from typing import TYPE_CHECKING, Callable, Iterable, Mapping, Optional, Sequence, Set, Tuple, Union

from dagster import _check as check
from dagster._serdes import ConfigurableClass, ConfigurableClassData

from .base_storage import DagsterStorage
from .event_log.base import AssetRecord, EventLogRecord, EventLogStorage, EventRecordsFilter
from .runs.base import RunStorage
from .schedules.base import ScheduleStorage

if TYPE_CHECKING:
    from dagster._core.definitions.events import AssetKey
    from dagster._core.definitions.run_request import InstigatorType
    from dagster._core.events import DagsterEvent, DagsterEventType
    from dagster._core.events.log import EventLogEntry
    from dagster._core.execution.backfill import BulkActionStatus, PartitionBackfill
    from dagster._core.execution.stats import RunStepKeyStatsSnapshot
    from dagster._core.scheduler.instigation import (
        InstigatorState,
        InstigatorTick,
        TickData,
        TickStatus,
    )
    from dagster._core.snap.execution_plan_snapshot import ExecutionPlanSnapshot
    from dagster._core.snap.pipeline_snapshot import PipelineSnapshot
    from dagster._core.storage.pipeline_run import (
        JobBucket,
        PipelineRun,
        PipelineRunStatsSnapshot,
        RunRecord,
        RunsFilter,
        TagBucket,
    )
    from dagster._daemon.types import DaemonHeartbeat


class CompositeStorage(DagsterStorage, ConfigurableClass):
    """Utiltity class for combining the individually configured run, event_log, schedule storages
    into the single dagster storage.
    """

    def __init__(
        self,
        run_storage: RunStorage,
        event_log_storage: EventLogStorage,
        schedule_storage: ScheduleStorage,
        inst_data=None,
    ):
        self._run_storage = run_storage
        self._event_log_storage = check.inst_param(
            event_log_storage, "event_log_storage", EventLogStorage
        )
        self._schedule_storage = check.inst_param(
            schedule_storage, "schedule_storage", ScheduleStorage
        )
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)
        super().__init__()

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {
            "run_storage": {
                "module_name": str,
                "class_name": str,
                "config_yaml": str,
            },
            "event_log_storage": {
                "module_name": str,
                "class_name": str,
                "config_yaml": str,
            },
            "schedule_storage": {
                "module_name": str,
                "class_name": str,
                "config_yaml": str,
            },
        }

    @staticmethod
    def from_config_value(inst_data, config_value):
        run_storage_config = config_value["run_storage"]
        run_storage = ConfigurableClassData(
            module_name=run_storage_config["module_name"],
            class_name=run_storage_config["class_name"],
            config_yaml=run_storage_config["config_yaml"],
        ).rehydrate()
        event_log_storage_config = config_value["event_log_storage"]
        event_log_storage = ConfigurableClassData(
            module_name=event_log_storage_config["module_name"],
            class_name=event_log_storage_config["class_name"],
            config_yaml=event_log_storage_config["config_yaml"],
        ).rehydrate()
        schedule_storage_config = config_value["schedule_storage"]
        schedule_storage = ConfigurableClassData(
            module_name=schedule_storage_config["module_name"],
            class_name=schedule_storage_config["class_name"],
            config_yaml=schedule_storage_config["config_yaml"],
        ).rehydrate()
        return CompositeStorage(
            run_storage, event_log_storage, schedule_storage, inst_data=inst_data
        )

    @property
    def event_log_storage(self) -> EventLogStorage:
        return self._event_log_storage

    @property
    def run_storage(self) -> RunStorage:
        return self._run_storage

    @property
    def schedule_storage(self) -> ScheduleStorage:
        return self._schedule_storage


class LegacyRunStorage(RunStorage, ConfigurableClass):
    def __init__(self, storage, inst_data=None):
        self._storage = check.inst_param(storage, "storage", DagsterStorage)
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)
        super().__init__()

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {
            "module_name": str,
            "class_name": str,
            "config_yaml": str,
        }

    @staticmethod
    def from_config_value(inst_data, config_value):
        storage = ConfigurableClassData(
            module_name=config_value["module_name"],
            class_name=config_value["class_name"],
            config_yaml=config_value["config_yaml"],
        ).rehydrate()
        return LegacyRunStorage(storage, inst_data=inst_data)

    def add_run(self, pipeline_run: "PipelineRun") -> "PipelineRun":
        return self._storage.run_storage.add_run(pipeline_run)

    def handle_run_event(self, run_id: str, event: "DagsterEvent"):
        return self._storage.run_storage.handle_run_event(run_id, event)

    def get_runs(
        self,
        filters: Optional["RunsFilter"] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        bucket_by: Optional[Union["JobBucket", "TagBucket"]] = None,
    ) -> Iterable["PipelineRun"]:
        return self._storage.run_storage.get_runs(filters, cursor, limit, bucket_by)

    def get_runs_count(self, filters: Optional["RunsFilter"] = None) -> int:
        return self._storage.run_storage.get_runs_count(filters)

    def get_run_group(self, run_id: str) -> Optional[Tuple[str, Iterable["PipelineRun"]]]:
        return self._storage.run_storage.get_run_group(run_id)

    def get_run_groups(
        self,
        filters: Optional["RunsFilter"] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Mapping[str, Mapping[str, Union[Iterable["PipelineRun"], int]]]:
        return self._storage.run_storage.get_run_groups(filters, cursor, limit)

    def get_run_by_id(self, run_id: str) -> Optional["PipelineRun"]:
        return self._storage.run_storage.get_run_by_id(run_id)

    def get_run_records(
        self,
        filters: Optional["RunsFilter"] = None,
        limit: Optional[int] = None,
        order_by: Optional[str] = None,
        ascending: bool = False,
        cursor: Optional[str] = None,
        bucket_by: Optional[Union["JobBucket", "TagBucket"]] = None,
    ) -> Sequence["RunRecord"]:
        return self._storage.run_storage.get_run_records(
            filters, limit, order_by, ascending, cursor, bucket_by
        )

    def get_run_tags(self) -> Sequence[Tuple[str, Set[str]]]:
        return self._storage.run_storage.get_run_tags()

    def add_run_tags(self, run_id: str, new_tags: Mapping[str, str]):
        return self._storage.run_storage.add_run_tags(run_id, new_tags)

    def has_run(self, run_id: str) -> bool:
        return self._storage.run_storage.has_run(run_id)

    def add_snapshot(
        self,
        snapshot: Union["PipelineSnapshot", "ExecutionPlanSnapshot"],
        snapshot_id: Optional[str] = None,
    ):
        return self._storage.run_storage.add_snapshot(snapshot, snapshot_id)

    def has_snapshot(self, snapshot_id: str):
        return self._storage.run_storage.has_snapshot(snapshot_id)

    def has_pipeline_snapshot(self, pipeline_snapshot_id: str) -> bool:
        return self._storage.run_storage.has_pipeline_snapshot(pipeline_snapshot_id)

    def add_pipeline_snapshot(
        self, pipeline_snapshot: "PipelineSnapshot", snapshot_id: Optional[str] = None
    ) -> str:
        return self._storage.run_storage.add_pipeline_snapshot(pipeline_snapshot, snapshot_id)

    def get_pipeline_snapshot(self, pipeline_snapshot_id: str) -> "PipelineSnapshot":
        return self._storage.run_storage.get_pipeline_snapshot(pipeline_snapshot_id)

    def has_execution_plan_snapshot(self, execution_plan_snapshot_id: str) -> bool:
        return self._storage.run_storage.has_execution_plan_snapshot(execution_plan_snapshot_id)

    def add_execution_plan_snapshot(
        self, execution_plan_snapshot: "ExecutionPlanSnapshot", snapshot_id: Optional[str] = None
    ) -> str:
        return self._storage.run_storage.add_execution_plan_snapshot(
            execution_plan_snapshot, snapshot_id
        )

    def get_execution_plan_snapshot(
        self, execution_plan_snapshot_id: str
    ) -> "ExecutionPlanSnapshot":
        return self._storage.run_storage.get_execution_plan_snapshot(execution_plan_snapshot_id)

    def wipe(self):
        return self._storage.run_storage.wipe()

    def delete_run(self, run_id: str):
        return self._storage.run_storage.delete_run(run_id)

    @property
    def supports_bucket_queries(self):
        return self._storage.run_storage.supports_bucket_queries()

    def migrate(self, print_fn: Optional[Callable] = None, force_rebuild_all: bool = False):
        return self._storage.run_storage.migrate(print_fn, force_rebuild_all)

    def optimize(self, print_fn: Optional[Callable] = None, force_rebuild_all: bool = False):
        return self._storage.run_storage.optimize(print_fn, force_rebuild_all)

    def dispose(self):
        return self._storage.run_storage.dispose()

    def optimize_for_dagit(self, statement_timeout: int, pool_recycle: int):
        return self._storage.run_storage.optimize_for_dagit(statement_timeout, pool_recycle)

    def add_daemon_heartbeat(self, daemon_heartbeat: "DaemonHeartbeat"):
        return self._storage.run_storage.add_daemon_heartbeat(daemon_heartbeat)

    def get_daemon_heartbeats(self) -> Mapping[str, "DaemonHeartbeat"]:
        return self._storage.run_storage.get_daemon_heartbeats()

    def wipe_daemon_heartbeats(self):
        return self._storage.run_storage.wipe_daemon_heartbeats()

    def get_backfills(
        self,
        status: Optional["BulkActionStatus"] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Sequence["PartitionBackfill"]:
        return self._storage.run_storage.get_backfills(status, cursor, limit)

    def get_backfill(self, backfill_id: str) -> Optional["PartitionBackfill"]:
        return self._storage.run_storage.get_backfill(backfill_id)

    def add_backfill(self, partition_backfill: "PartitionBackfill"):
        return self._storage.run_storage.add_backfill(partition_backfill)

    def update_backfill(self, partition_backfill: "PartitionBackfill"):
        return self._storage.run_storage.update_backfill(partition_backfill)


class LegacyEventLogStorage(EventLogStorage, ConfigurableClass):
    def __init__(self, storage, inst_data=None):
        self._storage = check.inst_param(storage, "storage", DagsterStorage)
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)
        super().__init__()

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {
            "module_name": str,
            "class_name": str,
            "config_yaml": str,
        }

    @staticmethod
    def from_config_value(inst_data, config_value):
        storage = ConfigurableClassData(
            module_name=config_value["module_name"],
            class_name=config_value["class_name"],
            config_yaml=config_value["config_yaml"],
        ).rehydrate()
        return LegacyEventLogStorage(storage, inst_data=inst_data)

    def get_logs_for_run(
        self,
        run_id: str,
        cursor: Optional[Union[str, int]] = None,
        of_type: Optional[Union["DagsterEventType", Set["DagsterEventType"]]] = None,
        limit: Optional[int] = None,
    ) -> Iterable["EventLogEntry"]:
        return self._storage.event_storage.get_logs_for_run(run_id, cursor, of_type, limit)

    def get_stats_for_run(self, run_id: str) -> "PipelineRunStatsSnapshot":
        return self._storage.event_storage.get_stats_for_run(run_id)

    def get_step_stats_for_run(
        self, run_id: str, step_keys=None
    ) -> Sequence["RunStepKeyStatsSnapshot"]:
        return self._storage.event_storage.get_step_stats_for_run(run_id, step_keys)

    def store_event(self, event: "EventLogEntry"):
        return self._storage.event_storage.store_event(event)

    def delete_events(self, run_id: str):
        return self._storage.event_storage.delete_events(run_id)

    def upgrade(self):
        return self._storage.event_storage.upgrade()

    def reindex_events(self, print_fn: Optional[Callable] = None, force: bool = False):
        return self._storage.event_storage.reindex_events(print_fn, force)

    def reindex_assets(self, print_fn: Optional[Callable] = None, force: bool = False):
        return self._storage.event_storage.reindex_assets(print_fn, force)

    def wipe(self):
        return self._storage.event_storage.wipe()

    def watch(self, run_id: str, cursor: str, callback: Callable):
        return self._storage.event_storage.watch(run_id, cursor, callback)

    def end_watch(self, run_id: str, handler: Callable):
        return self._storage.event_storage.end_watch(run_id, handler)

    @property
    def is_persistent(self) -> bool:
        return self._storage.event_storage.is_persistent

    def dispose(self):
        return self._storage.event_storage.dispose()

    def optimize_for_dagit(self, statement_timeout: int, pool_recycle: int):
        return self._storage.event_storage.optimize_for_dagit(statement_timeout, pool_recycle)

    def get_event_records(
        self,
        event_records_filter: Optional[EventRecordsFilter] = None,
        limit: Optional[int] = None,
        ascending: bool = False,
    ) -> Iterable[EventLogRecord]:
        return self._storage.event_storage.get_event_records(event_records_filter, limit, ascending)

    def get_asset_records(
        self, asset_keys: Optional[Sequence["AssetKey"]] = None
    ) -> Iterable[AssetRecord]:
        return self._storage.event_storage.get_asset_records(asset_keys)

    def has_asset_key(self, asset_key: "AssetKey") -> bool:
        return self._storage.event_storage.has_asset_key(asset_key)

    def all_asset_keys(self) -> Iterable["AssetKey"]:
        return self._storage.event_storage.all_asset_keys()

    def get_asset_keys(
        self,
        prefix: Optional[Sequence[str]] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Iterable["AssetKey"]:
        return self._storage.event_storage.get_asset_keys(prefix, limit, cursor)

    def get_latest_materialization_events(
        self, asset_keys: Sequence["AssetKey"]
    ) -> Mapping["AssetKey", Optional["EventLogEntry"]]:
        return self._storage.event_storage.get_latest_materialization_events(asset_keys)

    def get_asset_events(
        self,
        asset_key: "AssetKey",
        partitions: Optional[Sequence[str]] = None,
        before_cursor: Optional[int] = None,
        after_cursor: Optional[int] = None,
        limit: Optional[int] = None,
        ascending: bool = False,
        include_cursor: bool = False,
        before_timestamp=None,
        cursor: Optional[int] = None,  # deprecated
    ) -> Union[Iterable["EventLogEntry"], Iterable[Tuple[int, "EventLogEntry"]]]:
        return self._storage.event_storage.get_asset_events(
            asset_key,
            partitions,
            before_cursor,
            after_cursor,
            limit,
            ascending,
            include_cursor,
            before_timestamp,
            cursor,
        )

    def get_asset_run_ids(self, asset_key: "AssetKey") -> Iterable[str]:
        return self._storage.event_storage.get_asset_run_ids(asset_key)

    def wipe_asset(self, asset_key: "AssetKey"):
        return self._storage.event_storage.wipe_asset(asset_key)

    def get_materialization_count_by_partition(
        self, asset_keys: Sequence["AssetKey"]
    ) -> Mapping["AssetKey", Mapping[str, int]]:
        return self._storage.event_storage.get_materialization_count_by_partition(asset_keys)


class LegacyScheduleStorage(ScheduleStorage, ConfigurableClass):
    def __init__(self, storage, inst_data=None):
        self._storage = check.inst_param(storage, "storage", DagsterStorage)
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)
        super().__init__()

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {
            "module_name": str,
            "class_name": str,
            "config_yaml": str,
        }

    @staticmethod
    def from_config_value(inst_data, config_value):
        storage = ConfigurableClassData(
            module_name=config_value["module_name"],
            class_name=config_value["class_name"],
            config_yaml=config_value["config_yaml"],
        ).rehydrate()
        return LegacyScheduleStorage(storage, inst_data=inst_data)

    def wipe(self):
        return self._storage.schedule_storage.wipe()

    def all_instigator_state(
        self,
        repository_origin_id: Optional[str] = None,
        repository_selector_id: Optional[str] = None,
        instigator_type: Optional["InstigatorType"] = None,
    ) -> Iterable["InstigatorState"]:
        return self._storage.schedule_storage.all_instigator_state()

    def get_instigator_state(self, origin_id: str, selector_id: str) -> "InstigatorState":
        return self._storage.schedule_storage.get_instigator_state(origin_id, selector_id)

    def add_instigator_state(self, state: "InstigatorState"):
        return self._storage.schedule_storage.add_instigator_state(state)

    def update_instigator_state(self, state: "InstigatorState"):
        return self._storage.schedule_storage.update_instigator_state(state)

    def delete_instigator_state(self, origin_id: str, selector_id: str):
        return self._storage.schedule_storage.delete_instigator_state(origin_id, selector_id)

    @property
    def supports_batch_queries(self):
        return self._storage.schedule_storage.supports_batch_queries

    def get_batch_ticks(
        self,
        selector_ids: Sequence[str],
        limit: Optional[int] = None,
        statuses: Optional[Sequence["TickStatus"]] = None,
    ) -> Mapping[str, Iterable["InstigatorTick"]]:
        return self._storage.schedule_storage.get_batch_ticks(selector_ids, limit, statuses)

    def get_ticks(
        self,
        origin_id: str,
        selector_id: str,
        before: Optional[float] = None,
        after: Optional[float] = None,
        limit: Optional[int] = None,
        statuses: Optional[Sequence["TickStatus"]] = None,
    ) -> Iterable["InstigatorTick"]:
        return self._storage.schedule_storage.get_ticks(
            origin_id, selector_id, before, after, limit, statuses
        )

    def create_tick(self, tick_data: "TickData"):
        return self._storage.schedule_storage.create_tick(tick_data)

    def update_tick(self, tick: "InstigatorTick"):
        return self._storage.schedule_storage.update_tick(tick)

    def purge_ticks(
        self,
        origin_id: str,
        selector_id: str,
        before: float,
        tick_statuses: Optional[Sequence["TickStatus"]] = None,
    ):
        return self._storage.schedule_storage.purge_ticks(
            origin_id, selector_id, before, tick_statuses
        )

    def upgrade(self):
        return self._storage.schedule_storage.upgrade()

    def migrate(self, print_fn: Optional[Callable] = None, force_rebuild_all: bool = False):
        return self._storage.schedule_storage.migrate(print_fn, force_rebuild_all)

    def optimize(self, print_fn: Optional[Callable] = None, force_rebuild_all: bool = False):
        return self._storage.schedule_storage.optimize(print_fn, force_rebuild_all)

    def optimize_for_dagit(self, statement_timeout: int, pool_recycle: int):
        return self._storage.schedule_storage.optimize_for_dagit(statement_timeout, pool_recycle)
