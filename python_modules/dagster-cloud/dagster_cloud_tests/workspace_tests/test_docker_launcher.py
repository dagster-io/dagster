# ruff: noqa: SLF001
import io
import tarfile
import time
from contextlib import contextmanager
from unittest.mock import patch

import docker
import docker.errors
import docker.models.containers
import pytest
import requests.exceptions
from dagster._core.test_utils import instance_for_test
from dagster_cloud.workspace.docker import (
    AGENT_LABEL,
    GRPC_SERVER_LABEL,
    STOP_TIMEOUT_LABEL,
    DockerUserCodeLauncher,
)
from dagster_cloud.workspace.docker.utils import docker_client_from_env, unique_docker_resource_name
from dagster_cloud.workspace.user_code_launcher import DEFAULT_SERVER_PROCESS_STARTUP_TIMEOUT
from dagster_cloud.workspace.user_code_launcher.user_code_launcher import UserCodeLauncherEntry
from dagster_cloud.workspace.user_code_launcher.utils import deterministic_label_for_location
from dagster_cloud_cli.core.workspace import CodeLocationDeployData


@pytest.fixture(autouse=True)
def _bump_docker_client_timeout(monkeypatch):
    # docker-py's default 60s read timeout pops on `containers.create` and other
    # control-plane calls when the dind sidecar is under I/O contention during
    # CI fan-out. Widen it for these tests; production behavior is unchanged.
    monkeypatch.setenv("DAGSTER_CLOUD_DOCKER_CLIENT_TIMEOUT", "180")


def _retry_on_docker_timeout(fn, *, max_attempts: int = 2, backoff_seconds: float = 2.0):
    # The dind sidecar occasionally hangs mid-call (storage-driver stalls under
    # CI fan-out contention), blowing through the full read timeout. A fresh
    # connection on the next attempt typically succeeds — production callers
    # don't see this because they only drive docker via the CLI, not the SDK.
    last_exc: requests.exceptions.ReadTimeout | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            return fn()
        except requests.exceptions.ReadTimeout as exc:
            last_exc = exc
            if attempt == max_attempts:
                raise
            time.sleep(backoff_seconds)
    raise last_exc  # type: ignore[misc]  # ty: ignore[invalid-raise]  # unreachable


@pytest.fixture
def docker_client():
    client = docker_client_from_env()

    existing_containers = client.containers.list(all=True)

    yield client

    for container in client.containers.list(all=True):
        if container not in existing_containers:
            container.stop()
            container.remove(force=True)


def test_config():
    assert DockerUserCodeLauncher.config_type()


@contextmanager
def docker_instance(user_code_launcher_overrides=None):
    with instance_for_test(
        {
            "instance_class": {
                "module": "dagster_cloud",
                "class": "DagsterCloudAgentInstance",
            },
            "user_code_launcher": {
                "module": "dagster_cloud.workspace.docker",
                "class": "DockerUserCodeLauncher",
                "config": user_code_launcher_overrides or {},
            },
            "dagster_cloud_api": {
                "url": "http://localhost:2874",
                "agent_token": "FAKE_TOKEN",
            },
            "compute_logs": {
                "module": "dagster._core.storage.noop_compute_log_manager",
                "class": "NoOpComputeLogManager",
            },
        }
    ) as instance:
        yield instance


def test_default_instance():
    with docker_instance() as instance:
        assert instance.user_code_launcher.env_vars == []
        assert instance.user_code_launcher.container_kwargs == {}
        assert (
            instance.user_code_launcher._server_process_startup_timeout
            == DEFAULT_SERVER_PROCESS_STARTUP_TIMEOUT
        )


def test_container_kwargs():
    container_kwargs = {"auto_remove": True}
    with docker_instance({"container_kwargs": container_kwargs}) as instance:
        assert instance.run_launcher.container_kwargs == container_kwargs


def test_override_timeout():
    with docker_instance({"server_process_startup_timeout": 1234}) as instance:
        assert instance.user_code_launcher._server_process_startup_timeout == 1234


@contextmanager
def _ensure_local_image(tag: str):
    """Build a minimal local Docker image to avoid Docker Hub rate limits in CI.

    Yields, then removes the image if it was created by this context manager.
    """
    client = docker_client_from_env()
    created = False
    try:
        client.images.get(tag)
    except docker.errors.ImageNotFound:
        # Use `docker import` with an empty tar to create a minimal image locally
        # without pulling from Docker Hub.
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w"):
            pass
        repo, _, image_tag = tag.rpartition(":")
        client.api.import_image_from_data(buf.getvalue(), repository=repo, tag=image_tag)
        created = True
    try:
        yield
    finally:
        if created:
            client.images.remove(tag, force=True)


def test_get_standalone_server_handles_for_location(docker_client):
    image_tag = "dagster/dagster-cloud-examples:1.12.5"
    with docker_instance() as instance, _ensure_local_image(image_tag):
        assert not instance.user_code_launcher._get_standalone_dagster_server_handles_for_location(
            deployment_name="foo",
            location_name="bar",
        )

        _retry_on_docker_timeout(
            lambda: docker_client.containers.create(
                image=image_tag,
                command="unused",  # imported images have no default CMD
                labels={
                    GRPC_SERVER_LABEL: "",
                    deterministic_label_for_location("foo", "bar"): "",
                    AGENT_LABEL: instance.instance_uuid,
                },
            )
        )

        handles = instance.user_code_launcher._get_standalone_dagster_server_handles_for_location(
            deployment_name="foo",
            location_name="bar",
        )

        assert len(handles) == 1

        handle = handles[0]
        create_timestamp = instance.user_code_launcher.get_server_create_timestamp(handle)

        assert create_timestamp <= time.time() and create_timestamp >= time.time() - 60 * 5


def test_long_docker_resource_name():
    long_deployment_name = "a" * 128
    long_location_name = "b" * 128

    assert len(unique_docker_resource_name(long_deployment_name, long_location_name)) == 63


def test_container_kwargs_stop_timeout():
    image_tag = "dagster/dagster-cloud-examples:1.9.10"
    with docker_instance() as instance, _ensure_local_image(image_tag):
        assert not instance.user_code_launcher._get_standalone_dagster_server_handles_for_location(
            deployment_name="foo",
            location_name="bar",
        )

        # Mock Container.start because the minimal scratch image has no executable
        with patch.object(docker.models.containers.Container, "start"):
            result = _retry_on_docker_timeout(
                lambda: instance.user_code_launcher._start_new_server_spinup(
                    deployment_name="foo",
                    location_name="bar",
                    desired_entry=UserCodeLauncherEntry(
                        code_location_deploy_data=CodeLocationDeployData(
                            image=image_tag,
                            package_name="dagster-cloud-examples",
                            container_context={
                                "docker": {"container_kwargs": {"stop_timeout": 23}}
                            },
                        ),
                        update_timestamp=time.time(),
                    ),
                )
            )
            assert result.server_handle.container.labels[STOP_TIMEOUT_LABEL] == "23"

        assert instance.user_code_launcher._get_standalone_dagster_server_handles_for_location(
            deployment_name="foo",
            location_name="bar",
        )

        instance.user_code_launcher._remove_server_handle(result.server_handle)
