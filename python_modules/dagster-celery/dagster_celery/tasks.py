from celery import Celery
from celery.utils.collections import force_mapping
from dagster_celery.config import CeleryConfig
from dagster_graphql.client.mutations import execute_execute_plan_mutation
from kombu import Queue

from dagster import ExecutionTargetHandle, check
from dagster.core.instance import InstanceRef
from dagster.core.serdes import serialize_dagster_namedtuple
from dagster.seven import is_module_available


def create_task(celery_app, **task_kwargs):
    @celery_app.task(bind=True, name='execute_query', **task_kwargs)
    def _execute_query(_self, handle_dict, variables, instance_ref_dict):
        instance_ref = InstanceRef.from_dict(instance_ref_dict)
        handle = ExecutionTargetHandle.from_dict(handle_dict)

        events = execute_execute_plan_mutation(
            handle=handle, variables=variables, instance_ref=instance_ref,
        )
        serialized_events = [serialize_dagster_namedtuple(event) for event in events]
        return serialized_events

    return _execute_query


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
        'execute_query': {'queue': 'dagster', 'routing_key': 'dagster.execute_query'}
    }
    app_.conf.task_queue_max_priority = 10
    app_.conf.task_default_priority = 5
    return app_


app = make_app()

execute_query = create_task(app)
