import os

from celery import Celery
from dagster_graphql.client.mutations import execute_execute_plan_mutation

from dagster import ExecutionTargetHandle
from dagster.core.instance import InstanceRef
from dagster.core.serdes import serialize_dagster_namedtuple

from .config import CeleryConfig

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
    return app_


app = make_app()

execute_query = create_task(app)

if __name__ == '__main__':
    app.worker_main()
