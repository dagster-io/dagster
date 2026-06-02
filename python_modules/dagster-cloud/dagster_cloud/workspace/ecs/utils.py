import hashlib
import re

from dagster._core.remote_origin import RemoteJobOrigin
from dagster_aws.ecs.utils import sanitize_family

from dagster_cloud.workspace.user_code_launcher.utils import (
    get_human_readable_label,
    unique_resource_name,
)


def unique_ecs_resource_name(deployment_name, location_name):
    return unique_resource_name(
        deployment_name,
        location_name,
        length_limit=60,  # Service discovery name must satisfy DNS
        sanitize_fn=lambda name: re.sub("[^a-z0-9-]", "", name).strip("-"),
    )


def get_ecs_human_readable_label(name):
    return get_human_readable_label(
        name,
        length_limit=60,  # Service discovery name must satisfy DNS
        sanitize_fn=lambda name: re.sub("[^a-z0-9-]", "", name).strip("-"),
    )


def _get_family_hash(name, max_length=32, hash_size=8):
    m = hashlib.sha1()
    m.update(name.encode("utf-8"))
    name_hash = m.hexdigest()[:hash_size]
    return f"{name[: (max_length - hash_size - 1)]}_{name_hash}"


def get_server_task_definition_family(
    task_definition_prefix: str,
    organization_name: str | None,
    deployment_name: str,
    location_name: str,
) -> str:
    # Truncate the location name if it's too long (but add a unique suffix at the end so that no matter what it's unique)
    # Relies on the fact that org name and deployment name are always <= 64 characters long to
    # stay well underneath the 255 character limit imposed by ECS
    m = hashlib.sha1()
    m.update(location_name.encode("utf-8"))

    # '{16}_{64}_{64}_{64}': max 211 characters
    truncated_location_name = _get_family_hash(location_name, max_length=64)

    final_family: str = (
        f"{task_definition_prefix}_{organization_name}_{deployment_name}_{truncated_location_name}"
    )

    assert len(final_family) <= 255

    return sanitize_family(final_family)


def get_run_task_definition_family(
    task_definition_prefix: str,
    organization_name: str | None,
    deployment_name: str,
    job_origin: RemoteJobOrigin,
) -> str:
    # Truncate the location name if it's too long (but add a unique suffix at the end so that no matter what it's unique)
    # Relies on the fact that org name and deployment name are always <= 64 characters long to
    # stay well underneath the 255 character limit imposed by ECS
    job_name = job_origin.job_name
    repo_name = job_origin.repository_origin.repository_name
    location_name = job_origin.repository_origin.code_location_origin.location_name

    assert len(task_definition_prefix) <= 16
    assert len(str(organization_name)) <= 64
    assert len(deployment_name) <= 64

    # '{16}_{64}_{64}_{32}_{32}_{32}': max 245 characters

    final_family = f"{task_definition_prefix}_{organization_name}_{deployment_name}_{_get_family_hash(location_name)}_{_get_family_hash(repo_name)}_{_get_family_hash(job_name)}"

    assert len(final_family) <= 255

    return sanitize_family(final_family)
