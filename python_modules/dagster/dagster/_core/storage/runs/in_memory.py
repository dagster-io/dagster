from collections import OrderedDict, defaultdict
from typing import Callable, Dict, Iterable, List, Optional, Set, Tuple, Union, cast

import dagster._check as check
from dagster._core.errors import (
    DagsterRunAlreadyExists,
    DagsterRunNotFoundError,
    DagsterSnapshotDoesNotExist,
)
from dagster._core.events import EVENT_TYPE_TO_PIPELINE_RUN_STATUS, DagsterEvent, DagsterEventType
from dagster._core.execution.backfill import BulkActionStatus, PartitionBackfill
from dagster._core.snap import (
    ExecutionPlanSnapshot,
    PipelineSnapshot,
    create_execution_plan_snapshot_id,
    create_pipeline_snapshot_id,
)
from dagster._core.storage.tags import PARTITION_NAME_TAG
from dagster._daemon.types import DaemonHeartbeat
from dagster._utils import EPOCH, frozendict, merge_dicts

from ..pipeline_run import (
    JobBucket,
    PipelineRun,
    RunPartitionData,
    RunRecord,
    RunsFilter,
    TagBucket,
)
from .base import RunStorage


def build_run_filter(filters: Optional[RunsFilter]) -> Callable[[PipelineRun], bool]:
    def _filter(run: PipelineRun) -> bool:
        if not filters:
            return True

        if filters.run_ids and run.run_id not in filters.run_ids:
            return False

        if filters.statuses and run.status not in filters.statuses:
            return False

        if filters.job_name and filters.job_name != run.pipeline_name:
            return False

        if filters.mode and filters.mode != run.mode:
            return False

        if filters.tags and not all(
            (run.tags.get(key) == value if isinstance(value, str) else run.tags.get(key) in value)
            for key, value in filters.tags.items()
        ):
            return False

        if filters.snapshot_id and filters.snapshot_id != run.pipeline_snapshot_id:
            return False

        return True

    return _filter


class InMemoryRunStorage(RunStorage):
    def __init__(self, preload=None):
        self._init_storage()
        if preload:
            for payload in preload:
                self._runs[payload.pipeline_run.run_id] = payload.pipeline_run
                self._pipeline_snapshots[
                    payload.pipeline_run.pipeline_snapshot_id
                ] = payload.pipeline_snapshot
                self._ep_snapshots[
                    payload.pipeline_run.execution_plan_snapshot_id
                ] = payload.execution_plan_snapshot

        super().__init__()

    # separate method so it can be reused in wipe
    def _init_storage(self):
        self._runs: Dict[str, PipelineRun] = OrderedDict()
        self._run_tags: Dict[str, dict] = defaultdict(dict)
        self._pipeline_snapshots: Dict[str, PipelineSnapshot] = OrderedDict()
        self._ep_snapshots: Dict[str, ExecutionPlanSnapshot] = OrderedDict()
        self._bulk_actions: Dict[str, PartitionBackfill] = OrderedDict()

    def add_run(self, pipeline_run: PipelineRun) -> PipelineRun:
        check.inst_param(pipeline_run, "pipeline_run", PipelineRun)
        if self._runs.get(pipeline_run.run_id):
            raise DagsterRunAlreadyExists(
                "Can not add same run twice for run_id {run_id}".format(run_id=pipeline_run.run_id),
            )
        if pipeline_run.pipeline_snapshot_id:
            if not self.has_pipeline_snapshot(pipeline_run.pipeline_snapshot_id):
                raise DagsterSnapshotDoesNotExist(
                    "Snapshot ID {ss_id} does not exist in run storage.".format(
                        ss_id=pipeline_run.pipeline_snapshot_id
                    )
                )

        self._runs[pipeline_run.run_id] = pipeline_run
        if pipeline_run.tags and len(pipeline_run.tags) > 0:
            self._run_tags[pipeline_run.run_id] = frozendict(pipeline_run.tags)

        return pipeline_run

    def handle_run_event(self, run_id: str, event: DagsterEvent):
        check.str_param(run_id, "run_id")
        check.inst_param(event, "event", DagsterEvent)
        if run_id not in self._runs:
            return
        run = self._runs[run_id]

        if event.event_type in [DagsterEventType.PIPELINE_START, DagsterEventType.PIPELINE_SUCCESS]:
            self._runs[run_id] = run.with_status(
                EVENT_TYPE_TO_PIPELINE_RUN_STATUS[event.event_type]
            )
        else:
            self._runs[run_id] = self._runs[run_id].with_status(
                EVENT_TYPE_TO_PIPELINE_RUN_STATUS[event.event_type]
            )

    def get_runs(
        self,
        filters: Optional[RunsFilter] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        bucket_by: Optional[Union[JobBucket, TagBucket]] = None,
    ) -> List[PipelineRun]:
        check.opt_inst_param(filters, "filters", RunsFilter)
        check.opt_str_param(cursor, "cursor")
        check.opt_int_param(limit, "limit")
        check.opt_inst_param(bucket_by, "bucket_by", (JobBucket, TagBucket))

        matching_runs = list(filter(build_run_filter(filters), list(self._runs.values())[::-1]))
        if not bucket_by:
            return self._slice(matching_runs, cursor=cursor, limit=limit)

        results = []
        bucket_counts: Dict[str, int] = defaultdict(int)
        for run in matching_runs:
            bucket_key = (
                run.pipeline_name
                if isinstance(bucket_by, JobBucket)
                else run.tags.get(bucket_by.tag_key)
            )
            if not bucket_key or (
                bucket_by.bucket_limit and bucket_counts[bucket_key] >= bucket_by.bucket_limit
            ):
                continue
            bucket_counts[bucket_key] += 1
            results.append(run)
        return results

    def get_runs_count(self, filters: Optional[RunsFilter] = None) -> int:
        check.opt_inst_param(filters, "filters", RunsFilter)

        return len(self.get_runs(filters))

    def _slice(
        self,
        items: List,
        cursor: Optional[str],
        limit: Optional[int] = None,
        key_fn: Callable = lambda _: _.run_id,
    ):
        if cursor:
            try:
                index = next(i for i, item in enumerate(items) if key_fn(item) == cursor)
            except StopIteration:
                return []
            start = index + 1
        else:
            start = 0

        end: Optional[int]
        if limit:
            end = start + limit
        else:
            end = None

        return list(items)[start:end]

    def get_run_by_id(self, run_id: str) -> Optional[PipelineRun]:
        check.str_param(run_id, "run_id")
        return self._runs.get(run_id)

    def get_run_records(
        self,
        filters: Optional[RunsFilter] = None,
        limit: Optional[int] = None,
        order_by: Optional[str] = None,
        ascending: bool = False,
        cursor: Optional[str] = None,
        bucket_by: Optional[Union[JobBucket, TagBucket]] = None,
    ) -> List[RunRecord]:
        check.opt_inst_param(filters, "filters", RunsFilter)
        check.opt_str_param(cursor, "cursor")
        check.opt_int_param(limit, "limit")

        # record here is a tuple of storage_id, run
        records = enumerate(list(self._runs.values()))
        run_filter_fn = build_run_filter(filters)
        record_filter_fn = lambda record: run_filter_fn(record[1])

        matching_records = list(filter(record_filter_fn, list(records)[::-1]))
        sliced = self._slice(matching_records, cursor=cursor, limit=limit)
        return [
            RunRecord(
                storage_id=record[0],
                pipeline_run=record[1],
                create_timestamp=EPOCH,  # hack just to populate some timestamp
                update_timestamp=EPOCH,  # hack just to populate some timestamp
            )
            for record in sliced
        ]

    def get_run_tags(self) -> List[Tuple[str, Set[str]]]:
        all_tags = defaultdict(set)
        for _run_id, tags in self._run_tags.items():
            for k, v in tags.items():
                all_tags[k].add(v)

        return sorted([(k, v) for k, v in all_tags.items()], key=lambda x: x[0])

    def add_run_tags(self, run_id: str, new_tags: Dict[str, str]):
        check.str_param(run_id, "run_id")
        check.dict_param(new_tags, "new_tags", key_type=str, value_type=str)
        run = self._runs[run_id]
        run_tags = merge_dicts(run.tags if run.tags else {}, new_tags)
        self._runs[run_id] = run.with_tags(run_tags)
        self._run_tags[run_id] = frozendict(run_tags)

    def has_run(self, run_id: str) -> bool:
        check.str_param(run_id, "run_id")
        return run_id in self._runs

    def delete_run(self, run_id: str):
        check.str_param(run_id, "run_id")
        del self._runs[run_id]
        if run_id in self._run_tags:
            del self._run_tags[run_id]

    def has_pipeline_snapshot(self, pipeline_snapshot_id: str) -> bool:
        check.str_param(pipeline_snapshot_id, "pipeline_snapshot_id")
        return pipeline_snapshot_id in self._pipeline_snapshots

    def add_pipeline_snapshot(
        self, pipeline_snapshot: PipelineSnapshot, snapshot_id: Optional[str] = None
    ) -> str:
        check.inst_param(pipeline_snapshot, "pipeline_snapshot", PipelineSnapshot)
        check.opt_str_param(snapshot_id, "snapshot_id")
        if not snapshot_id:
            snapshot_id = create_pipeline_snapshot_id(pipeline_snapshot)
        self._pipeline_snapshots[snapshot_id] = pipeline_snapshot
        return snapshot_id

    def get_pipeline_snapshot(self, pipeline_snapshot_id: str) -> PipelineSnapshot:
        check.str_param(pipeline_snapshot_id, "pipeline_snapshot_id")
        return self._pipeline_snapshots[pipeline_snapshot_id]

    def has_execution_plan_snapshot(self, execution_plan_snapshot_id: str) -> bool:
        check.str_param(execution_plan_snapshot_id, "execution_plan_snapshot_id")
        return execution_plan_snapshot_id in self._ep_snapshots

    def add_execution_plan_snapshot(
        self, execution_plan_snapshot: ExecutionPlanSnapshot, snapshot_id: Optional[str] = None
    ) -> str:
        check.inst_param(execution_plan_snapshot, "execution_plan_snapshot", ExecutionPlanSnapshot)
        check.opt_str_param(snapshot_id, "snapshot_id")
        if not snapshot_id:
            snapshot_id = create_execution_plan_snapshot_id(execution_plan_snapshot)
        self._ep_snapshots[snapshot_id] = execution_plan_snapshot
        return snapshot_id

    def get_execution_plan_snapshot(self, execution_plan_snapshot_id: str) -> ExecutionPlanSnapshot:
        check.str_param(execution_plan_snapshot_id, "execution_plan_snapshot_id")
        return self._ep_snapshots[execution_plan_snapshot_id]

    def wipe(self):
        self._init_storage()

    def get_run_group(self, run_id: str) -> Optional[Tuple[str, List[PipelineRun]]]:
        check.str_param(run_id, "run_id")
        pipeline_run = self._runs.get(run_id)
        if not pipeline_run:
            raise DagsterRunNotFoundError(
                f"Run {run_id} was not found in instance.", invalid_run_id=run_id
            )
        # if the run doesn't have root_run_id, itself is the root
        root_run = (
            self.get_run_by_id(pipeline_run.root_run_id)
            if pipeline_run.root_run_id
            else pipeline_run
        )
        if not root_run:
            return None
        run_group = [root_run]
        for curr_run in self._runs.values():
            if curr_run.root_run_id == root_run.run_id:
                run_group.append(curr_run)
        return (cast(str, root_run.root_run_id), run_group)

    def get_run_groups(
        self,
        filters: Optional[RunsFilter] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Dict[str, Union[Iterable[PipelineRun], int]]]:
        runs = self.get_runs(filters=filters, cursor=cursor, limit=limit)
        root_run_id_to_group: Dict[str, Dict[str, PipelineRun]] = defaultdict(dict)
        for run in runs:
            root_run_id = run.get_root_run_id()
            if root_run_id is not None:
                root_run_id_to_group[root_run_id][run.run_id] = run
            else:
                # this run is the root run
                root_run_id_to_group[run.run_id][run.run_id] = run

        # add root run to the group if it's not already there
        for root_run_id in root_run_id_to_group:
            if root_run_id not in root_run_id_to_group[root_run_id]:
                root_pipeline_run = self.get_run_by_id(root_run_id)
                if root_pipeline_run:
                    root_run_id_to_group[root_run_id][root_run_id] = root_pipeline_run

        # counts total number of runs in a run group, including the ones don't match the given filter
        root_run_id_to_count: Dict[str, int] = defaultdict(int)
        for run in self.get_runs():
            root_run_id = run.get_root_run_id() or run.run_id
            if root_run_id in root_run_id_to_group:
                root_run_id_to_count[root_run_id] += 1

        return {
            root_run_id: {
                "runs": list(run_group.values()),
                "count": root_run_id_to_count[root_run_id],
            }
            for root_run_id, run_group in root_run_id_to_group.items()
        }

    def get_run_partition_data(self, runs_filter: RunsFilter) -> List[RunPartitionData]:
        """Get run partition data for a given partitioned job."""
        run_filter = build_run_filter(runs_filter)
        matching_runs = list(filter(run_filter, list(self._runs.values())[::-1]))
        _partition_data_by_partition = {}
        for run in matching_runs:
            partition = run.tags.get(PARTITION_NAME_TAG)
            if not partition or partition in _partition_data_by_partition:
                continue

            _partition_data_by_partition[partition] = RunPartitionData(
                run_id=run.run_id,
                partition=partition,
                status=run.status,
                start_time=None,
                end_time=None,
            )

        return list(_partition_data_by_partition.values())

    # Daemon Heartbeats

    def add_daemon_heartbeat(self, daemon_heartbeat: DaemonHeartbeat):
        raise NotImplementedError(
            "The dagster daemon lives in a separate process. It cannot use in memory storage."
        )

    def get_daemon_heartbeats(self) -> Dict[str, DaemonHeartbeat]:
        return {}

    def wipe_daemon_heartbeats(self):
        raise NotImplementedError(
            "The dagster daemon lives in a separate process. It cannot use in memory storage."
        )

    def get_backfills(
        self,
        status: Optional[BulkActionStatus] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[PartitionBackfill]:
        check.opt_inst_param(status, "status", BulkActionStatus)
        backfills = [
            backfill
            for backfill in self._bulk_actions.values()
            if not status or status == backfill.status
        ]
        return self._slice(backfills[::-1], cursor, limit, key_fn=lambda _: _.backfill_id)

    def get_backfill(self, backfill_id: str) -> Optional[PartitionBackfill]:
        check.str_param(backfill_id, "backfill_id")
        return self._bulk_actions.get(backfill_id)

    def add_backfill(self, partition_backfill: PartitionBackfill):
        check.inst_param(partition_backfill, "partition_backfill", PartitionBackfill)
        self._bulk_actions[partition_backfill.backfill_id] = partition_backfill

    def update_backfill(self, partition_backfill: PartitionBackfill):
        check.inst_param(partition_backfill, "partition_backfill", PartitionBackfill)
        self._bulk_actions[partition_backfill.backfill_id] = partition_backfill

    def supports_kvs(self):
        return False

    def kvs_get(self, keys: Set[str]) -> Dict[str, str]:
        raise NotImplementedError()

    def kvs_set(self, pairs: Dict[str, str]) -> None:
        raise NotImplementedError()
