from typing import NamedTuple, Sequence

import dagster._check as check
from dagster._core.events.log import EventLogEntry
from dagster._core.snap import ExecutionPlanSnapshot, PipelineSnapshot
from dagster._core.storage.pipeline_run import DagsterRun
from dagster._serdes import serialize_dagster_namedtuple, whitelist_for_serdes


@whitelist_for_serdes
class DebugRunPayload(
    NamedTuple(
        "_DebugRunPayload",
        [
            ("version", str),
            ("pipeline_run", DagsterRun),
            ("event_list", Sequence[EventLogEntry]),
            ("pipeline_snapshot", PipelineSnapshot),
            ("execution_plan_snapshot", ExecutionPlanSnapshot),
        ],
    )
):
    def __new__(
        cls,
        version: str,
        pipeline_run: DagsterRun,
        event_list: Sequence[EventLogEntry],
        pipeline_snapshot: PipelineSnapshot,
        execution_plan_snapshot: ExecutionPlanSnapshot,
    ):
        return super(DebugRunPayload, cls).__new__(
            cls,
            version=check.str_param(version, "version"),
            pipeline_run=check.inst_param(pipeline_run, "pipeline_run", DagsterRun),
            event_list=check.sequence_param(event_list, "event_list", EventLogEntry),
            pipeline_snapshot=check.inst_param(
                pipeline_snapshot, "pipeline_snapshot", PipelineSnapshot
            ),
            execution_plan_snapshot=check.inst_param(
                execution_plan_snapshot, "execution_plan_snapshot", ExecutionPlanSnapshot
            ),
        )

    @classmethod
    def build(cls, instance, run):
        from dagster import __version__ as dagster_version

        return cls(
            version=dagster_version,
            pipeline_run=run,
            event_list=instance.all_logs(run.run_id),
            pipeline_snapshot=instance.get_pipeline_snapshot(run.pipeline_snapshot_id),
            execution_plan_snapshot=instance.get_execution_plan_snapshot(
                run.execution_plan_snapshot_id
            ),
        )

    def write(self, output_file):
        return output_file.write(serialize_dagster_namedtuple(self).encode("utf-8"))
