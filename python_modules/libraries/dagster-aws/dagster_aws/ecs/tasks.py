import os
from typing import Any, Mapping, NamedTuple, Optional, Sequence

import requests

import dagster._check as check
from dagster._utils import merge_dicts
from dagster._utils.backoff import backoff


class DagsterEcsTaskDefinitionConfig(
    NamedTuple(
        "_DagsterEcsTaskDefinitionConfig",
        [
            ("family", str),
            ("image", str),
            ("container_name", str),
            ("command", Optional[Sequence[str]]),
            ("log_configuration", Optional[Mapping[str, Any]]),
            ("secrets", Sequence[Mapping[str, str]]),
            ("environment", Sequence[Mapping[str, str]]),
            ("execution_role_arn", Optional[str]),
            ("task_role_arn", Optional[str]),
            ("sidecars", Sequence[Mapping[str, Any]]),
            ("requires_compatibilities", Sequence[str]),
            ("cpu", str),
            ("memory", str),
        ],
    )
):
    """All the information that Dagster needs to create a task definition and compare two task
    definitions to see if they should be reused."""

    def __new__(
        cls,
        family: str,
        image: str,
        container_name: str,
        command: Optional[Sequence[str]],
        log_configuration: Optional[Mapping[str, Any]],
        secrets: Optional[Sequence[Mapping[str, str]]],
        environment: Optional[Sequence[Mapping[str, str]]],
        execution_role_arn: Optional[str],
        task_role_arn: Optional[str],
        sidecars: Optional[Sequence[Mapping[str, Any]]],
        requires_compatibilities: Optional[Sequence[str]],
        cpu: Optional[str] = None,
        memory: Optional[str] = None,
    ):
        return super(DagsterEcsTaskDefinitionConfig, cls).__new__(
            cls,
            check.str_param(family, "family"),
            check.str_param(image, "image"),
            check.str_param(container_name, "container_name"),
            check.opt_sequence_param(command, "command"),
            check.opt_mapping_param(log_configuration, "log_configuration"),
            check.opt_sequence_param(secrets, "secrets"),
            check.opt_sequence_param(environment, "environment"),
            check.opt_str_param(execution_role_arn, "execution_role_arn"),
            check.opt_str_param(task_role_arn, "task_role_arn"),
            check.opt_sequence_param(sidecars, "sidecars"),
            check.opt_sequence_param(requires_compatibilities, "requires_compatibilities"),
            check.opt_str_param(cpu, "cpu", default="256"),
            check.opt_str_param(memory, "memory", default="512"),
        )

    def task_definition_dict(self):
        kwargs = dict(
            family=self.family,
            requiresCompatibilities=self.requires_compatibilities,
            networkMode="awsvpc",
            containerDefinitions=[
                merge_dicts(
                    {
                        "name": self.container_name,
                        "image": self.image,
                    },
                    (
                        {"logConfiguration": self.log_configuration}
                        if self.log_configuration
                        else {}
                    ),
                    ({"command": self.command} if self.command else {}),
                    ({"secrets": self.secrets} if self.secrets else {}),
                    ({"environment": self.environment} if self.environment else {}),
                ),
                *self.sidecars,
            ],
            cpu=self.cpu,
            memory=self.memory,
        )

        if self.execution_role_arn:
            kwargs.update(dict(executionRoleArn=self.execution_role_arn))

        if self.task_role_arn:
            kwargs.update(dict(taskRoleArn=self.task_role_arn))

        return kwargs

    @staticmethod
    def from_task_definition_dict(task_definition_dict, container_name):

        matching_container_defs = [
            container
            for container in task_definition_dict["containerDefinitions"]
            if container["name"] == container_name
        ]

        if not matching_container_defs:
            raise Exception(f"No container in task definition with expected name {container_name}")

        container_definition = matching_container_defs[0]

        sidecars = [
            container
            for container in task_definition_dict["containerDefinitions"]
            if container["name"] != container_name
        ]

        return DagsterEcsTaskDefinitionConfig(
            family=task_definition_dict["family"],
            image=container_definition["image"],
            container_name=container_name,
            command=container_definition.get("command"),
            log_configuration=container_definition.get("logConfiguration"),
            secrets=container_definition.get("secrets"),
            environment=container_definition.get("environment"),
            execution_role_arn=task_definition_dict.get("executionRoleArn"),
            task_role_arn=task_definition_dict.get("taskRoleArn"),
            sidecars=sidecars,
            requires_compatibilities=task_definition_dict.get("requiresCompatibilities"),
            cpu=task_definition_dict.get("cpu"),
            memory=task_definition_dict.get("memory"),
        )


# 9 retries polls for up to 51.1 seconds with exponential backoff.
BACKOFF_RETRIES = 9


# The ECS API is eventually consistent:
# https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_RunTask.html
# describe_tasks might initially return nothing even if a task exists.
class EcsEventualConsistencyTimeout(Exception):
    pass


class EcsNoTasksFound(Exception):
    pass


def get_task_definition_dict_from_current_task(
    ecs,
    family,
    current_task,
    image,
    container_name,
    environment,
    command=None,
    secrets=None,
    include_sidecars=False,
):

    current_container_name = current_ecs_container_name()

    current_task_definition_arn = current_task["taskDefinitionArn"]
    current_task_definition_dict = ecs.describe_task_definition(
        taskDefinition=current_task_definition_arn
    )["taskDefinition"]

    container_definition = next(
        iter(
            [
                container
                for container in current_task_definition_dict["containerDefinitions"]
                if container["name"] == current_container_name
            ]
        )
    )

    # Start with the current process's task's definition but remove
    # extra keys that aren't useful for creating a new task definition
    # (status, revision, etc.)
    expected_keys = [
        key for key in ecs.meta.service_model.shape_for("RegisterTaskDefinitionRequest").members
    ]
    task_definition = dict(
        (key, current_task_definition_dict[key])
        for key in expected_keys
        if key in current_task_definition_dict.keys()
    )

    # The current process might not be running in a container that has the
    # pipeline's code installed. Inherit most of the process's container
    # definition (things like environment, dependencies, etc.) but replace
    # the image with the pipeline origin's image and give it a new name.
    # Also remove entryPoint. We plan to set containerOverrides. If both
    # entryPoint and containerOverrides are specified, they're concatenated
    # and the command will fail
    # https://aws.amazon.com/blogs/opensource/demystifying-entrypoint-cmd-docker/
    new_container_definition = merge_dicts(
        {
            **container_definition,
            "name": container_name,
            "image": image,
            "entryPoint": [],
            "command": command if command else [],
        },
        ({"environment": environment} if environment else {}),
        ({"secrets": secrets} if secrets else {}),
        {} if include_sidecars else {"dependsOn": []},
    )

    if include_sidecars:
        container_definitions = current_task_definition_dict.get("containerDefinitions")
        container_definitions.remove(container_definition)
        container_definitions.append(new_container_definition)
    else:
        container_definitions = [new_container_definition]

    task_definition = {
        **task_definition,
        "family": family,
        "containerDefinitions": container_definitions,
    }

    return task_definition


class CurrentEcsTaskMetadata(
    NamedTuple("_CurrentEcsTaskMetadata", [("cluster", str), ("task_arn", str)])
):
    pass


def get_current_ecs_task_metadata() -> CurrentEcsTaskMetadata:
    task_metadata_uri = _container_metadata_uri() + "/task"
    response = requests.get(task_metadata_uri).json()
    cluster = response.get("Cluster")
    task_arn = response.get("TaskARN")

    return CurrentEcsTaskMetadata(cluster=cluster, task_arn=task_arn)


def _container_metadata_uri():
    """
    ECS injects an environment variable into each Fargate task. The value
    of this environment variable is a url that can be queried to introspect
    information about the current processes's running task:

    https://docs.aws.amazon.com/AmazonECS/latest/userguide/task-metadata-endpoint-v4-fargate.html
    """
    return os.environ.get("ECS_CONTAINER_METADATA_URI_V4")


def current_ecs_container_name():
    return requests.get(_container_metadata_uri()).json()["Name"]


def get_current_ecs_task(ecs, task_arn, cluster):
    def describe_task_or_raise(task_arn, cluster):
        try:
            return ecs.describe_tasks(tasks=[task_arn], cluster=cluster)["tasks"][0]
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

    return task


def get_task_kwargs_from_current_task(
    ec2,
    cluster,
    task,
):
    enis = []
    subnets = []
    for attachment in task["attachments"]:
        if attachment["type"] == "ElasticNetworkInterface":
            for detail in attachment["details"]:
                if detail["name"] == "subnetId":
                    subnets.append(detail["value"])
                if detail["name"] == "networkInterfaceId":
                    enis.append(ec2.NetworkInterface(detail["value"]))

    public_ip = False
    security_groups = []
    for eni in enis:
        if (eni.association_attribute or {}).get("PublicIp"):
            public_ip = True
        for group in eni.groups:
            security_groups.append(group["GroupId"])

    return {
        "cluster": cluster,
        "networkConfiguration": {
            "awsvpcConfiguration": {
                "subnets": subnets,
                "assignPublicIp": "ENABLED" if public_ip else "DISABLED",
                "securityGroups": security_groups,
            },
        },
        "launchType": task.get("launchType") or "FARGATE",
    }
