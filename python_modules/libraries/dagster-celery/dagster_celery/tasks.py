from celery import Celery
from celery.utils.collections import force_mapping
from dagster_celery.config import CeleryConfig
from kombu import Queue

from dagster import DagsterInstance, EventMetadataEntry, ExecutionTargetHandle, check
from dagster.core.events import EngineEventData
from dagster.core.execution.api import create_execution_plan, execute_plan_iterator
from dagster.core.execution.retries import Retries
from dagster.core.instance import InstanceRef
from dagster.core.serdes import serialize_dagster_namedtuple
from dagster.seven import is_module_available

from .engine import DELEGATE_MARKER, CeleryEngine


def create_task(celery_app, **task_kwargs):
    @celery_app.task(bind=True, name='execute_plan', **task_kwargs)
    def _execute_plan(_self, instance_ref_dict, handle_dict, run_id, step_keys, retries_dict):
        check.dict_param(instance_ref_dict, 'instance_ref_dict')
        check.dict_param(handle_dict, 'handle_dict')
        check.str_param(run_id, 'run_id')
        check.list_param(step_keys, 'step_keys', of_type=str)
        check.dict_param(retries_dict, 'retries_dict')

        instance_ref = InstanceRef.from_dict(instance_ref_dict)
        instance = DagsterInstance.from_ref(instance_ref)
        handle = ExecutionTargetHandle.from_dict(handle_dict)
        retries = Retries.from_config(retries_dict)

        pipeline_run = instance.get_run_by_id(run_id)
        check.invariant(pipeline_run, 'Could not load run {}'.format(run_id))

        pipeline_def = handle.get_pipeline_for_run(pipeline_run)

        step_keys_str = ", ".join(step_keys)

        engine_event = instance.report_engine_event(
            CeleryEngine,
            'Executing steps {} in celery worker'.format(step_keys_str),
            pipeline_run,
            EngineEventData(
                [EventMetadataEntry.text(step_keys_str, 'step_keys'),], marker_end=DELEGATE_MARKER,
            ),
        )

        execution_plan = create_execution_plan(
            pipeline_def, pipeline_run.environment_dict, pipeline_run
        ).build_subset_plan(step_keys)

        events = [engine_event]
        for step_event in execute_plan_iterator(
            execution_plan,
            pipeline_run=pipeline_run,
            environment_dict=pipeline_run.environment_dict,
            instance=instance,
            retries=retries,
        ):
            events.append(step_event)

        serialized_events = [serialize_dagster_namedtuple(event) for event in events]
        return serialized_events

    return _execute_plan


def make_app(config=None):
    config = check.opt_inst_param(config, 'config', CeleryConfig)
    app_ = Celery('dagster', **(config._asdict() if config is not None else {}))
    if config is None:
        app_.config_from_object('dagster_celery.defaults', force=True)

        if is_module_available('dagster_celery_config'):
            # pylint: disable=protected-access
            obj = force_mapping(app_.loader._smart_import('dagster_celery_config'))
            app_.conf.update(obj)

    app_.loader.import_module('celery.contrib.testing.tasks')

    app_.conf.task_queues = [
        Queue('dagster', routing_key='dagster.#', queue_arguments={'x-max-priority': 10})
    ]
    app_.conf.task_routes = {
        'execute_plan': {'queue': 'dagster', 'routing_key': 'dagster.execute_plan'}
    }
    app_.conf.task_queue_max_priority = 10
    app_.conf.task_default_priority = 5
    return app_


app = make_app()

execute_plan = create_task(app)
