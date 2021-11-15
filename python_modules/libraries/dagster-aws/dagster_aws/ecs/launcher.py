import boto3
import dagster
from botocore.exceptions import ClientError
from dagster import Field, check
from dagster.core.launcher.base import LaunchRunContext, RunLauncher
from dagster.grpc.types import ExecuteRunArgs
from dagster.serdes import ConfigurableClass
from dagster.utils.backcompat import experimental

from .tasks import default_ecs_task_definition, default_ecs_task_metadata


@experimental
class EcsRunLauncher(RunLauncher, ConfigurableClass):
    def __init__(self, inst_data=None, task_definition=None, container_name="run"):
        self._inst_data = inst_data
        self.ecs = boto3.client("ecs")
        self.ec2 = boto3.resource("ec2")

        self.task_definition = task_definition
        self.container_name = container_name

        if self.task_definition:
            task_definition = self.ecs.describe_task_definition(taskDefinition=task_definition)
            container_names = [
                container.get("name")
                for container in task_definition["taskDefinition"]["containerDefinitions"]
            ]
            check.invariant(
                container_name in container_names,
                f"Cannot override container '{container_name}' in task definition "
                f"'{self.task_definition}' because the container is not defined.",
            )
            self.task_definition = task_definition["taskDefinition"]["taskDefinitionArn"]

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {
            "task_definition": Field(
                dagster.String,
                is_required=False,
                description=(
                    "The task definition to use when launching new tasks. "
                    "If none is provided, each run will create its own task "
                    "definition."
                ),
            ),
            "container_name": Field(
                dagster.String,
                is_required=False,
                default_value="run",
                description=(
                    "The container name to use when launching new tasks. Defaults to 'run'."
                ),
            ),
        }

    @staticmethod
    def from_config_value(inst_data, config_value):
        return EcsRunLauncher(inst_data=inst_data, **config_value)

    def _set_ecs_tags(self, run_id, task_arn):
        try:
            tags = [{"key": "dagster/run_id", "value": run_id}]
            self.ecs.tag_resource(resourceArn=task_arn, tags=tags)
        except ClientError:
            pass

    def _set_run_tags(self, run_id, task_arn):
        cluster = self._task_metadata().cluster
        tags = {"ecs/task_arn": task_arn, "ecs/cluster": cluster}
        self._instance.add_run_tags(run_id, tags)

    def _get_run_tags(self, run_id):
        run = self._instance.get_run_by_id(run_id)
        tags = run.tags if run else {}
        arn = tags.get("ecs/task_arn")
        cluster = tags.get("ecs/cluster")

        return (arn, cluster)

    def launch_run(self, context: LaunchRunContext) -> None:

        """
        Launch a run in an ECS task.

        Currently, Fargate is the only supported launchType and awsvpc is the
        only supported networkMode. These are the defaults that are set up by
        docker-compose when you use the Dagster ECS reference deployment.
        """
        run = context.pipeline_run
        metadata = self._task_metadata()
        pipeline_origin = context.pipeline_code_origin
        image = pipeline_origin.repository_origin.container_image
        task_definition = self._task_definition(metadata, image)["family"]

        args = ExecuteRunArgs(
            pipeline_origin=pipeline_origin,
            pipeline_run_id=run.run_id,
            instance_ref=self._instance.get_ref(),
        )
        command = args.get_command_args()
        # Run a task using the same network configuration as this processes's
        # task.

        response = self.ecs.run_task(
            taskDefinition=task_definition,
            cluster=metadata.cluster,
            overrides={"containerOverrides": [{"name": self.container_name, "command": command}]},
            networkConfiguration={
                "awsvpcConfiguration": {
                    "subnets": metadata.subnets,
                    "assignPublicIp": "ENABLED",
                    "securityGroups": metadata.security_groups,
                }
            },
            launchType="FARGATE",
        )

        arn = response["tasks"][0]["taskArn"]
        self._set_run_tags(run.run_id, task_arn=arn)
        self._set_ecs_tags(run.run_id, task_arn=arn)
        self._instance.report_engine_event(
            message=f"Launching run in task {arn} on cluster {metadata.cluster}",
            pipeline_run=run,
            cls=self.__class__,
        )

    def can_terminate(self, run_id):
        arn, cluster = self._get_run_tags(run_id)

        if not (arn and cluster):
            return False

        tasks = self.ecs.describe_tasks(tasks=[arn], cluster=cluster).get("tasks")
        if not tasks:
            return False

        status = tasks[0].get("lastStatus")
        if status and status != "STOPPED":
            return True

        return False

    def terminate(self, run_id):
        arn, cluster = self._get_run_tags(run_id)

        if not (arn and cluster):
            return False

        tasks = self.ecs.describe_tasks(tasks=[arn], cluster=cluster).get("tasks")
        if not tasks:
            return False

        status = tasks[0].get("lastStatus")
        if status == "STOPPED":
            return False

        self.ecs.stop_task(task=arn, cluster=cluster)
        return True

    def _task_definition(self, metadata, image):
        """
        Return the launcher's default task definition if it's configured.

        Otherwise, a new task definition revision is registered for every run.
        First, the process that calls this method finds its own task
        definition. Next, it creates a new task definition based on its own
        but it overrides the image with the pipeline origin's image.
        """
        if self.task_definition:
            task_definition = self.ecs.describe_task_definition(taskDefinition=self.task_definition)
            return task_definition["taskDefinition"]

        return default_ecs_task_definition(self.ecs, metadata, image, self.container_name)

    def _task_metadata(self):
        return default_ecs_task_metadata(self.ec2, self.ecs)
