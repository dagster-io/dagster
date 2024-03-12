from typing import (
    TYPE_CHECKING,
    Iterable,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
)

from dagster import (
    _check as check,
)
from dagster._config.config_schema import UserConfigSchema
from dagster._core.definitions.asset_condition.asset_condition import (
    AssetConditionEvaluationWithRunIds,
)
from dagster._core.definitions.events import AssetKey
from dagster._core.event_api import EventHandlerFn
from dagster._core.storage.asset_check_execution_record import (
    AssetCheckExecutionRecord,
)
from dagster._serdes import ConfigurableClass, ConfigurableClassData
from dagster._utils import PrintFn
from dagster._utils.concurrency import ConcurrencyClaimStatus, ConcurrencyKeyInfo

from .base_storage import DagsterStorage
from .event_log.base import (
    AssetRecord,
    EventLogConnection,
    EventLogRecord,
    EventLogStorage,
    EventRecordsFilter,
    EventRecordsResult,
    PlannedMaterializationInfo,
)
from .runs.base import RunStorage
from .schedules.base import ScheduleStorage

if TYPE_CHECKING:
    from dagster._core.definitions.asset_check_spec import AssetCheckKey
    from dagster._core.definitions.run_request import InstigatorType
    from dagster._core.event_api import AssetRecordsFilter, RunStatusChangeRecordsFilter
    from dagster._core.events import DagsterEvent, DagsterEventType
    from dagster._core.events.log import EventLogEntry
    from dagster._core.execution.backfill import BulkActionStatus, PartitionBackfill
    from dagster._core.execution.stats import RunStepKeyStatsSnapshot
    from dagster._core.instance import DagsterInstance
    from dagster._core.remote_representation.origin import ExternalJobOrigin
    from dagster._core.scheduler.instigation import (
        AutoMaterializeAssetEvaluationRecord,
        InstigatorState,
        InstigatorStatus,
        InstigatorTick,
        TickData,
        TickStatus,
    )
    from dagster._core.snap.execution_plan_snapshot import ExecutionPlanSnapshot
    from dagster._core.snap.job_snapshot import JobSnapshot
    from dagster._core.storage.dagster_run import (
        DagsterRun,
        DagsterRunStatsSnapshot,
        JobBucket,
        RunPartitionData,
        RunRecord,
        RunsFilter,
        TagBucket,
    )
    from dagster._core.storage.partition_status_cache import AssetStatusCacheValue
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
        inst_data: Optional[ConfigurableClassData] = None,
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
    def inst_data(self) -> Optional[ConfigurableClassData]:
        return self._inst_data

    @classmethod
    def config_type(cls) -> UserConfigSchema:
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

    @classmethod
    def from_config_value(
        cls,
        inst_data: Optional[ConfigurableClassData],
        config_value: Mapping[str, Mapping[str, str]],
    ) -> "CompositeStorage":
        run_storage_config = config_value["run_storage"]
        run_storage = ConfigurableClassData(
            module_name=run_storage_config["module_name"],
            class_name=run_storage_config["class_name"],
            config_yaml=run_storage_config["config_yaml"],
        ).rehydrate(as_type=RunStorage)
        event_log_storage_config = config_value["event_log_storage"]
        event_log_storage = ConfigurableClassData(
            module_name=event_log_storage_config["module_name"],
            class_name=event_log_storage_config["class_name"],
            config_yaml=event_log_storage_config["config_yaml"],
        ).rehydrate(as_type=EventLogStorage)
        schedule_storage_config = config_value["schedule_storage"]
        schedule_storage = ConfigurableClassData(
            module_name=schedule_storage_config["module_name"],
            class_name=schedule_storage_config["class_name"],
            config_yaml=schedule_storage_config["config_yaml"],
        ).rehydrate(as_type=ScheduleStorage)
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
    def __init__(self, storage: DagsterStorage, inst_data: Optional[ConfigurableClassData] = None):
        self._storage = check.inst_param(storage, "storage", DagsterStorage)
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)
        super().__init__()

    @property
    def inst_data(self) -> Optional[ConfigurableClassData]:
        return self._inst_data

    @property
    def _instance(self) -> Optional["DagsterInstance"]:
        return self._storage._instance  # noqa: SLF001

    def register_instance(self, instance: "DagsterInstance") -> None:
        if not self._storage.has_instance:
            self._storage.register_instance(instance)

    @classmethod
    def config_type(cls) -> UserConfigSchema:
        return {
            "module_name": str,
            "class_name": str,
            "config_yaml": str,
        }

    @classmethod
    def from_config_value(
        cls, inst_data: Optional[ConfigurableClassData], config_value: Mapping[str, str]
    ) -> "LegacyRunStorage":
        storage = ConfigurableClassData(
            module_name=config_value["module_name"],
            class_name=config_value["class_name"],
            config_yaml=config_value["config_yaml"],
        ).rehydrate(as_type=DagsterStorage)
        return LegacyRunStorage(storage, inst_data=inst_data)

    def add_run(self, dagster_run: "DagsterRun") -> "DagsterRun":
        return self._storage.run_storage.add_run(dagster_run)

    def handle_run_event(self, run_id: str, event: "DagsterEvent") -> None:
        return self._storage.run_storage.handle_run_event(run_id, event)

    def get_runs(
        self,
        filters: Optional["RunsFilter"] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        bucket_by: Optional[Union["JobBucket", "TagBucket"]] = None,
        ascending: bool = False,
    ) -> Iterable["DagsterRun"]:
        return self._storage.run_storage.get_runs(filters, cursor, limit, bucket_by, ascending)

    def get_run_ids(
        self,
        filters: Optional["RunsFilter"] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Iterable[str]:
        return self._storage.run_storage.get_run_ids(filters, cursor=cursor, limit=limit)

    def get_runs_count(self, filters: Optional["RunsFilter"] = None) -> int:
        return self._storage.run_storage.get_runs_count(filters)

    def get_run_group(self, run_id: str) -> Optional[Tuple[str, Iterable["DagsterRun"]]]:
        return self._storage.run_storage.get_run_group(run_id)

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

    def get_run_tags(
        self,
        tag_keys: Sequence[str],
        value_prefix: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Sequence[Tuple[str, Set[str]]]:
        return self._storage.run_storage.get_run_tags(tag_keys, value_prefix, limit)

    def get_run_tag_keys(self) -> Sequence[str]:
        return self._storage.run_storage.get_run_tag_keys()

    def add_run_tags(self, run_id: str, new_tags: Mapping[str, str]):
        return self._storage.run_storage.add_run_tags(run_id, new_tags)

    def has_run(self, run_id: str) -> bool:
        return self._storage.run_storage.has_run(run_id)

    def add_snapshot(
        self,
        snapshot: Union["JobSnapshot", "ExecutionPlanSnapshot"],
        snapshot_id: Optional[str] = None,
    ) -> None:
        return self._storage.run_storage.add_snapshot(snapshot, snapshot_id)

    def has_snapshot(self, snapshot_id: str) -> bool:
        return self._storage.run_storage.has_snapshot(snapshot_id)

    def has_job_snapshot(self, job_snapshot_id: str) -> bool:
        return self._storage.run_storage.has_job_snapshot(job_snapshot_id)

    def add_job_snapshot(
        self, job_snapshot: "JobSnapshot", snapshot_id: Optional[str] = None
    ) -> str:
        return self._storage.run_storage.add_job_snapshot(job_snapshot, snapshot_id)

    def get_job_snapshot(self, job_snapshot_id: str) -> "JobSnapshot":
        return self._storage.run_storage.get_job_snapshot(job_snapshot_id)

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

    def wipe(self) -> None:
        return self._storage.run_storage.wipe()

    def delete_run(self, run_id: str) -> None:
        return self._storage.run_storage.delete_run(run_id)

    def migrate(self, print_fn: Optional[PrintFn] = None, force_rebuild_all: bool = False) -> None:
        return self._storage.run_storage.migrate(print_fn, force_rebuild_all)

    def optimize(self, print_fn: Optional[PrintFn] = None, force_rebuild_all: bool = False) -> None:
        return self._storage.run_storage.optimize(print_fn, force_rebuild_all)

    def dispose(self) -> None:
        return self._storage.run_storage.dispose()

    def optimize_for_webserver(self, statement_timeout: int, pool_recycle: int) -> None:
        return self._storage.run_storage.optimize_for_webserver(statement_timeout, pool_recycle)

    def add_daemon_heartbeat(self, daemon_heartbeat: "DaemonHeartbeat") -> None:
        return self._storage.run_storage.add_daemon_heartbeat(daemon_heartbeat)

    def get_daemon_heartbeats(self) -> Mapping[str, "DaemonHeartbeat"]:
        return self._storage.run_storage.get_daemon_heartbeats()

    def wipe_daemon_heartbeats(self) -> None:
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

    def add_backfill(self, partition_backfill: "PartitionBackfill") -> None:
        return self._storage.run_storage.add_backfill(partition_backfill)

    def update_backfill(self, partition_backfill: "PartitionBackfill") -> None:
        return self._storage.run_storage.update_backfill(partition_backfill)

    def get_run_partition_data(self, runs_filter: "RunsFilter") -> Sequence["RunPartitionData"]:
        return self._storage.run_storage.get_run_partition_data(runs_filter)

    def get_cursor_values(self, keys: Set[str]) -> Mapping[str, str]:
        return self._storage.run_storage.get_cursor_values(keys)

    def set_cursor_values(self, pairs: Mapping[str, str]) -> None:
        return self._storage.run_storage.set_cursor_values(pairs)

    def replace_job_origin(self, run: "DagsterRun", job_origin: "ExternalJobOrigin") -> None:
        return self._storage.run_storage.replace_job_origin(run, job_origin)


class LegacyEventLogStorage(EventLogStorage, ConfigurableClass):
    def __init__(self, storage: DagsterStorage, inst_data: Optional[ConfigurableClassData] = None):
        self._storage = check.inst_param(storage, "storage", DagsterStorage)
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)
        super().__init__()

    @property
    def inst_data(self) -> Optional[ConfigurableClassData]:
        return self._inst_data

    @classmethod
    def config_type(cls) -> UserConfigSchema:
        return {
            "module_name": str,
            "class_name": str,
            "config_yaml": str,
        }

    @classmethod
    def from_config_value(
        cls, inst_data: Optional[ConfigurableClassData], config_value: Mapping[str, str]
    ) -> "LegacyEventLogStorage":
        storage = ConfigurableClassData(
            module_name=config_value["module_name"],
            class_name=config_value["class_name"],
            config_yaml=config_value["config_yaml"],
        ).rehydrate(as_type=DagsterStorage)
        # Type checker says LegacyEventStorage is abstract and can't be instantiated. Not sure whether
        # type check is wrong, or is unused code path.
        return LegacyEventLogStorage(storage, inst_data=inst_data)

    @property
    def _instance(self) -> Optional["DagsterInstance"]:
        return self._storage._instance  # noqa: SLF001

    def index_connection(self):
        return self._storage.event_log_storage.index_connection()

    def register_instance(self, instance: "DagsterInstance") -> None:
        if not self._storage.has_instance:
            self._storage.register_instance(instance)

    def get_logs_for_run(
        self,
        run_id: str,
        cursor: Optional[Union[str, int]] = None,
        of_type: Optional[Union["DagsterEventType", Set["DagsterEventType"]]] = None,
        limit: Optional[int] = None,
        ascending: bool = True,
    ) -> Iterable["EventLogEntry"]:
        return self._storage.event_log_storage.get_logs_for_run(
            run_id, cursor, of_type, limit, ascending
        )

    def get_stats_for_run(self, run_id: str) -> "DagsterRunStatsSnapshot":
        return self._storage.event_log_storage.get_stats_for_run(run_id)

    def get_step_stats_for_run(
        self, run_id: str, step_keys: Optional[Sequence[str]] = None
    ) -> Sequence["RunStepKeyStatsSnapshot"]:
        return self._storage.event_log_storage.get_step_stats_for_run(run_id, step_keys)

    def store_event(self, event: "EventLogEntry") -> None:
        return self._storage.event_log_storage.store_event(event)

    def delete_events(self, run_id: str) -> None:
        return self._storage.event_log_storage.delete_events(run_id)

    def upgrade(self) -> None:
        return self._storage.event_log_storage.upgrade()

    def reindex_events(self, print_fn: Optional[PrintFn] = None, force: bool = False) -> None:
        return self._storage.event_log_storage.reindex_events(print_fn, force)

    def reindex_assets(self, print_fn: Optional[PrintFn] = None, force: bool = False) -> None:
        return self._storage.event_log_storage.reindex_assets(print_fn, force)

    def wipe(self) -> None:
        return self._storage.event_log_storage.wipe()

    def watch(self, run_id: str, cursor: str, callback: EventHandlerFn) -> None:
        return self._storage.event_log_storage.watch(run_id, cursor, callback)

    def end_watch(self, run_id: str, handler: EventHandlerFn) -> None:
        return self._storage.event_log_storage.end_watch(run_id, handler)

    @property
    def is_persistent(self) -> bool:
        return self._storage.event_log_storage.is_persistent

    def dispose(self) -> None:
        return self._storage.event_log_storage.dispose()

    def optimize_for_webserver(self, statement_timeout: int, pool_recycle: int) -> None:
        return self._storage.event_log_storage.optimize_for_webserver(
            statement_timeout, pool_recycle
        )

    def get_event_records(
        self,
        event_records_filter: Optional[EventRecordsFilter] = None,
        limit: Optional[int] = None,
        ascending: bool = False,
    ) -> Iterable[EventLogRecord]:
        # type ignored because `get_event_records` does not accept None. Unclear which type
        # annotation is wrong.
        return self._storage.event_log_storage.get_event_records(
            event_records_filter,  # type: ignore
            limit,
            ascending,
        )

    def fetch_materializations(
        self,
        filters: Union[AssetKey, "AssetRecordsFilter"],
        limit: int,
        cursor: Optional[str] = None,
        ascending: bool = False,
    ) -> EventRecordsResult:
        return self._storage.event_log_storage.fetch_materializations(
            filters, limit, cursor, ascending
        )

    def fetch_observations(
        self,
        filters: Union[AssetKey, "AssetRecordsFilter"],
        limit: int,
        cursor: Optional[str] = None,
        ascending: bool = False,
    ) -> EventRecordsResult:
        return self._storage.event_log_storage.fetch_observations(filters, limit, cursor, ascending)

    def fetch_run_status_changes(
        self,
        filters: Union["DagsterEventType", "RunStatusChangeRecordsFilter"],
        limit: int,
        cursor: Optional[str] = None,
        ascending: bool = False,
    ) -> EventRecordsResult:
        return self._storage.event_log_storage.fetch_run_status_changes(
            filters, limit, cursor, ascending
        )

    def get_latest_planned_materialization_info(
        self,
        asset_key: AssetKey,
        partition: Optional[str] = None,
    ) -> Optional[PlannedMaterializationInfo]:
        return self._storage.event_log_storage.get_latest_planned_materialization_info(
            asset_key, partition
        )

    def get_asset_records(
        self, asset_keys: Optional[Sequence["AssetKey"]] = None
    ) -> Iterable[AssetRecord]:
        return self._storage.event_log_storage.get_asset_records(asset_keys)

    def has_asset_key(self, asset_key: "AssetKey") -> bool:
        return self._storage.event_log_storage.has_asset_key(asset_key)

    def all_asset_keys(self) -> Iterable["AssetKey"]:
        return self._storage.event_log_storage.all_asset_keys()

    def get_asset_keys(
        self,
        prefix: Optional[Sequence[str]] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Iterable["AssetKey"]:
        return self._storage.event_log_storage.get_asset_keys(prefix, limit, cursor)

    def get_latest_materialization_events(
        self, asset_keys: Iterable["AssetKey"]
    ) -> Mapping["AssetKey", Optional["EventLogEntry"]]:
        return self._storage.event_log_storage.get_latest_materialization_events(asset_keys)

    def wipe_asset(self, asset_key: "AssetKey") -> None:
        return self._storage.event_log_storage.wipe_asset(asset_key)

    def get_materialized_partitions(
        self,
        asset_key: AssetKey,
        before_cursor: Optional[int] = None,
        after_cursor: Optional[int] = None,
    ) -> Set[str]:
        return self._storage.event_log_storage.get_materialized_partitions(
            asset_key, before_cursor, after_cursor
        )

    def get_latest_storage_id_by_partition(
        self, asset_key: "AssetKey", event_type: "DagsterEventType"
    ) -> Mapping[str, int]:
        return self._storage.event_log_storage.get_latest_storage_id_by_partition(
            asset_key, event_type
        )

    def get_latest_tags_by_partition(
        self,
        asset_key: "AssetKey",
        event_type: "DagsterEventType",
        tag_keys: Sequence[str],
        asset_partitions: Optional[Sequence[str]] = None,
        before_cursor: Optional[int] = None,
        after_cursor: Optional[int] = None,
    ) -> Mapping[str, Mapping[str, str]]:
        return self._storage.event_log_storage.get_latest_tags_by_partition(
            asset_key, event_type, tag_keys, asset_partitions, before_cursor, after_cursor
        )

    def get_latest_asset_partition_materialization_attempts_without_materializations(
        self, asset_key: "AssetKey", after_storage_id: Optional[int] = None
    ) -> Mapping[str, Tuple[str, int]]:
        return self._storage.event_log_storage.get_latest_asset_partition_materialization_attempts_without_materializations(
            asset_key, after_storage_id
        )

    def get_dynamic_partitions(self, partitions_def_name: str) -> Sequence[str]:
        return self._storage.event_log_storage.get_dynamic_partitions(partitions_def_name)

    def has_dynamic_partition(self, partitions_def_name: str, partition_key: str) -> bool:
        return self._storage.event_log_storage.has_dynamic_partition(
            partitions_def_name, partition_key
        )

    def add_dynamic_partitions(
        self, partitions_def_name: str, partition_keys: Sequence[str]
    ) -> None:
        return self._storage.event_log_storage.add_dynamic_partitions(
            partitions_def_name, partition_keys
        )

    def delete_dynamic_partition(self, partitions_def_name: str, partition_key: str) -> None:
        return self._storage.event_log_storage.delete_dynamic_partition(
            partitions_def_name, partition_key
        )

    def get_event_tags_for_asset(
        self,
        asset_key: "AssetKey",
        filter_tags: Optional[Mapping[str, str]] = None,
        filter_event_id: Optional[int] = None,
    ) -> Sequence[Mapping[str, str]]:
        return self._storage.event_log_storage.get_event_tags_for_asset(
            asset_key, filter_tags, filter_event_id
        )

    def can_cache_asset_status_data(self) -> bool:
        return self._storage.event_log_storage.can_cache_asset_status_data()

    def wipe_asset_cached_status(self, asset_key: "AssetKey") -> None:
        return self._storage.event_log_storage.wipe_asset_cached_status(asset_key)

    def update_asset_cached_status_data(
        self, asset_key: "AssetKey", cache_values: "AssetStatusCacheValue"
    ) -> None:
        self._storage.event_log_storage.update_asset_cached_status_data(
            asset_key=asset_key, cache_values=cache_values
        )

    def get_records_for_run(
        self,
        run_id: str,
        cursor: Optional[str] = None,
        of_type: Optional[Union["DagsterEventType", Set["DagsterEventType"]]] = None,
        limit: Optional[int] = None,
        ascending: bool = True,
    ) -> EventLogConnection:
        return self._storage.event_log_storage.get_records_for_run(
            run_id, cursor, of_type, limit, ascending
        )

    def initialize_concurrency_limit_to_default(self, concurrency_key: str) -> bool:
        return self._storage.event_log_storage.initialize_concurrency_limit_to_default(
            concurrency_key
        )

    def set_concurrency_slots(self, concurrency_key: str, num: int) -> None:
        return self._storage.event_log_storage.set_concurrency_slots(concurrency_key, num)

    def delete_concurrency_limit(self, concurrency_key: str) -> None:
        return self._storage.event_log_storage.delete_concurrency_limit(concurrency_key)

    def get_concurrency_keys(self) -> Set[str]:
        return self._storage.event_log_storage.get_concurrency_keys()

    def get_concurrency_info(self, concurrency_key: str) -> ConcurrencyKeyInfo:
        return self._storage.event_log_storage.get_concurrency_info(concurrency_key)

    def claim_concurrency_slot(
        self, concurrency_key: str, run_id: str, step_key: str, priority: Optional[int] = None
    ) -> ConcurrencyClaimStatus:
        return self._storage.event_log_storage.claim_concurrency_slot(
            concurrency_key, run_id, step_key, priority
        )

    def check_concurrency_claim(self, concurrency_key: str, run_id: str, step_key: str):
        return self._storage.event_log_storage.check_concurrency_claim(
            concurrency_key, run_id, step_key
        )

    def get_concurrency_run_ids(self) -> Set[str]:
        return self._storage.event_log_storage.get_concurrency_run_ids()

    def free_concurrency_slots_for_run(self, run_id: str) -> None:
        return self._storage.event_log_storage.free_concurrency_slots_for_run(run_id)

    def free_concurrency_slot_for_step(self, run_id: str, step_key: str) -> None:
        return self._storage.event_log_storage.free_concurrency_slot_for_step(run_id, step_key)

    def get_asset_check_execution_history(
        self,
        check_key: "AssetCheckKey",
        limit: int,
        cursor: Optional[int] = None,
    ) -> Sequence[AssetCheckExecutionRecord]:
        return self._storage.event_log_storage.get_asset_check_execution_history(
            check_key=check_key,
            limit=limit,
            cursor=cursor,
        )

    def get_latest_asset_check_execution_by_key(
        self,
        check_keys: Sequence["AssetCheckKey"],
    ) -> Mapping["AssetCheckKey", Optional[AssetCheckExecutionRecord]]:
        return self._storage.event_log_storage.get_latest_asset_check_execution_by_key(check_keys)


class LegacyScheduleStorage(ScheduleStorage, ConfigurableClass):
    def __init__(self, storage: DagsterStorage, inst_data: Optional[ConfigurableClassData] = None):
        self._storage = check.inst_param(storage, "storage", DagsterStorage)
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)
        super().__init__()

    @property
    def inst_data(self) -> Optional[ConfigurableClassData]:
        return self._inst_data

    @classmethod
    def config_type(cls) -> UserConfigSchema:
        return {
            "module_name": str,
            "class_name": str,
            "config_yaml": str,
        }

    @classmethod
    def from_config_value(
        cls, inst_data: Optional[ConfigurableClassData], config_value: Mapping[str, str]
    ) -> "LegacyScheduleStorage":
        storage = ConfigurableClassData(
            module_name=config_value["module_name"],
            class_name=config_value["class_name"],
            config_yaml=config_value["config_yaml"],
        ).rehydrate(as_type=DagsterStorage)
        return LegacyScheduleStorage(storage, inst_data=inst_data)

    @property
    def _instance(self) -> Optional["DagsterInstance"]:
        return self._storage._instance  # noqa: SLF001

    def register_instance(self, instance: "DagsterInstance") -> None:
        if not self._storage.has_instance:
            self._storage.register_instance(instance)

    def wipe(self) -> None:
        return self._storage.schedule_storage.wipe()

    def all_instigator_state(
        self,
        repository_origin_id: Optional[str] = None,
        repository_selector_id: Optional[str] = None,
        instigator_type: Optional["InstigatorType"] = None,
        instigator_statuses: Optional[Set["InstigatorStatus"]] = None,
    ) -> Iterable["InstigatorState"]:
        return self._storage.schedule_storage.all_instigator_state(
            repository_origin_id, repository_selector_id, instigator_type, instigator_statuses
        )

    def get_instigator_state(self, origin_id: str, selector_id: str) -> Optional["InstigatorState"]:
        return self._storage.schedule_storage.get_instigator_state(origin_id, selector_id)

    def add_instigator_state(self, state: "InstigatorState") -> "InstigatorState":
        return self._storage.schedule_storage.add_instigator_state(state)

    def update_instigator_state(self, state: "InstigatorState") -> "InstigatorState":
        return self._storage.schedule_storage.update_instigator_state(state)

    def delete_instigator_state(self, origin_id: str, selector_id: str) -> None:
        return self._storage.schedule_storage.delete_instigator_state(origin_id, selector_id)

    @property
    def supports_batch_queries(self) -> bool:
        return self._storage.schedule_storage.supports_batch_queries

    def get_batch_ticks(
        self,
        selector_ids: Sequence[str],
        limit: Optional[int] = None,
        statuses: Optional[Sequence["TickStatus"]] = None,
    ) -> Mapping[str, Iterable["InstigatorTick"]]:
        return self._storage.schedule_storage.get_batch_ticks(selector_ids, limit, statuses)

    def get_tick(self, tick_id: int) -> "InstigatorTick":
        return self._storage.schedule_storage.get_tick(tick_id)

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

    def create_tick(self, tick_data: "TickData") -> "InstigatorTick":
        return self._storage.schedule_storage.create_tick(tick_data)

    def update_tick(self, tick: "InstigatorTick") -> "InstigatorTick":
        return self._storage.schedule_storage.update_tick(tick)

    def purge_ticks(
        self,
        origin_id: str,
        selector_id: str,
        before: float,
        tick_statuses: Optional[Sequence["TickStatus"]] = None,
    ) -> None:
        return self._storage.schedule_storage.purge_ticks(
            origin_id, selector_id, before, tick_statuses
        )

    def add_auto_materialize_asset_evaluations(
        self,
        evaluation_id: int,
        asset_evaluations: Sequence[AssetConditionEvaluationWithRunIds],
    ) -> None:
        return self._storage.schedule_storage.add_auto_materialize_asset_evaluations(
            evaluation_id, asset_evaluations
        )

    def get_auto_materialize_asset_evaluations(
        self, asset_key: AssetKey, limit: int, cursor: Optional[int] = None
    ) -> Sequence["AutoMaterializeAssetEvaluationRecord"]:
        return self._storage.schedule_storage.get_auto_materialize_asset_evaluations(
            asset_key, limit, cursor
        )

    def get_auto_materialize_evaluations_for_evaluation_id(
        self, evaluation_id: int
    ) -> Sequence["AutoMaterializeAssetEvaluationRecord"]:
        return self._storage.schedule_storage.get_auto_materialize_evaluations_for_evaluation_id(
            evaluation_id
        )

    def purge_asset_evaluations(self, before: float):
        return self._storage.schedule_storage.purge_asset_evaluations(before)

    def upgrade(self) -> None:
        return self._storage.schedule_storage.upgrade()

    def migrate(self, print_fn: Optional[PrintFn] = None, force_rebuild_all: bool = False) -> None:
        return self._storage.schedule_storage.migrate(print_fn, force_rebuild_all)

    def optimize(self, print_fn: Optional[PrintFn] = None, force_rebuild_all: bool = False) -> None:
        return self._storage.schedule_storage.optimize(print_fn, force_rebuild_all)

    def optimize_for_webserver(self, statement_timeout: int, pool_recycle: int) -> None:
        return self._storage.schedule_storage.optimize_for_webserver(
            statement_timeout, pool_recycle
        )

    def dispose(self) -> None:
        return self._storage.schedule_storage.dispose()
