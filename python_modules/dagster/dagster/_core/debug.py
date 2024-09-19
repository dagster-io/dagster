from typing import NamedTuple, Sequence

import dagster._check as check
from dagster._core.events.log import EventLogEntry
from dagster._core.instance import DagsterInstance
from dagster._core.snap import ExecutionPlanSnapshot, JobSnapshot
from dagster._core.storage.dagster_run import DagsterRun
from dagster._serdes import serialize_value, whitelist_for_serdes


@whitelist_for_serdes(
    storage_field_names={
        "dagster_run": "pipeline_run",
        "job_snapshot": "pipeline_snapshot",
    }
)
class DebugRunPayload(
    NamedTuple(
        "_DebugRunPayload",
        [
            ("version", str),
            ("dagster_run", DagsterRun),
            ("event_list", Sequence[EventLogEntry]),
            ("job_snapshot", JobSnapshot),
            ("execution_plan_snapshot", ExecutionPlanSnapshot),
        ],
    )
):
    def __new__(
        cls,
        version: str,
        dagster_run: DagsterRun,
        event_list: Sequence[EventLogEntry],
        job_snapshot: JobSnapshot,
        execution_plan_snapshot: ExecutionPlanSnapshot,
    ):
        return super(DebugRunPayload, cls).__new__(
            cls,
            version=check.str_param(version, "version"),
            dagster_run=check.inst_param(dagster_run, "dagster_run", DagsterRun),
            event_list=check.sequence_param(event_list, "event_list", EventLogEntry),
            job_snapshot=check.inst_param(job_snapshot, "job_snapshot", JobSnapshot),
            execution_plan_snapshot=check.inst_param(
                execution_plan_snapshot, "execution_plan_snapshot", ExecutionPlanSnapshot
            ),
        )

    @classmethod
    def build(cls, instance: DagsterInstance, run: DagsterRun) -> "DebugRunPayload":
        from dagster import __version__ as dagster_version

        return cls(
            version=dagster_version,
            dagster_run=run,
            event_list=instance.all_logs(run.run_id),
            job_snapshot=instance.get_job_snapshot(run.job_snapshot_id),  # type: ignore  # (possible none)
            execution_plan_snapshot=instance.get_execution_plan_snapshot(
                run.execution_plan_snapshot_id  # type: ignore  # (possible none)
            ),
        )

    def write(self, output_file):
        return output_file.write(serialize_value(self).encode("utf-8"))
