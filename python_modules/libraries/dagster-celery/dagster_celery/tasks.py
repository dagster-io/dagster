from dagster import DagsterInstance, EventMetadataEntry, check
from dagster.core.definitions.reconstructable import ReconstructablePipeline
from dagster.core.events import EngineEventData
from dagster.core.execution.api import create_execution_plan, execute_plan_iterator
from dagster.core.execution.retries import Retries
from dagster.core.instance import InstanceRef
from dagster.serdes import serialize_dagster_namedtuple

from .core_execution_loop import DELEGATE_MARKER
from .executor import CeleryExecutor


def create_task(celery_app, **task_kwargs):
    @celery_app.task(bind=True, name="execute_plan", **task_kwargs)
    def _execute_plan(_self, instance_ref_dict, executable_dict, run_id, step_keys, retries_dict):
        check.dict_param(instance_ref_dict, "instance_ref_dict")
        check.dict_param(executable_dict, "executable_dict")
        check.str_param(run_id, "run_id")
        check.list_param(step_keys, "step_keys", of_type=str)
        check.dict_param(retries_dict, "retries_dict")

        instance_ref = InstanceRef.from_dict(instance_ref_dict)
        instance = DagsterInstance.from_ref(instance_ref)
        pipeline = ReconstructablePipeline.from_dict(executable_dict)
        retries = Retries.from_config(retries_dict)

        pipeline_run = instance.get_run_by_id(run_id)
        check.invariant(pipeline_run, "Could not load run {}".format(run_id))

        step_keys_str = ", ".join(step_keys)

        execution_plan = create_execution_plan(
            pipeline,
            pipeline_run.run_config,
            mode=pipeline_run.mode,
            step_keys_to_execute=pipeline_run.step_keys_to_execute,
        ).build_subset_plan(step_keys)

        engine_event = instance.report_engine_event(
            "Executing steps {} in celery worker".format(step_keys_str),
            pipeline_run,
            EngineEventData(
                [EventMetadataEntry.text(step_keys_str, "step_keys"),], marker_end=DELEGATE_MARKER,
            ),
            CeleryExecutor,
            step_key=execution_plan.step_key_for_single_step_plans(),
        )

        events = [engine_event]
        for step_event in execute_plan_iterator(
            execution_plan,
            pipeline_run=pipeline_run,
            run_config=pipeline_run.run_config,
            instance=instance,
            retries=retries,
        ):
            events.append(step_event)

        serialized_events = [serialize_dagster_namedtuple(event) for event in events]
        return serialized_events

    return _execute_plan
