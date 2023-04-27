from dagster import (
    DagsterInstance,
    _check as check,
)
from dagster._core.definitions.reconstruct import ReconstructableJob
from dagster._core.events import EngineEventData
from dagster._core.execution.api import create_execution_plan, execute_plan_iterator
from dagster._grpc.types import ExecuteStepArgs
from dagster._serdes import serialize_value, unpack_value

from .core_execution_loop import DELEGATE_MARKER
from .executor import CeleryExecutor


def create_task(celery_app, **task_kwargs):
    @celery_app.task(bind=True, name="execute_plan", **task_kwargs)
    def _execute_plan(self, execute_step_args_packed, executable_dict):
        execute_step_args = unpack_value(
            check.dict_param(
                execute_step_args_packed,
                "execute_step_args_packed",
            ),
            as_type=ExecuteStepArgs,
        )

        check.dict_param(executable_dict, "executable_dict")

        instance = DagsterInstance.from_ref(execute_step_args.instance_ref)

        recon_job = ReconstructableJob.from_dict(executable_dict)
        retry_mode = execute_step_args.retry_mode

        dagster_run = instance.get_run_by_id(execute_step_args.run_id)
        check.invariant(dagster_run, f"Could not load run {execute_step_args.run_id}")

        step_keys_str = ", ".join(execute_step_args.step_keys_to_execute)

        execution_plan = create_execution_plan(
            recon_job,
            dagster_run.run_config,
            step_keys_to_execute=execute_step_args.step_keys_to_execute,
            known_state=execute_step_args.known_state,
        )

        engine_event = instance.report_engine_event(
            f"Executing steps {step_keys_str} in celery worker",
            dagster_run,
            EngineEventData(
                {
                    "step_keys": step_keys_str,
                    "Celery worker": self.request.hostname,
                },
                marker_end=DELEGATE_MARKER,
            ),
            CeleryExecutor,
            step_key=execution_plan.step_handle_for_single_step_plans().to_key(),
        )

        events = [engine_event]
        for step_event in execute_plan_iterator(
            execution_plan=execution_plan,
            job=recon_job,
            dagster_run=dagster_run,
            instance=instance,
            retry_mode=retry_mode,
            run_config=dagster_run.run_config,
        ):
            events.append(step_event)

        serialized_events = [serialize_value(event) for event in events]
        return serialized_events

    return _execute_plan
