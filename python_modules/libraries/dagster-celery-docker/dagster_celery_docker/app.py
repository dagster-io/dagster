from dagster_celery.make_app import make_app_with_task_routes

from .executor import create_docker_task

app = make_app_with_task_routes(
    task_routes={
        "execute_step_docker": {"queue": "dagster", "routing_key": "dagster.execute_step_docker",},
    }
)


execute_step_docker = create_docker_task(app)
