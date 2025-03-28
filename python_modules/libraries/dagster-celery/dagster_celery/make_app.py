from typing import Optional

from celery import Celery
from celery.utils.collections import force_mapping
from dagster import Any
from dagster_shared.seven import is_module_available
from kombu import Queue

from dagster_celery.config import (
    TASK_EXECUTE_JOB_NAME,
    TASK_EXECUTE_PLAN_NAME,
    TASK_RESUME_JOB_NAME,
)


def make_app(app_args=None):
    return make_app_with_task_routes(
        app_args=app_args,
        task_routes={
            TASK_EXECUTE_PLAN_NAME: {
                "queue": "dagster",
                "routing_key": f"dagster.{TASK_EXECUTE_PLAN_NAME}",
            },
            TASK_EXECUTE_JOB_NAME: {
                "queue": "dagster",
                "routing_key": f"dagster.{TASK_EXECUTE_JOB_NAME}",
            },
            TASK_RESUME_JOB_NAME: {
                "queue": "dagster",
                "routing_key": f"dagster.{TASK_RESUME_JOB_NAME}",
            },
        },
    )


def make_app_with_task_routes(
    task_routes: dict,
    app_args: Optional[dict[str, Any]] = None,
):
    app_ = Celery("dagster", **(app_args if app_args else {}))

    if app_args is None:
        app_.config_from_object("dagster_celery.defaults", force=True)

        if is_module_available("dagster_celery_config"):
            obj = force_mapping(app_.loader._smart_import("dagster_celery_config"))  # noqa: SLF001
            app_.conf.update(obj)

    app_.loader.import_module("celery.contrib.testing.tasks")

    app_.conf.task_queues = [
        Queue("dagster", routing_key="dagster.#", queue_arguments={"x-max-priority": 10})
    ]
    app_.conf.task_routes = task_routes
    app_.conf.task_queue_max_priority = 10
    app_.conf.task_default_priority = 5
    return app_
