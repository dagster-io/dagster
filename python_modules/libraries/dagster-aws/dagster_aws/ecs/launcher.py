import os
from dataclasses import dataclass
from typing import List

import boto3
import requests
from dagster.core.launcher.base import RunLauncher
from dagster.grpc.types import ExecuteRunArgs
from dagster.serdes import ConfigurableClass, serialize_dagster_namedtuple
from dagster.utils.backcompat import experimental_class_warning


@dataclass
class TaskMetadata:
    arn: str
    container: str
    family: str
    cluster: str
    subnets: List[str]


class EcsRunLauncher(RunLauncher, ConfigurableClass):
    def __init__(self, inst_data=None, boto3_client=boto3.client("ecs", region_name="us-east-1")):
        experimental_class_warning("EcsRunLauncher")

        self._inst_data = inst_data
        self.ecs = boto3_client

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {}

    @staticmethod
    def from_config_value(inst_data, config_value):
        return EcsRunLauncher(inst_data=inst_data, **config_value)

    def _ecs_tags(self, run_id):
        return [{"key": "dagster/run_id", "value": run_id}]

    def _run_tags(self, task_arn):
        cluster = self._task_metadata().cluster
        return {"ecs/task_arn": task_arn, "ecs/cluster": cluster}

    def launch_run(self, run, external_pipeline):
        """
        Launch a run using the same task definition as the parent process but
        overriding its command to execute `dagster api execute_run` instead.

        Currently, Fargate is the only supported launchType and awsvpc is the
        only supported networkMode. These are the defaults that are set up by
        docker-compose when you use the Dagster ECS reference deployment.

        When using the Dagster ECS reference deployment, the parent process
        will be running in a daemon task so pipeline runs will all be part of
        the daemon task definition family.

        TODO: Support creating a new task definition (with custom config)
              instead of spawning from the parent process.
        """
        metadata = self._task_metadata()

        input_json = serialize_dagster_namedtuple(
            ExecuteRunArgs(
                pipeline_origin=external_pipeline.get_python_origin(),
                pipeline_run_id=run.run_id,
                instance_ref=self._instance.get_ref(),
            )
        )
        command = ["dagster", "api", "execute_run", input_json]

        response = self.ecs.run_task(
            taskDefinition=metadata.family,
            cluster=metadata.cluster,
            overrides={"containerOverrides": [{"name": metadata.container, "command": command}]},
            networkConfiguration={
                "awsvpcConfiguration": {
                    "subnets": metadata.subnets,
                    "assignPublicIp": "ENABLED",
                }
            },
            launchType="FARGATE",
        )

        arn = response["tasks"][0]["taskArn"]
        self._instance.add_run_tags(run.run_id, self._run_tags(task_arn=arn))
        self.ecs.tag_resource(resourceArn=arn, tags=self._ecs_tags(run.run_id))

        return run.run_id

    def can_terminate(self, run_id):
        arn = self._instance.get_run_by_id(run_id).tags.get("ecs/task_arn")
        if arn:
            cluster = self._task_metadata().cluster
            status = self.ecs.describe_tasks(tasks=[arn], cluster=cluster)["tasks"][0]["lastStatus"]
            if status != "STOPPED":
                return True

        return False

    def terminate(self, run_id):
        cluster = self._task_metadata().cluster
        arn = self._instance.get_run_by_id(run_id).tags.get("ecs/task_arn")
        status = self.ecs.describe_tasks(tasks=[arn], cluster=cluster)["tasks"][0]["lastStatus"]
        if status == "STOPPED":
            return False

        self.ecs.stop_task(task=arn, cluster=cluster)
        return True

    def _task_metadata(self):
        """
        ECS injects an environment variable into each Fargate task. The value
        of this environment variable is a url that can be queried to introspect
        information about the running task:

        https://docs.aws.amazon.com/AmazonECS/latest/userguide/task-metadata-endpoint-v4-fargate.html

        We use this so we can spawn new tasks using the same task definition as
        the existing process.
        """
        container_metadata_uri = os.environ.get("ECS_CONTAINER_METADATA_URI_V4")
        container = requests.get(container_metadata_uri).json()["Name"]

        task_metadata_uri = container_metadata_uri + "/task"
        response = requests.get(task_metadata_uri).json()
        cluster = response.get("Cluster")
        arn = response.get("TaskARN")
        family = response.get("Family")

        task = self.ecs.describe_tasks(tasks=[arn], cluster=cluster)["tasks"][0]
        subnets = []
        for attachment in task["attachments"]:
            if attachment["type"] == "ElasticNetworkInterface":
                for detail in attachment["details"]:
                    if detail["name"] == "subnetId":
                        subnets.append(detail["value"])

        return TaskMetadata(
            arn=arn, container=container, family=family, cluster=cluster, subnets=subnets
        )
