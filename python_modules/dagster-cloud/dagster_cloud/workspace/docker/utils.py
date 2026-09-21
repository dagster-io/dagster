import os
import re

import docker

from dagster_cloud.workspace.user_code_launcher.utils import unique_resource_name


def unique_docker_resource_name(deployment_name, location_name):
    return unique_resource_name(
        deployment_name,
        location_name,
        length_limit=63,  # Max DNS hostname limit
        sanitize_fn=lambda name: re.sub("[^a-z0-9-]", "", name).strip("-"),
    )


def docker_client_from_env() -> docker.DockerClient:
    timeout = int(os.environ.get("DAGSTER_CLOUD_DOCKER_CLIENT_TIMEOUT", "60"))
    return docker.client.from_env(timeout=timeout)
