import os
import typing
from dataclasses import dataclass

import requests

from dagster.utils import merge_dicts
from dagster.utils.backoff import backoff


@dataclass
class TaskMetadata:
    cluster: str
    subnets: typing.List[str]
    security_groups: typing.List[str]
    task_definition: typing.Dict[str, typing.Any]
    container_definition: typing.Dict[str, typing.Any]
    assign_public_ip: bool


# 9 retries polls for up to 51.1 seconds with exponential backoff.
BACKOFF_RETRIES = 9


# The ECS API is eventually consistent:
# https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_RunTask.html
# describe_tasks might initially return nothing even if a task exists.
class EcsEventualConsistencyTimeout(Exception):
    pass


class EcsNoTasksFound(Exception):
    pass


def default_ecs_task_definition(
    ecs,
    family,
    metadata,
    image,
    container_name,
    command=None,
    secrets=None,
    include_sidecars=False,
):
    # Start with the current process's task's definition but remove
    # extra keys that aren't useful for creating a new task definition
    # (status, revision, etc.)
    expected_keys = [
        key for key in ecs.meta.service_model.shape_for("RegisterTaskDefinitionRequest").members
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
    new_container_definition = merge_dicts(
        {
            **metadata.container_definition,
            "name": container_name,
            "image": image,
            "entryPoint": [],
            "command": command if command else [],
        },
        secrets or {},
        {} if include_sidecars else {"dependsOn": []},
    )

    if include_sidecars:
        container_definitions = metadata.task_definition.get("containerDefinitions")
        container_definitions.remove(metadata.container_definition)
        container_definitions.append(new_container_definition)
    else:
        container_definitions = [new_container_definition]

    task_definition = {
        **task_definition,
        "family": family,
        "containerDefinitions": container_definitions,
    }

    # Register the task overridden task definition as a revision to the
    # "dagster-run" family.
    ecs.register_task_definition(**task_definition)

    return task_definition


def default_ecs_task_metadata(ec2, ecs):
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

    task_definition_arn = task["taskDefinitionArn"]
    task_definition = ecs.describe_task_definition(taskDefinition=task_definition_arn)[
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
        assign_public_ip="ENABLED" if public_ip else "DISABLED",
    )
