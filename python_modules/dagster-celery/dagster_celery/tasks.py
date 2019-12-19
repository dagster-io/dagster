import os

from celery import Celery
from dagster_celery.config import CeleryConfig
from dagster_graphql.client.mutations import execute_execute_plan_mutation
from kombu import Queue

from dagster import ExecutionTargetHandle
from dagster.core.instance import InstanceRef
from dagster.core.serdes import serialize_dagster_namedtuple

DEFAULT_BROKER = 'pyamqp://guest@{hostname}:5672//'.format(
    hostname=os.getenv('DAGSTER_CELERY_BROKER_HOST', 'localhost')
)


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


def make_app(config=CeleryConfig()):
    app_ = Celery('dagster', **dict({'broker': DEFAULT_BROKER}, **(config._asdict())))
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

if __name__ == '__main__':
    app.worker_main()
