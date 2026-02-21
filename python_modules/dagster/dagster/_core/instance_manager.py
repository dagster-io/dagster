import datetime
from contextlib import ExitStack
from typing import Optional

from dagster_shared import check

import dagster as dg
from dagster._core.definitions.asset_selection import CoercibleToAssetSelection
from dagster._core.definitions.assets.job.asset_job import IMPLICIT_ASSET_JOB_NAME
from dagster._core.definitions.job_base import InMemoryJob
from dagster._core.events import DagsterEvent, DagsterEventType
from dagster._core.execution.api import create_execution_plan, execute_plan_iterator
from dagster._core.execution.plan.active import ActiveExecution
from dagster._core.execution.plan.objects import ErrorSource, StepFailureData
from dagster._core.execution.plan.plan import ExecutionPlan
from dagster._core.execution.retries import RetryMode
from dagster._core.instance_for_test import instance_for_test
from dagster._core.snap.execution_plan_snapshot import snapshot_from_execution_plan
from dagster._core.storage.dagster_run import DagsterRunStatus
from dagster._core.test_utils import freeze_time
from dagster._core.utils import make_new_run_id


class InstanceManager:
    def __init__(self, defs: dg.Definitions, current_time: Optional[datetime.datetime] = None):
        self._defs = defs
        self._instance_cm = instance_for_test()
        self._current_time = current_time or datetime.datetime.now()
        self._exit_stack = ExitStack()

    def __enter__(self):
        self.instance = self._exit_stack.enter_context(self._instance_cm)
        self._exit_stack.enter_context(freeze_time(self._current_time))
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._exit_stack.close()

    def advance_time(self, **kwargs):
        self._current_time = self._current_time + datetime.timedelta(**kwargs)
        self._exit_stack.enter_context(freeze_time(self._current_time))

    @property
    def asset_graph(self):
        return self._defs.get_repository_def().asset_graph

    def create_asset_run(self, asset_selection: CoercibleToAssetSelection) -> "ManagedRun":
        run_id = make_new_run_id()

        asset_keys = dg.AssetSelection.from_coercible(asset_selection).resolve(self.asset_graph)
        job_def = self._defs.get_implicit_global_asset_job_def().get_subset(
            asset_selection=asset_keys
        )
        job_snapshot = job_def.get_job_snapshot()
        execution_plan = create_execution_plan(
            job=job_def,
            run_config={},
            instance_ref=self.instance.get_ref(),
        )

        dagster_run = self.instance.create_run(
            job_name=IMPLICIT_ASSET_JOB_NAME,
            run_id=run_id,
            status=DagsterRunStatus.NOT_STARTED,
            asset_selection=asset_keys,
            run_config={},
            tags={},
            root_run_id=None,
            parent_run_id=None,
            step_keys_to_execute=None,
            execution_plan_snapshot=snapshot_from_execution_plan(
                execution_plan, job_snapshot.snapshot_id
            ),
            job_snapshot=job_snapshot,
            parent_job_snapshot=None,
            asset_check_selection=None,
            resolved_op_selection=None,
            op_selection=None,
            remote_job_origin=None,
            job_code_origin=None,
            asset_graph=self.asset_graph,
        )
        return ManagedRun(job_def=job_def, dagster_run=dagster_run)

    def _get_updated_active_execution(
        self, execution_plan: ExecutionPlan, run: "ManagedRun"
    ) -> ActiveExecution:
        active_execution = ActiveExecution(
            execution_plan=execution_plan, retry_mode=RetryMode.ENABLED
        )
        active_execution._context_guard = True  # noqa
        run_events = [
            log.dagster_event
            for log in self.instance.event_log_storage.get_logs_for_run(run.dagster_run.run_id)
            if log.dagster_event
        ]
        active_execution.rebuild_from_events(run_events)
        return active_execution

    def _get_execution_plan(self, run: "ManagedRun") -> ExecutionPlan:
        execution_plan_snapshot = self.instance.get_execution_plan_snapshot(
            run.execution_plan_snapshot_id
        )
        return ExecutionPlan.rebuild_from_snapshot(
            run.dagster_run.job_name, execution_plan_snapshot
        )

    def execute_steps(self, run: "ManagedRun", step_keys: list[str]) -> None:
        if run.dagster_run.status == DagsterRunStatus.NOT_STARTED:
            launch_started_event = DagsterEvent(
                event_type_value=DagsterEventType.PIPELINE_START.value,
                job_name=run.dagster_run.job_name,
            )

            self.instance.report_dagster_event(launch_started_event, run_id=run.dagster_run.run_id)

        execution_plan = self._get_execution_plan(run)
        active_execution = self._get_updated_active_execution(execution_plan, run)

        sub_execution_plan = create_execution_plan(
            job=run.job_def,
            run_config=run.dagster_run.run_config,
            step_keys_to_execute=step_keys,
            known_state=active_execution.get_known_state(),
        )
        list(
            execute_plan_iterator(
                sub_execution_plan,
                InMemoryJob(run.job_def),
                run.dagster_run,
                instance=self.instance,
            )
        )

        if self._get_updated_active_execution(execution_plan, run).is_complete:
            self.instance.report_dagster_event(
                DagsterEvent(
                    event_type_value=DagsterEventType.PIPELINE_SUCCESS.value,
                    job_name=run.dagster_run.job_name,
                ),
                run_id=run.dagster_run.run_id,
            )

        # update the managed run with the current state
        run.dagster_run = check.not_none(self.instance.get_run_by_id(run.dagster_run.run_id))

    def fail_steps(self, run: "ManagedRun", step_keys: list[str]) -> None:
        for step_key in step_keys:
            self.instance.report_dagster_event(
                DagsterEvent(
                    event_type_value=DagsterEventType.STEP_FAILURE.value,
                    job_name=run.dagster_run.job_name,
                    event_specific_data=StepFailureData(
                        error_source=ErrorSource.USER_CODE_ERROR,
                        error=None,
                        user_failure_data=None,
                    ),
                    step_key=step_key,
                ),
                run_id=run.dagster_run.run_id,
            )

        self.instance.report_run_failed(dagster_run=run.dagster_run)
        run.dagster_run = check.not_none(self.instance.get_run_by_id(run.dagster_run.run_id))

    def _get_step_keys_for_assets(
        self, run: "ManagedRun", asset_selection: CoercibleToAssetSelection
    ) -> set[str]:
        asset_keys = dg.AssetSelection.from_coercible(asset_selection).resolve(self.asset_graph)
        step_keys = set()
        for step in self._get_execution_plan(run).steps:
            for output in step.step_outputs:
                if output.properties and output.properties.asset_key in asset_keys:
                    step_keys.add(step.key)
        return step_keys

    def execute_steps_for_assets(
        self, run: "ManagedRun", asset_selection: CoercibleToAssetSelection
    ) -> None:
        step_keys = self._get_step_keys_for_assets(run, asset_selection)
        self.execute_steps(run, list(step_keys))

    def fail_steps_for_assets(
        self, run: "ManagedRun", asset_selection: CoercibleToAssetSelection
    ) -> None:
        step_keys = self._get_step_keys_for_assets(run, asset_selection)
        self.fail_steps(run, list(step_keys))

    def start_run(self, run: "ManagedRun") -> None:
        self.instance.report_dagster_event(
            DagsterEvent(
                event_type_value=DagsterEventType.PIPELINE_START.value,
                job_name=run.dagster_run.job_name,
            ),
            run_id=run.dagster_run.run_id,
        )
        run.dagster_run = check.not_none(self.instance.get_run_by_id(run.dagster_run.run_id))


class ManagedRun:
    def __init__(self, job_def: dg.JobDefinition, dagster_run: dg.DagsterRun):
        self.job_def = job_def
        self.dagster_run = dagster_run

    @property
    def execution_plan_snapshot_id(self) -> str:
        return check.not_none(self.dagster_run.execution_plan_snapshot_id)
