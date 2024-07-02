# The celery CLI points to a module (via the -A argument)
# to find tasks. This file exists to be a target for that argument.
# Examples:
#   - See `worker_start_command` in dagster_celery.cli
#   - deployment-flower.yaml helm chart
from .tasks import create_task
from .make_app import make_app

app = make_app()

execute_plan = create_task(app)
