from typing import TYPE_CHECKING, Iterable, Mapping, Optional, Sequence

from dagster._annotations import public
from dagster._core.definitions.events import AssetKey
from dagster._core.storage.pipeline_run import DagsterRun

if TYPE_CHECKING:
    from dagster._core.event_api import EventLogRecord, EventRecordsFilter
    from dagster._core.events import DagsterEventType
    from dagster._core.events.log import EventLogEntry
    from dagster._core.execution.stats import RunStepKeyStatsSnapshot
    from dagster._core.instance import DagsterInstance
    from dagster._core.snap.execution_plan_snapshot import ExecutionPlanSnapshot
    from dagster._core.storage.pipeline_run import PipelineRunStatsSnapshot


class InstanceInterfaceInStepWorker:
    # Event-log-related

    def __init__(self, instance: "DagsterInstance"):
        self._instance = instance

    def get_inner_instance_for_framework(self):
        return self._instance

    def storage_directory(self):
        return self._instance.storage_directory()

    def get_ref(self):
        return self._instance.get_ref()

    def get_execution_plan_snapshot(self, snapshot_id: str) -> "ExecutionPlanSnapshot":
        return self._instance.get_execution_plan_snapshot(snapshot_id)

    def get_latest_logical_version_record(
        self,
        key: AssetKey,
        is_source: Optional[bool] = None,
    ) -> Optional["EventLogRecord"]:
        return self._instance.get_latest_logical_version_record(key, is_source)

    @property
    def is_ephemeral(self):
        return self._instance.is_ephemeral

    @property
    def is_persistent(self):
        return self._instance.is_persistent

    @property
    def python_log_level(self):
        return self._instance.python_log_level

    def get_handlers(self):
        return self._instance.get_handlers()

    @property
    def managed_python_loggers(self):
        return self._instance.managed_python_loggers

    @property
    def run_monitoring_enabled(self):
        return self._instance.run_monitoring_enabled

    # probably for test?
    def create_run_for_pipeline(self, *args, **kwargs):
        return self._instance.create_run_for_pipeline(*args, **kwargs)

    def run_will_resume(self, *args, **kwargs):
        return self._instance.run_will_resume(*args, **kwargs)

    def get_run_by_id(self, run_id: str) -> Optional[DagsterRun]:
        return self._instance.get_run_by_id(run_id)

    def get_run_stats(self, run_id: str) -> "PipelineRunStatsSnapshot":
        return self._instance.get_run_stats(run_id)

    def get_run_step_stats(
        self, run_id: str, step_keys: Optional[Sequence[str]] = None
    ) -> Sequence["RunStepKeyStatsSnapshot"]:
        return self._instance.get_run_step_stats(run_id, step_keys)

    def logs_after(
        self,
        run_id: str,
        cursor: Optional[int] = None,
        of_type: Optional["DagsterEventType"] = None,
        limit: Optional[int] = None,
    ):
        return self._instance.logs_after(run_id=run_id, cursor=cursor, of_type=of_type, limit=limit)

    @public
    def get_latest_materialization_events(
        self, asset_keys: Sequence[AssetKey]
    ) -> Mapping[AssetKey, Optional["EventLogEntry"]]:
        return self._instance.get_latest_materialization_events(asset_keys)

    @public
    def get_latest_materialization_event(self, asset_key: AssetKey) -> Optional["EventLogEntry"]:
        return self._instance.get_latest_materialization_event(asset_key)

    @public
    def get_event_records(
        self,
        event_records_filter: "EventRecordsFilter",
        limit: Optional[int] = None,
        ascending: bool = False,
    ) -> Iterable["EventLogRecord"]:
        return self._instance.get_event_records(
            event_records_filter=event_records_filter, limit=limit, ascending=ascending
        )

    def handle_new_event(self, *args, **kwargs):
        return self._instance.handle_new_event(*args, **kwargs)

    def report_engine_event(
        self,
        message,
        pipeline_run=None,
        engine_event_data=None,
        cls=None,
        step_key=None,
        pipeline_name=None,
        run_id=None,
    ):
        return self._instance.report_engine_event(
            message=message,
            pipeline_run=pipeline_run,
            engine_event_data=engine_event_data,
            cls=cls,
            step_key=step_key,
            pipeline_name=pipeline_name,
            run_id=run_id,
        )

    def report_run_canceling(
        self,
        pipeline_run,
        message=None,
    ):
        return self._instance.report_run_canceled(pipeline_run, message)

    def report_run_canceled(
        self,
        pipeline_run,
        message=None,
    ):
        return self._instance.report_run_canceled(pipeline_run, message)

    def report_run_failed(
        self,
        pipeline_run,
        message=None,
    ):
        return self._instance.report_run_failed(pipeline_run, message)


# class GraphQLBackedInstance(UserProcessInstance):
#     def __init__(self, event_storage: )

#     def get_run_stats(self, run_id: str) -> PipelineRunStatsSnapshot:
#         return self._event_storage.get_stats_for_run(run_id)
