# The celery CLI points to a module (via the -A argument)
# to find tasks. This file exists to be a target for that argument.
# Examples:
#   - See `worker_start_command` in dagster_celery.cli
#   - deployment-flower.yaml helm chart
from .docker_task import create_docker_task
from .k8s_job_task import create_k8s_job_task
from .make_app import make_app
from .tasks import create_task

app = make_app()

execute_plan = create_task(app)
execute_step_k8s_job = create_k8s_job_task(app)
execute_step_docker = create_docker_task(app)
