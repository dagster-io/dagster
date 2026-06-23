import logging
import sys
import time
from typing import Any, NamedTuple

import docker
import docker.errors
from dagster import (
    Field,
    IntSource,
    _check as check,
)
from dagster._core.launcher.base import LaunchRunContext
from dagster._core.utils import parse_env_var
from dagster._grpc.types import ExecuteRunArgs
from dagster._serdes import ConfigurableClass
from dagster._serdes.config_class import ConfigurableClassData
from dagster._utils import find_free_port
from dagster._utils.merger import merge_dicts
from dagster._vendored.dateutil.parser import parse
from dagster_cloud_cli.core.workspace import PexMetadata
from dagster_docker import DockerRunLauncher
from dagster_docker.container_context import DockerContainerContext
from dagster_shared.serdes.serdes import deserialize_value, serialize_value
from docker.models.containers import Container
from typing_extensions import Self

from dagster_cloud.api.dagster_cloud_api import UserCodeDeploymentType
from dagster_cloud.execution.monitoring import CloudContainerResourceLimits
from dagster_cloud.storage.tags import PEX_METADATA_TAG
from dagster_cloud.workspace.config_schema.docker import SHARED_DOCKER_CONFIG
from dagster_cloud.workspace.docker.utils import docker_client_from_env, unique_docker_resource_name
from dagster_cloud.workspace.user_code_launcher import (
    DEFAULT_SERVER_PROCESS_STARTUP_TIMEOUT,
    SHARED_USER_CODE_LAUNCHER_CONFIG,
    DagsterCloudGrpcServer,
    DagsterCloudUserCodeLauncher,
    ServerEndpoint,
)
from dagster_cloud.workspace.user_code_launcher.user_code_launcher import UserCodeLauncherEntry
from dagster_cloud.workspace.user_code_launcher.utils import (
    deterministic_label_for_location,
    get_code_server_port,
    get_grpc_server_env,
)

GRPC_SERVER_LABEL = "dagster_grpc_server"
MULTIPEX_SERVER_LABEL = "dagster_multipex_server"
AGENT_LABEL = "dagster_agent_id"
SERVER_TIMESTAMP_LABEL = "dagster_server_timestamp"
STOP_TIMEOUT_LABEL = "dagster_stop_timeout"


IMAGE_PULL_LOG_INTERVAL = 15


class DagsterDockerContainer(NamedTuple):
    """We use __str__ on server handles to serialize them to the run tags. Wrap the docker container
    object so that we can serialize it to a string.
    """

    container: Container

    def __str__(self):
        return self.container.id


class DockerUserCodeLauncher(
    DagsterCloudUserCodeLauncher[DagsterDockerContainer], ConfigurableClass
):
    def __init__(
        self,
        inst_data=None,
        networks=None,
        env_vars=None,
        container_kwargs=None,
        **kwargs,
    ):
        self._inst_data = inst_data
        self._logger = logging.getLogger("dagster_cloud")
        self._networks = check.opt_list_param(networks, "networks", of_type=str)
        self._input_env_vars = check.opt_list_param(env_vars, "env_vars", of_type=str)

        self._container_kwargs = check.opt_dict_param(
            container_kwargs, "container_kwargs", key_type=str
        )

        super().__init__(**kwargs)

    @property
    def requires_images(self):
        return True

    def user_code_deployment_type(self) -> UserCodeDeploymentType:
        return UserCodeDeploymentType.DOCKER

    @property
    def inst_data(self):
        return self._inst_data

    @property
    def env_vars(self) -> list[str]:
        return self._input_env_vars + self._instance.dagster_cloud_api_env_vars

    @property
    def container_kwargs(self) -> dict[str, Any]:
        return self._container_kwargs

    @classmethod
    def config_type(cls):
        return merge_dicts(
            SHARED_DOCKER_CONFIG,
            {
                "server_process_startup_timeout": Field(
                    IntSource,
                    is_required=False,
                    default_value=DEFAULT_SERVER_PROCESS_STARTUP_TIMEOUT,
                    description=(
                        "Timeout when waiting for a code server to be ready after it is created"
                    ),
                ),
            },
            SHARED_USER_CODE_LAUNCHER_CONFIG,
        )

    @classmethod
    def from_config_value(cls, inst_data: ConfigurableClassData, config_value: Any) -> Self:
        return cls(inst_data=inst_data, **config_value)

    def _create_container(
        self,
        client,
        image,
        container_name,
        hostname,
        environment,
        ports,
        container_context,
        command,
        labels,
    ):
        container_kwargs = {**container_context.container_kwargs}

        container_kwargs.pop("stop_timeout", None)

        return client.containers.create(
            image,
            detach=True,
            hostname=hostname,
            name=container_name,
            network=container_context.networks[0] if len(container_context.networks) else None,
            environment=environment,
            labels=labels,
            command=command,
            ports=ports,
            **container_kwargs,
        )

    def _get_standalone_dagster_server_handles_for_location(
        self, deployment_name: str, location_name: str
    ) -> list[DagsterDockerContainer]:
        client = docker_client_from_env()
        return [
            DagsterDockerContainer(container=container)
            for container in client.containers.list(
                all=True,
                filters={
                    "label": [
                        GRPC_SERVER_LABEL,
                        deterministic_label_for_location(deployment_name, location_name),
                        f"{AGENT_LABEL}={self._instance.instance_uuid}",
                    ]
                },
            )
        ]

    def _get_multipex_server_handles_for_location(
        self, deployment_name: str, location_name: str
    ) -> list[DagsterDockerContainer]:
        client = docker_client_from_env()
        return [
            DagsterDockerContainer(container=container)
            for container in client.containers.list(
                all=True,
                filters={
                    "label": [
                        MULTIPEX_SERVER_LABEL,
                        deterministic_label_for_location(deployment_name, location_name),
                        f"{AGENT_LABEL}={self._instance.instance_uuid}",
                    ]
                },
            )
        ]

    def _launch_container(
        self,
        deployment_name: str,
        location_name: str,
        container_name: str,
        hostname: str,
        grpc_port: int,
        ports: dict[int, int],
        image: str,
        container_context: DockerContainerContext,
        command: list[str],
        additional_env: dict[str, str],
        labels: dict[str, str],
    ) -> tuple[Container, ServerEndpoint]:
        client = docker_client_from_env()

        self._logger.info(
            f"Starting a new container for {deployment_name}:{location_name} with image {image}:"
            f" {container_name}"
        )

        environment = merge_dicts(
            (dict([parse_env_var(env_var) for env_var in container_context.env_vars])),
            additional_env,
        )

        try:
            container = self._create_container(
                client,
                image,
                container_name,
                hostname,
                environment,
                ports,
                container_context,
                command,
                labels,
            )
        except docker.errors.ImageNotFound:
            last_log_time = time.time()
            self._logger.info(f"Pulling image {image}...")
            for _line in docker.APIClient().pull(image, stream=True):
                if time.time() - last_log_time > IMAGE_PULL_LOG_INTERVAL:
                    self._logger.info(f"Still pulling image {image}...")
                    last_log_time = time.time()

            container = self._create_container(
                client,
                image,
                container_name,
                hostname,
                environment,
                ports,
                container_context,
                command,
                labels,
            )

        if len(container_context.networks) > 1:
            for network_name in container_context.networks[1:]:
                network = client.networks.get(network_name)
                network.connect(container)

        container.start()

        endpoint = ServerEndpoint(
            host=hostname,
            port=grpc_port,
            socket=None,
        )

        self._logger.info(f"Started container {container.id}")

        return (container, endpoint)

    def get_code_server_resource_limits(
        self, deployment_name: str, location_name: str
    ) -> CloudContainerResourceLimits:
        # Empty because we don't currently internally monitor docker deployment resource usage.
        return {}

    def _start_new_server_spinup(
        self,
        deployment_name: str,
        location_name: str,
        desired_entry: UserCodeLauncherEntry,
    ) -> DagsterCloudGrpcServer:
        metadata = desired_entry.code_location_deploy_data
        container_name = unique_docker_resource_name(deployment_name, location_name)

        container_context = DockerContainerContext(
            registry=None,
            env_vars=self.env_vars
            + [f"{k}={v}" for k, v in (metadata.cloud_context_env or {}).items()],
            networks=self._networks,
            container_kwargs=self._container_kwargs,
        ).merge(DockerContainerContext.create_from_config(metadata.container_context))

        ports = {}

        has_network = len(self._networks) > 0
        if has_network:
            grpc_port = get_code_server_port()
            hostname = container_name
        else:
            grpc_port = find_free_port()
            ports[grpc_port] = grpc_port
            hostname = "localhost"

        if metadata.pex_metadata:
            command = metadata.get_multipex_server_command(
                grpc_port,
                metrics_enabled=self._instance.user_code_launcher.code_server_metrics_enabled,
            )
            environment = metadata.get_multipex_server_env()
            labels = {
                MULTIPEX_SERVER_LABEL: "",
                deterministic_label_for_location(deployment_name, location_name): "",
                AGENT_LABEL: self._instance.instance_uuid,
                SERVER_TIMESTAMP_LABEL: str(desired_entry.update_timestamp),
            }
        else:
            command = metadata.get_grpc_server_command(
                metrics_enabled=self._instance.user_code_launcher.code_server_metrics_enabled
            )
            environment = get_grpc_server_env(
                metadata,
                grpc_port,
                location_name,
                self._instance.ref_for_deployment(deployment_name),
            )
            labels = {
                GRPC_SERVER_LABEL: "",
                deterministic_label_for_location(deployment_name, location_name): "",
                AGENT_LABEL: self._instance.instance_uuid,
                SERVER_TIMESTAMP_LABEL: str(desired_entry.update_timestamp),
            }

        if "stop_timeout" in container_context.container_kwargs:
            labels[STOP_TIMEOUT_LABEL] = str(container_context.container_kwargs["stop_timeout"])

        container, server_endpoint = self._launch_container(
            deployment_name,
            location_name,
            container_name,
            hostname,
            grpc_port,
            ports,
            check.not_none(metadata.image),
            container_context,
            command,
            additional_env=environment,
            labels=labels,
        )

        return DagsterCloudGrpcServer(
            DagsterDockerContainer(container=container), server_endpoint, metadata
        )

    async def _wait_for_new_server_ready(  # ty: ignore[invalid-method-override], fix me!
        self,
        deployment_name: str,
        location_name: str,
        user_code_launcher_entry: UserCodeLauncherEntry,
        server_handle: DagsterDockerContainer,
        server_endpoint: ServerEndpoint,
    ) -> None:
        await self._wait_for_dagster_server_process(
            client=server_endpoint.create_client(),
            timeout=self._server_process_startup_timeout,
        )

    def _remove_server_handle(self, server_handle: DagsterDockerContainer) -> None:
        container = server_handle.container

        stop_timeout_str = server_handle.container.labels.get(STOP_TIMEOUT_LABEL)
        stop_timeout = int(stop_timeout_str) if stop_timeout_str else None

        try:
            container.stop(timeout=stop_timeout)
        except Exception:
            self._logger.error(f"Failure stopping container {container.id}: {sys.exc_info()}")
        container.remove(force=True)
        self._logger.info(f"Removed container {container.id}")

    def get_agent_id_for_server(self, handle: DagsterDockerContainer) -> str | None:
        return handle.container.labels.get(AGENT_LABEL)

    def get_server_create_timestamp(self, handle: DagsterDockerContainer) -> float | None:
        created_time_str = handle.container.attrs["Created"]  # ty: ignore[not-subscriptable]
        return parse(created_time_str).timestamp()

    def _list_server_handles(self) -> list[DagsterDockerContainer]:
        client = docker_client_from_env()
        return [
            DagsterDockerContainer(container=container)
            for container in client.containers.list(all=True, filters={"label": GRPC_SERVER_LABEL})
        ] + [
            DagsterDockerContainer(container=container)
            for container in client.containers.list(
                all=True, filters={"label": MULTIPEX_SERVER_LABEL}
            )
        ]

    def run_launcher(self):
        launcher = CloudDockerRunLauncher(
            image=None,
            env_vars=self.env_vars,
            networks=self._networks,
            container_kwargs=self._container_kwargs,
        )
        launcher.register_instance(self._instance)

        return launcher


class CloudDockerRunLauncher(DockerRunLauncher):
    def launch_run(self, context: LaunchRunContext) -> None:
        serialized_pex_metadata = context.dagster_run.tags.get(PEX_METADATA_TAG)

        if serialized_pex_metadata:
            run = context.dagster_run
            job_origin = check.not_none(run.job_code_origin)

            docker_image = self._get_docker_image(job_origin)

            run_args = ExecuteRunArgs(
                job_origin=job_origin,
                run_id=run.run_id,
                instance_ref=self._instance.get_ref(),
            )

            deserialize_value(serialized_pex_metadata, PexMetadata)
            command = [
                "dagster-cloud",
                "pex",
                "execute-run",
                serialize_value(run_args),
                serialized_pex_metadata,
            ]
            self._launch_container_with_command(run, docker_image, command)
        else:
            return super().launch_run(context)
