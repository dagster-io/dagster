import dagster._check as check
from dagster_aws.ecs import EcsRunLauncher

from dagster_cloud.instance import DagsterCloudAgentInstance
from dagster_cloud.workspace.ecs.utils import get_run_task_definition_family


class CloudEcsRunLauncher(EcsRunLauncher[DagsterCloudAgentInstance]):
    def _get_run_task_definition_family(self, run) -> str:
        return get_run_task_definition_family(
            self._task_definition_prefix,
            self._instance.organization_name,
            check.not_none(self._instance.deployment_name),
            check.not_none(run.remote_job_origin),
        )
