import hashlib
import re
from collections.abc import Mapping
from typing import Any

from dagster._core.remote_representation.origin import RemoteJobOrigin

from dagster_aws.ecs.tasks import DagsterEcsTaskDefinitionConfig


def sanitize_family(family):
    # Trim the location name and remove special characters
    return re.sub(r"[^\w^\-]", "", family)[:255]


def sanitize_tag(tag):
    # https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs-using-tags.html
    return re.sub("[^A-Za-z0-9_]", "-", tag)[:255].strip("-")


def _get_family_hash(name):
    m = hashlib.sha1()
    m.update(name.encode("utf-8"))
    name_hash = m.hexdigest()[:8]
    return f"{name[:55]}_{name_hash}"


class RetryableEcsException(Exception): ...


def run_ecs_task(ecs, run_task_kwargs) -> Mapping[str, Any]:
    response = ecs.run_task(**run_task_kwargs)

    tasks = response["tasks"]

    if not tasks:
        failures = response["failures"]
        failure_messages = []
        for failure in failures:
            arn = failure.get("arn")
            reason = failure.get("reason")
            detail = failure.get("detail")

            failure_message = (
                "Task"
                + (f" {arn}" if arn else "")
                + " failed."
                + (f" Failure reason: {reason}" if reason else "")
                + (f" Failure details: {detail}" if detail else "")
            )
            failure_messages.append(failure_message)

        failure_message = "\n".join(failure_messages) if failure_messages else "Task failed."

        if "Capacity is unavailable at this time" in failure_message:
            raise RetryableEcsException(failure_message)

        raise Exception(failure_message)
    return tasks[0]


def get_task_definition_family(
    prefix: str,
    job_origin: RemoteJobOrigin,
) -> str:
    job_name = job_origin.job_name
    repo_name = job_origin.repository_origin.repository_name
    location_name = job_origin.repository_origin.code_location_origin.location_name

    assert len(prefix) < 32

    # Truncate the location name if it's too long (but add a unique suffix at the end so that no matter what it's unique)
    # Relies on the fact that org name and deployment name are always <= 64 characters long to
    # stay well underneath the 255 character limit imposed by ECS

    final_family = f"{prefix}_{_get_family_hash(location_name)}_{_get_family_hash(repo_name)}_{_get_family_hash(job_name)}"

    assert len(final_family) <= 255

    return sanitize_family(final_family)


def task_definitions_match(
    desired_task_definition_config: DagsterEcsTaskDefinitionConfig,
    existing_task_definition: Mapping[str, Any],
    container_name: str,
) -> bool:
    if not any(
        [
            container["name"] == container_name
            for container in existing_task_definition["containerDefinitions"]
        ]
    ):
        return False

    existing_task_definition_config = DagsterEcsTaskDefinitionConfig.from_task_definition_dict(
        existing_task_definition, container_name
    )

    return existing_task_definition_config.matches_other_task_definition_config(
        desired_task_definition_config
    )


def get_task_logs(ecs, logs_client, cluster, task_arn, container_name, limit=10):
    task = ecs.describe_tasks(cluster=cluster, tasks=[task_arn]).get("tasks")[0]

    task_definition_arn = task.get("taskDefinitionArn")
    task_definition = ecs.describe_task_definition(taskDefinition=task_definition_arn).get(
        "taskDefinition"
    )

    matching_container_definitions = [
        container_definition
        for container_definition in task_definition.get("containerDefinitions", [])
        if container_definition["name"] == container_name
    ]
    if not matching_container_definitions:
        raise Exception(f"Could not find container with name {container_name}")

    container_definition = matching_container_definitions[0]

    log_options = container_definition.get("logConfiguration", {}).get("options", {})
    log_group = log_options.get("awslogs-group")
    log_stream_prefix = log_options.get("awslogs-stream-prefix")

    if not log_group or not log_stream_prefix:
        return []

    container_name = container_definition.get("name")
    task_id = task_arn.split("/")[-1]

    log_stream = f"{log_stream_prefix}/{container_name}/{task_id}"

    events = logs_client.get_log_events(
        logGroupName=log_group, logStreamName=log_stream, limit=limit
    ).get("events")

    return [event.get("message") for event in events]


def is_transient_task_stopped_reason(stopped_reason: str) -> bool:
    if "Timeout waiting for network interface provisioning to complete" in stopped_reason:
        return True

    if "Timeout waiting for EphemeralStorage provisioning to complete" in stopped_reason:
        return True

    if "CannotPullContainerError" in stopped_reason and "i/o timeout" in stopped_reason:
        return True

    if "CannotPullContainerError" in stopped_reason and (
        "invalid argument" in stopped_reason or "EOF" in stopped_reason
    ):
        return True

    if (
        "Unexpected EC2 error while attempting to Create Network Interface" in stopped_reason
        and "AuthFailure" in stopped_reason
    ):
        return True

    return False
