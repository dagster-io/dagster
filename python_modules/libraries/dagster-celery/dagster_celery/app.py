# The celery CLI points to a module (via the -A argument)
# to find tasks. This file exists to be a target for that argument.
# Examples:
#   - See `worker_start_command` in dagster_celery.cli
#   - deployment-flower.yaml helm chart
from dagster_celery.make_app import make_app
from dagster_celery.tasks import create_execute_job_task, create_resume_job_task, create_task

app = make_app()

execute_plan = create_task(app)

execute_job = create_execute_job_task(app)

resume_job = create_resume_job_task(app)
