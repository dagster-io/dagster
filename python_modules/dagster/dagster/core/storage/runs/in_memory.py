from collections import OrderedDict, defaultdict

from dagster import check
from dagster.core.errors import DagsterRunAlreadyExists, DagsterSnapshotDoesNotExist
from dagster.core.events import DagsterEvent, DagsterEventType
from dagster.core.snap import (
    ExecutionPlanSnapshot,
    PipelineSnapshot,
    create_execution_plan_snapshot_id,
    create_pipeline_snapshot_id,
)
from dagster.utils import frozendict, merge_dicts

from ..pipeline_run import PipelineRun, PipelineRunStatus, PipelineRunsFilter
from .base import RunStorage


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

    # separate method so it can be reused in wipe
    def _init_storage(self):
        self._runs = OrderedDict()
        self._run_tags = defaultdict(dict)
        self._pipeline_snapshots = OrderedDict()
        self._ep_snapshots = OrderedDict()

    def add_run(self, pipeline_run):
        check.inst_param(pipeline_run, "pipeline_run", PipelineRun)
        if self._runs.get(pipeline_run.run_id):
            raise DagsterRunAlreadyExists(
                "Can not add same run twice for run_id {run_id}".format(run_id=pipeline_run.run_id),
            )
        if pipeline_run.pipeline_snapshot_id:
            if not self.has_pipeline_snapshot(pipeline_run.pipeline_snapshot_id):
                raise DagsterSnapshotDoesNotExist(
                    "pipeline_snapshot_id {ss_id} does not exist in run storage.".format(
                        ss_id=pipeline_run.pipeline_snapshot_id
                    )
                )

        self._runs[pipeline_run.run_id] = pipeline_run
        if pipeline_run.tags and len(pipeline_run.tags) > 0:
            self._run_tags[pipeline_run.run_id] = frozendict(pipeline_run.tags)

        return pipeline_run

    def handle_run_event(self, run_id, event):
        check.str_param(run_id, "run_id")
        check.inst_param(event, "event", DagsterEvent)
        run = self._runs[run_id]

        if event.event_type == DagsterEventType.PIPELINE_START:
            self._runs[run_id] = run.with_status(PipelineRunStatus.STARTED)
        elif event.event_type == DagsterEventType.PIPELINE_SUCCESS:
            self._runs[run_id] = run.with_status(PipelineRunStatus.SUCCESS)
        elif event.event_type == DagsterEventType.PIPELINE_INIT_FAILURE:
            self._runs[run_id] = self._runs[run_id].with_status(PipelineRunStatus.FAILURE)
        elif event.event_type == DagsterEventType.PIPELINE_FAILURE:
            self._runs[run_id] = self._runs[run_id].with_status(PipelineRunStatus.FAILURE)
        elif event.event_type == DagsterEventType.PIPELINE_ENQUEUED:
            self._runs[run_id] = self._runs[run_id].with_status(PipelineRunStatus.QUEUED)
        elif event.event_type == DagsterEventType.PIPELINE_STARTING:
            self._runs[run_id] = self._runs[run_id].with_status(PipelineRunStatus.STARTING)
        elif event.event_type == DagsterEventType.PIPELINE_CANCELING:
            self._runs[run_id] = self._runs[run_id].with_status(PipelineRunStatus.CANCELING)
        elif event.event_type == DagsterEventType.PIPELINE_CANCELED:
            self._runs[run_id] = self._runs[run_id].with_status(PipelineRunStatus.CANCELED)

    def get_runs(self, filters=None, cursor=None, limit=None):
        check.opt_inst_param(filters, "filters", PipelineRunsFilter)
        check.opt_str_param(cursor, "cursor")
        check.opt_int_param(limit, "limit")

        if not filters:
            return self._slice(list(self._runs.values())[::-1], cursor, limit)

        def run_filter(run):
            if filters.run_ids and run.run_id not in filters.run_ids:
                return False

            if filters.statuses and run.status not in filters.statuses:
                return False

            if filters.pipeline_name and filters.pipeline_name != run.pipeline_name:
                return False

            if filters.tags and not all(
                run.tags.get(key) == value for key, value in filters.tags.items()
            ):
                return False

            if filters.snapshot_id and filters.snapshot_id != run.pipeline_snapshot_id:
                return False

            return True

        matching_runs = list(filter(run_filter, reversed(self._runs.values())))
        return self._slice(matching_runs, cursor=cursor, limit=limit)

    def get_runs_count(self, filters=None):
        check.opt_inst_param(filters, "filters", PipelineRunsFilter)

        return len(self.get_runs(filters))

    def _slice(self, runs, cursor, limit):
        if cursor:
            try:
                index = next(i for i, run in enumerate(runs) if run.run_id == cursor)
            except StopIteration:
                return []
            start = index + 1
        else:
            start = 0

        if limit:
            end = start + limit
        else:
            end = None

        return list(runs)[start:end]

    def get_run_by_id(self, run_id):
        check.str_param(run_id, "run_id")
        return self._runs.get(run_id)

    def get_run_tags(self):
        all_tags = defaultdict(set)
        for _run_id, tags in self._run_tags.items():
            for k, v in tags.items():
                all_tags[k].add(v)

        return sorted([(k, v) for k, v in all_tags.items()], key=lambda x: x[0])

    def add_run_tags(self, run_id, new_tags):
        check.str_param(run_id, "run_id")
        check.dict_param(new_tags, "new_tags", key_type=str, value_type=str)
        run = self._runs[run_id]
        run_tags = merge_dicts(run.tags if run.tags else {}, new_tags)
        self._runs[run_id] = run.with_tags(run_tags)
        self._run_tags[run_id] = frozendict(run_tags)

    def has_run(self, run_id):
        check.str_param(run_id, "run_id")
        return run_id in self._runs

    def delete_run(self, run_id):
        check.str_param(run_id, "run_id")
        del self._runs[run_id]
        if run_id in self._run_tags:
            del self._run_tags[run_id]

    def has_pipeline_snapshot(self, pipeline_snapshot_id):
        check.str_param(pipeline_snapshot_id, "pipeline_snapshot_id")
        return pipeline_snapshot_id in self._pipeline_snapshots

    def add_pipeline_snapshot(self, pipeline_snapshot):
        check.inst_param(pipeline_snapshot, "pipeline_snapshot", PipelineSnapshot)
        pipeline_snapshot_id = create_pipeline_snapshot_id(pipeline_snapshot)
        self._pipeline_snapshots[pipeline_snapshot_id] = pipeline_snapshot
        return pipeline_snapshot_id

    def get_pipeline_snapshot(self, pipeline_snapshot_id):
        check.str_param(pipeline_snapshot_id, "pipeline_snapshot_id")
        return self._pipeline_snapshots[pipeline_snapshot_id]

    def has_execution_plan_snapshot(self, execution_plan_snapshot_id):
        check.str_param(execution_plan_snapshot_id, "execution_plan_snapshot_id")
        return execution_plan_snapshot_id in self._ep_snapshots

    def add_execution_plan_snapshot(self, execution_plan_snapshot):
        check.inst_param(execution_plan_snapshot, "execution_plan_snapshot", ExecutionPlanSnapshot)
        execution_plan_snapshot_id = create_execution_plan_snapshot_id(execution_plan_snapshot)
        self._ep_snapshots[execution_plan_snapshot_id] = execution_plan_snapshot
        return execution_plan_snapshot_id

    def get_execution_plan_snapshot(self, execution_plan_snapshot_id):
        check.str_param(execution_plan_snapshot_id, "execution_plan_snapshot_id")
        return self._ep_snapshots[execution_plan_snapshot_id]

    def wipe(self):
        self._init_storage()

    def build_missing_indexes(self, print_fn=lambda _: None, force_rebuild_all=False):
        pass

    def get_run_group(self, run_id):
        check.str_param(run_id, "run_id")
        pipeline_run = self._runs.get(run_id)
        if not pipeline_run:
            return None
        # if the run doesn't have root_run_id, itself is the root
        root_run = (
            self.get_run_by_id(pipeline_run.root_run_id)
            if pipeline_run.root_run_id
            else pipeline_run
        )
        run_group = [root_run]
        for curr_run in self._runs.values():
            if curr_run.root_run_id == root_run.run_id:
                run_group.append(curr_run)
        return (root_run.root_run_id, run_group)

    def get_run_groups(self, filters=None, cursor=None, limit=None):
        runs = self.get_runs(filters=filters, cursor=cursor, limit=limit)
        run_groups = defaultdict(lambda: {"runs": {}, "count": 0})

        for run in runs:
            root_run_id = run.get_root_run_id()
            if root_run_id is not None:
                run_groups[root_run_id]["runs"][run.run_id] = run
            else:
                run_groups[run.run_id]["runs"][run.run_id] = run

        for root_run_id in run_groups:
            if root_run_id not in run_groups[root_run_id]["runs"]:
                run_groups[root_run_id]["runs"][root_run_id] = self.get_run_by_id(root_run_id)
            run_groups[root_run_id]["runs"] = list(run_groups[root_run_id]["runs"].values())

        for run in self.get_runs():
            root_run_id = run.get_root_run_id() or run.run_id
            if root_run_id in run_groups:
                run_groups[root_run_id]["count"] += 1

        return run_groups

    # Daemon Heartbeats

    def add_daemon_heartbeat(self, daemon_heartbeat):
        raise NotImplementedError(
            "The dagster daemon lives in a separate process. It cannot use in memory storage."
        )

    def get_daemon_heartbeats(self):
        raise NotImplementedError(
            "The dagster daemon lives in a separate process. It cannot use in memory storage."
        )

    def wipe_daemon_heartbeats(self):
        raise NotImplementedError(
            "The dagster daemon lives in a separate process. It cannot use in memory storage."
        )
