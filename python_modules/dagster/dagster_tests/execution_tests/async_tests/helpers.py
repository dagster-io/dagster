from contextlib import AbstractContextManager
from typing import Protocol

import dagster as dg
from dagster import DagsterRun, StepExecutionContext
from dagster._core.execution.api import create_execution_plan
from dagster._core.execution.plan.plan import ExecutionPlan
from dagster._core.utils import make_new_run_id


class StepContextFactory(Protocol):
    def __call__(
        self,
        job_def: dg.JobDefinition,
        step_key: str | None = None,
        run_config: dict[str, object] | None = None,
    ) -> AbstractContextManager[StepExecutionContext]: ...


def _create_plan_and_run(
    job_def: dg.JobDefinition, run_config: dict[str, object] | None = None
) -> tuple[ExecutionPlan, DagsterRun, dict[str, object]]:
    resolved_run_config: dict[str, object] = dict(run_config or {})
    plan = create_execution_plan(job=job_def, run_config=resolved_run_config)
    dagster_run = DagsterRun(
        job_name=job_def.name,
        run_config=resolved_run_config,
        run_id=make_new_run_id(),
    )
    return plan, dagster_run, resolved_run_config
