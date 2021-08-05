import os
import typing
from dataclasses import dataclass

import boto3
import dagster
import requests
from dagster import Field, check
from dagster.core.launcher.base import LaunchRunContext, RunLauncher
from dagster.grpc.types import ExecuteRunArgs
from dagster.serdes import ConfigurableClass, serialize_dagster_namedtuple
from dagster.utils.backcompat import experimental
from dagster.utils.backoff import backoff


# The ECS API is eventually consistent:
# https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_RunTask.html
# describe_tasks might initially return nothing even if a task exists.
class EcsEventualConsistencyTimeout(Exception):
    pass


class EcsNoTasksFound(Exception):
    pass


# 9 retries polls for up to 51.1 seconds with exponential backoff.
BACKOFF_RETRIES = 9


@dataclass
class TaskMetadata:
    cluster: str
    subnets: typing.List[str]
    security_groups: typing.List[str]
    task_definition: typing.Dict[str, typing.Any]
    container_definition: typing.Dict[str, typing.Any]


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
        tags = [{"key": "dagster/run_id", "value": run_id}]
        self.ecs.tag_resource(resourceArn=task_arn, tags=tags)

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

        input_json = serialize_dagster_namedtuple(
            ExecuteRunArgs(
                pipeline_origin=pipeline_origin,
                pipeline_run_id=run.run_id,
                instance_ref=self._instance.get_ref(),
            )
        )
        command = ["dagster", "api", "execute_run", input_json]

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

        # Start with the current process's task's definition but remove
        # extra keys that aren't useful for creating a new task definition
        # (status, revision, etc.)
        expected_keys = [
            key
            for key in self.ecs.meta.service_model.shape_for(
                "RegisterTaskDefinitionRequest"
            ).members
        ]
        task_definition = dict(
            (key, metadata.task_definition[key])
            for key in expected_keys
            if key in metadata.task_definition.keys()
        )

        # The current process might not be running in a container that has the
        # pipeline's code installed. Inherit most of the process's container
        # definition (things like environment, dependencies, etc.) but replace
        # the image with the pipeline origin's image and give it a new name.
        # Also remove entryPoint. We plan to set containerOverrides. If both
        # entryPoint and containerOverrides are specified, they're concatenated
        # and the command will fail
        # https://aws.amazon.com/blogs/opensource/demystifying-entrypoint-cmd-docker/
        container_definitions = task_definition["containerDefinitions"]
        container_definitions.remove(metadata.container_definition)
        container_definitions.append(
            {
                **metadata.container_definition,
                "name": self.container_name,
                "image": image,
                "entryPoint": [],
            }
        )
        task_definition = {
            **task_definition,
            "family": "dagster-run",
            "containerDefinitions": container_definitions,
        }

        # Register the task overridden task definition as a revision to the
        # "dagster-run" family.
        # TODO: Only register the task definition if a matching one doesn't
        # already exist. Otherwise, we risk exhausting the revisions limit
        # (1,000,000 per family) with unnecessary revisions:
        # https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service-quotas.html
        self.ecs.register_task_definition(**task_definition)

        return task_definition

    def _task_metadata(self):
        """
        ECS injects an environment variable into each Fargate task. The value
        of this environment variable is a url that can be queried to introspect
        information about the current processes's running task:

        https://docs.aws.amazon.com/AmazonECS/latest/userguide/task-metadata-endpoint-v4-fargate.html
        """
        container_metadata_uri = os.environ.get("ECS_CONTAINER_METADATA_URI_V4")
        name = requests.get(container_metadata_uri).json()["Name"]

        task_metadata_uri = container_metadata_uri + "/task"
        response = requests.get(task_metadata_uri).json()
        cluster = response.get("Cluster")
        task_arn = response.get("TaskARN")

        def describe_task_or_raise(task_arn, cluster):
            try:
                return self.ecs.describe_tasks(tasks=[task_arn], cluster=cluster)["tasks"][0]
            except IndexError:
                raise EcsNoTasksFound

        try:
            task = backoff(
                describe_task_or_raise,
                retry_on=(EcsNoTasksFound,),
                kwargs={"task_arn": task_arn, "cluster": cluster},
                max_retries=BACKOFF_RETRIES,
            )
        except EcsNoTasksFound:
            raise EcsEventualConsistencyTimeout

        enis = []
        subnets = []
        for attachment in task["attachments"]:
            if attachment["type"] == "ElasticNetworkInterface":
                for detail in attachment["details"]:
                    if detail["name"] == "subnetId":
                        subnets.append(detail["value"])
                    if detail["name"] == "networkInterfaceId":
                        enis.append(self.ec2.NetworkInterface(detail["value"]))

        security_groups = []
        for eni in enis:
            for group in eni.groups:
                security_groups.append(group["GroupId"])

        task_definition_arn = task["taskDefinitionArn"]
        task_definition = self.ecs.describe_task_definition(taskDefinition=task_definition_arn)[
            "taskDefinition"
        ]

        container_definition = next(
            iter(
                [
                    container
                    for container in task_definition["containerDefinitions"]
                    if container["name"] == name
                ]
            )
        )

        return TaskMetadata(
            cluster=cluster,
            subnets=subnets,
            security_groups=security_groups,
            task_definition=task_definition,
            container_definition=container_definition,
        )
