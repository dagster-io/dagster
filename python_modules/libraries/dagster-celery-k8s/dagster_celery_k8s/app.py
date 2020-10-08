from dagster_celery.make_app import make_app_with_task_routes

from .executor import create_k8s_job_task

app = make_app_with_task_routes(
    task_routes={
        "execute_step_k8s_job": {
            "queue": "dagster",
            "routing_key": "dagster.execute_step_k8s_job",
        },
    }
)


execute_step_k8s_job = create_k8s_job_task(app)
