from dagster import (
    DagsterInstance,
    MetadataEntry,
    _check as check,
)
from dagster._core.definitions.reconstruct import ReconstructablePipeline
from dagster._core.events import EngineEventData
from dagster._core.execution.api import create_execution_plan, execute_plan_iterator
from dagster._grpc.types import ExecuteStepArgs
from dagster._serdes import serialize_dagster_namedtuple, unpack_value

from .core_execution_loop import DELEGATE_MARKER
from .executor import CeleryExecutor


def create_task(celery_app, **task_kwargs):
    @celery_app.task(bind=True, name="execute_plan", **task_kwargs)
    def _execute_plan(self, execute_step_args_packed, executable_dict):
        execute_step_args = unpack_value(
            check.dict_param(
                execute_step_args_packed,
                "execute_step_args_packed",
            )
        )
        check.inst_param(execute_step_args, "execute_step_args", ExecuteStepArgs)

        check.dict_param(executable_dict, "executable_dict")

        instance = DagsterInstance.from_ref(execute_step_args.instance_ref)

        pipeline = ReconstructablePipeline.from_dict(executable_dict)
        retry_mode = execute_step_args.retry_mode

        pipeline_run = instance.get_run_by_id(execute_step_args.pipeline_run_id)
        check.invariant(
            pipeline_run, "Could not load run {}".format(execute_step_args.pipeline_run_id)
        )

        step_keys_str = ", ".join(execute_step_args.step_keys_to_execute)

        execution_plan = create_execution_plan(
            pipeline,
            pipeline_run.run_config,
            mode=pipeline_run.mode,
            step_keys_to_execute=execute_step_args.step_keys_to_execute,
            known_state=execute_step_args.known_state,
        )

        engine_event = instance.report_engine_event(
            "Executing steps {} in celery worker".format(step_keys_str),
            pipeline_run,
            EngineEventData(
                [
                    MetadataEntry("step_keys", value=step_keys_str),
                    MetadataEntry("Celery worker", value=self.request.hostname),
                ],
                marker_end=DELEGATE_MARKER,
            ),
            CeleryExecutor,
            step_key=execution_plan.step_handle_for_single_step_plans().to_key(),
        )

        events = [engine_event]
        for step_event in execute_plan_iterator(
            execution_plan=execution_plan,
            pipeline=pipeline,
            pipeline_run=pipeline_run,
            instance=instance,
            retry_mode=retry_mode,
            run_config=pipeline_run.run_config,
        ):
            events.append(step_event)

        serialized_events = [serialize_dagster_namedtuple(event) for event in events]
        return serialized_events

    return _execute_plan
