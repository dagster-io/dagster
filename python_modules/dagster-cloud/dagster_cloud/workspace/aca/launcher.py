import asyncio
import logging
import time
from typing import TYPE_CHECKING, Any

import dagster._check as check
from dagster import Field, IntSource, StringSource
from dagster._annotations import beta
from dagster._serdes import ConfigurableClass, ConfigurableClassData
from dagster._utils.merger import merge_dicts

from dagster_cloud.api.dagster_cloud_api import UserCodeDeploymentType
from dagster_cloud.workspace.aca.handle import AcaServerHandle
from dagster_cloud.workspace.aca.utils import get_aca_human_readable_label, unique_aca_resource_name
from dagster_cloud.workspace.user_code_launcher import (
    DEFAULT_SERVER_PROCESS_STARTUP_TIMEOUT,
    SHARED_USER_CODE_LAUNCHER_CONFIG,
    DagsterCloudGrpcServer,
    DagsterCloudUserCodeLauncher,
    ServerEndpoint,
)
from dagster_cloud.workspace.user_code_launcher.user_code_launcher import (
    UserCodeLauncherEntry,
    async_serialize_exceptions,
)
from dagster_cloud.workspace.user_code_launcher.utils import (
    deterministic_label_for_location,
    get_code_server_port,
    get_grpc_server_env,
)

try:
    from azure.core.exceptions import AzureError
    from azure.identity import DefaultAzureCredential
    from azure.mgmt.appcontainers import ContainerAppsAPIClient
    from azure.mgmt.appcontainers.models import (
        Configuration,
        Container,
        ContainerApp,
        ContainerResources,
        EnvironmentVar,
        Ingress,
        ManagedServiceIdentity,
        Scale,
        Template,
        UserAssignedIdentity,
    )
    from dagster_azure.container_apps import SHARED_ACA_SCHEMA, AcaContainerContext, AcaRunLauncher
    from dagster_azure.container_apps.resources import interpret_aca_cpu_str_as_millicpus
    from dagster_azure.container_apps.utils import build_acr_registry_credentials
except ImportError as e:
    raise ImportError(
        "The Azure Container Apps agent requires the `aca` extra. "
        "Install it with `pip install dagster-cloud[aca]`."
    ) from e

if TYPE_CHECKING:
    from collections.abc import Collection, Mapping

    from dagster_cloud_cli.core.workspace import CodeLocationDeployData

    from dagster_cloud.execution.monitoring import CloudContainerResourceLimits

# Internal http2 ingress is reached on port 80; Azure proxies it to the container's target port.
_ACA_INGRESS_H2C_PORT = 80
_DEFAULT_SERVER_POLL_INTERVAL_SECS = 5
_DEFAULT_SERVER_STARTUP_TIMEOUT_SECS = 180


class AcaCodeServerStartupError(Exception):
    """Raised when a code server Container App fails to reach Running status."""


@beta
class AcaUserCodeLauncher(DagsterCloudUserCodeLauncher[AcaServerHandle], ConfigurableClass):
    """Runs each code location as a Container App and each run as a Container Apps Job."""

    def __init__(
        self,
        *,
        inst_data: ConfigurableClassData | None,
        subscription_id: str,
        resource_group: str,
        environment_name: str,
        region: str = "eastus",
        env_vars: list[str] | None = None,
        server_resources: dict[str, Any] | None = None,
        run_resources: dict[str, Any] | None = None,
        identity_id: str | None = None,
        run_job_replica_timeout: int | None = None,
        **kwargs,
    ):
        self._subscription_id = subscription_id
        self._resource_group = resource_group
        self._environment_name = environment_name
        self._region = region
        self.env_vars = check.opt_list_param(env_vars, "env_vars")
        self.server_resources = check.opt_mapping_param(server_resources, "server_resources")
        self.run_resources = check.opt_mapping_param(run_resources, "run_resources")
        self._identity_id = identity_id
        self._run_job_replica_timeout = run_job_replica_timeout
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)

        self._aca_client: ContainerAppsAPIClient | None = None
        self._environment_id: str | None = None

        super().__init__(**kwargs)

    def _get_aca_client(self) -> ContainerAppsAPIClient:
        if self._aca_client is None:
            # The SDK logs every request and response header at INFO, which drowns the agent log.
            logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(
                logging.WARNING
            )
            self._aca_client = ContainerAppsAPIClient(
                DefaultAzureCredential(), self._subscription_id
            )
        return self._aca_client

    def _get_environment_id(self) -> str:
        if self._environment_id is None:
            client = self._get_aca_client()
            env = client.managed_environments.get(self._resource_group, self._environment_name)
            self._environment_id = check.not_none(env.id, "ACA environment has no id")
        return self._environment_id

    @classmethod
    def config_type(cls):
        return merge_dicts(
            {
                "subscription_id": Field(
                    StringSource,
                    description="Azure subscription ID.",
                ),
                "resource_group": Field(
                    StringSource,
                    description="Azure resource group containing the ACA environment.",
                ),
                "environment_name": Field(
                    StringSource,
                    description="Name of the Azure Container Apps managed environment.",
                ),
                "region": Field(
                    StringSource,
                    is_required=False,
                    default_value="eastus",
                    description="Azure region for Container Apps (e.g. 'eastus', 'westeurope').",
                ),
                "server_process_startup_timeout": Field(
                    IntSource,
                    is_required=False,
                    default_value=DEFAULT_SERVER_PROCESS_STARTUP_TIMEOUT,
                    description=(
                        "Timeout (seconds) when waiting for a code server gRPC process to become "
                        "ready after its Container App starts."
                    ),
                ),
                "code_server_metrics": Field(
                    {"enabled": Field(bool, is_required=False, default_value=False)},
                    is_required=False,
                ),
                "agent_metrics": Field(
                    {"enabled": Field(bool, is_required=False, default_value=False)},
                    is_required=False,
                ),
            },
            SHARED_ACA_SCHEMA,
            SHARED_USER_CODE_LAUNCHER_CONFIG,
        )

    @classmethod
    def from_config_value(cls, inst_data: ConfigurableClassData, config_value: "Mapping[str, Any]"):
        return cls(inst_data=inst_data, **config_value)

    @property
    def inst_data(self) -> ConfigurableClassData | None:
        return self._inst_data

    @property
    def requires_images(self) -> bool:
        return True

    @property
    def user_code_deployment_type(self) -> UserCodeDeploymentType:
        return UserCodeDeploymentType.ACA

    def _server_app_name(self, deployment_name: str, location_name: str) -> str:
        # A new name per spin-up lets the reconciler run the new server beside the old one.
        return unique_aca_resource_name(deployment_name, location_name)

    def _dagster_tags(
        self, deployment_name: str, location_name: str, extra: dict[str, str] | None
    ) -> dict[str, str]:
        tags = {
            "dagster-deployment": get_aca_human_readable_label(deployment_name),
            "dagster-location": get_aca_human_readable_label(location_name),
            "dagster-location-hash": deterministic_label_for_location(
                deployment_name, location_name
            ),
            "dagster-agent-id": self._instance.instance_uuid,
            "managed-by": "dagster-cloud-agent",
        }
        if extra:
            tags.update(extra)
        return tags

    def _build_registries(self, image: str):
        return build_acr_registry_credentials(self._identity_id, image) or []

    def _build_identity(self):
        if self._identity_id:
            return ManagedServiceIdentity(
                type="UserAssigned",
                user_assigned_identities={self._identity_id: UserAssignedIdentity()},
            )
        return None

    def _start_new_server_spinup(
        self,
        deployment_name: str,
        location_name: str,
        desired_entry: UserCodeLauncherEntry,
    ) -> DagsterCloudGrpcServer:
        metadata = desired_entry.code_location_deploy_data
        app_name = self._server_app_name(deployment_name, location_name)
        tags, container_app = self._build_container_app(
            deployment_name, location_name, desired_entry
        )

        self._logger.info(
            f"Creating code server Container App {app_name!r} for {deployment_name}:{location_name}"
        )
        app = self._create_container_app(app_name, container_app)

        # Azure assigns the hostname; for internal ingress it includes an "internal." segment.
        hostname = check.not_none(
            app.configuration.ingress.fqdn
            if app.configuration and app.configuration.ingress
            else None,
            f"Container App {app_name!r} has no ingress FQDN",
        )
        create_timestamp = (
            app.system_data.created_at.timestamp()
            if app.system_data and app.system_data.created_at
            else None
        )
        handle = AcaServerHandle(
            app_name=app_name,
            hostname=hostname,
            tags=tags,
            create_timestamp=create_timestamp,
        )
        endpoint = ServerEndpoint(host=hostname, port=_ACA_INGRESS_H2C_PORT, socket=None)

        self._logger.info(
            f"Created code server {app_name!r} at {hostname} for {deployment_name}:{location_name}"
        )
        return DagsterCloudGrpcServer(handle, endpoint, metadata)

    def _server_command_and_env(
        self, deployment_name: str, location_name: str, metadata: "CodeLocationDeployData"
    ) -> tuple[list[str], dict[str, str], str]:
        """Return the container command, the env it needs, and the tag naming the server kind."""
        metrics_enabled = self._instance.user_code_launcher.code_server_metrics_enabled
        if metadata.pex_metadata:
            command = metadata.get_multipex_server_command(
                get_code_server_port(), metrics_enabled=metrics_enabled
            )
            return command, metadata.get_multipex_server_env(), "dagster-multipex-server"
        command = metadata.get_grpc_server_command(metrics_enabled=metrics_enabled)
        env = get_grpc_server_env(
            metadata,
            get_code_server_port(),
            location_name,
            self._instance.ref_for_deployment(deployment_name),
        )
        return command, env, "dagster-grpc-server"

    def _server_container_context(self, metadata: "CodeLocationDeployData") -> AcaContainerContext:
        """Agent-level settings layered under the code location's own `aca` block."""
        return AcaContainerContext(
            env_vars=[
                *self.env_vars,
                *(f"{k}={v}" for k, v in (metadata.cloud_context_env or {}).items()),
            ],
            server_resources=dict(self.server_resources),
            run_resources=dict(self.run_resources),
            identity_id=self._identity_id,
            run_job_replica_timeout=self._run_job_replica_timeout,
        ).merge(AcaContainerContext.create_from_config(metadata.container_context))

    def _server_resources(self, container_context: AcaContainerContext) -> ContainerResources:
        resources = container_context.server_resources
        cpu_millis = interpret_aca_cpu_str_as_millicpus(str(resources.get("cpu", "0.5")))
        cpu = (cpu_millis / 1000) if cpu_millis is not None else 0.5
        return ContainerResources(cpu=cpu, memory=resources.get("memory", "2.0Gi"))

    def _build_container_app(
        self,
        deployment_name: str,
        location_name: str,
        desired_entry: UserCodeLauncherEntry,
    ) -> tuple[dict[str, str], ContainerApp]:
        """Assemble the Container App for a code location; returns its tags and the spec."""
        metadata = desired_entry.code_location_deploy_data
        command, additional_env, server_tag = self._server_command_and_env(
            deployment_name, location_name, metadata
        )
        container_context = self._server_container_context(metadata)
        env_dict = merge_dicts(container_context.get_environment_dict(), additional_env)

        image = check.not_none(
            self._resolve_image(metadata),
            f"Code location {location_name!r} has no container image (requires_images=True).",
        )
        if image != metadata.image:
            self._logger.info("Resolved image to %r", image)

        tags = self._dagster_tags(
            deployment_name,
            location_name,
            extra={
                server_tag: "1",
                "dagster-server-timestamp": str(desired_entry.update_timestamp),
            },
        )
        container_app = ContainerApp(
            location=self._region,
            managed_environment_id=self._get_environment_id(),
            identity=self._build_identity(),
            configuration=Configuration(
                ingress=Ingress(
                    external=False,
                    target_port=get_code_server_port(),
                    transport="http2",
                    allow_insecure=True,
                ),
                registries=self._build_registries(image) or None,
                active_revisions_mode="Single",
            ),
            template=Template(
                containers=[
                    Container(
                        name="server",
                        image=image,
                        resources=self._server_resources(container_context),
                        env=[EnvironmentVar(name=k, value=str(v)) for k, v in env_dict.items()],
                        command=command,
                    )
                ],
                scale=Scale(min_replicas=1, max_replicas=1, rules=[]),
            ),
            tags=tags,
        )
        return tags, container_app

    def _create_container_app(self, app_name: str, container_app: ContainerApp) -> ContainerApp:
        """Create the app and wait for Azure to accept it, removing the remains if it does not."""
        client = self._get_aca_client()
        poller = client.container_apps.begin_create_or_update(
            self._resource_group, app_name, container_app
        )
        try:
            return poller.result(timeout=_DEFAULT_SERVER_STARTUP_TIMEOUT_SECS)
        except Exception:
            # A failed create can leave a Container App behind with no handle to clean it up later.
            self._logger.warning(
                f"Creating Container App {app_name!r} failed; deleting the partial resource"
            )
            try:
                client.container_apps.begin_delete(self._resource_group, app_name)
            except AzureError:
                self._logger.exception(f"Could not delete failed Container App {app_name!r}")
            raise

    @async_serialize_exceptions
    async def _wait_for_new_server_ready(
        self,
        deployment_name: str,
        location_name: str,
        desired_entry: UserCodeLauncherEntry,
        server_handle: AcaServerHandle,
        server_endpoint: ServerEndpoint,
    ) -> None:
        self._logger.info(f"Waiting for Container App {server_handle.app_name!r} to be ready...")
        await self._poll_until_running(server_handle.app_name)
        await self._wait_for_dagster_server_process(
            client=server_endpoint.create_client(),
            timeout=self._server_process_startup_timeout,
            additional_check=lambda: self._assert_app_not_stopped(server_handle.app_name),
        )

    async def _poll_until_running(self, app_name: str) -> None:
        client = self._get_aca_client()
        started = time.monotonic()
        deadline = started + _DEFAULT_SERVER_STARTUP_TIMEOUT_SECS
        loop = asyncio.get_running_loop()
        last_status = None
        while True:
            app = await loop.run_in_executor(
                None,
                lambda: client.container_apps.get(self._resource_group, app_name),
            )
            status = app.running_status
            if status != last_status:
                self._logger.info(f"Container App {app_name!r} status: {status!r}")
                last_status = status
            if status == "Running":
                self._logger.info(
                    f"Container App {app_name!r} is running after {time.monotonic() - started:.0f}s"
                )
                return
            if status in ("Stopped", "Failed", "Degraded"):
                raise AcaCodeServerStartupError(
                    f"Container App {app_name!r} entered status {status!r} instead of Running."
                )
            if time.monotonic() > deadline:
                raise AcaCodeServerStartupError(
                    f"Timed out waiting for Container App {app_name!r} to reach Running status "
                    f"(last status: {status!r})."
                )
            await asyncio.sleep(_DEFAULT_SERVER_POLL_INTERVAL_SECS)

    def _assert_app_not_stopped(self, app_name: str) -> None:
        client = self._get_aca_client()
        app = client.container_apps.get(self._resource_group, app_name)
        status = app.running_status
        if status in ("Stopped", "Failed", "Degraded"):
            raise AcaCodeServerStartupError(
                f"Container App {app_name!r} unexpectedly stopped (status: {status!r})."
            )

    def _remove_server_handle(self, server_handle: AcaServerHandle) -> None:
        self._logger.info(f"Deleting Container App {server_handle.app_name!r}...")
        self._get_aca_client().container_apps.begin_delete(
            self._resource_group, server_handle.app_name
        )

    def _handle_for_app(self, app) -> AcaServerHandle | None:
        tags = app.tags or {}
        if "dagster-location" not in tags:
            return None
        fqdn = (
            app.configuration.ingress.fqdn
            if app.configuration and app.configuration.ingress
            else None
        )
        if not fqdn:
            return None
        created_at = app.system_data.created_at if app.system_data else None
        return AcaServerHandle(
            app_name=app.name,
            hostname=fqdn,
            tags=dict(tags),
            create_timestamp=created_at.timestamp() if created_at else None,
        )

    def _list_server_handles(self) -> list[AcaServerHandle]:
        client = self._get_aca_client()
        handles = []
        for app in client.container_apps.list_by_resource_group(self._resource_group):
            handle = self._handle_for_app(app)
            if handle is not None:
                handles.append(handle)
        return handles

    def _get_standalone_dagster_server_handles_for_location(
        self, deployment_name: str, location_name: str
    ) -> "Collection[AcaServerHandle]":
        location_hash = deterministic_label_for_location(deployment_name, location_name)
        return [
            h
            for h in self._list_server_handles()
            if h.tags.get("dagster-location-hash") == location_hash
            and "dagster-grpc-server" in h.tags
            and h.tags.get("dagster-agent-id") == self._instance.instance_uuid
        ]

    def _get_multipex_server_handles_for_location(
        self, deployment_name: str, location_name: str
    ) -> "Collection[AcaServerHandle]":
        location_hash = deterministic_label_for_location(deployment_name, location_name)
        return [
            h
            for h in self._list_server_handles()
            if h.tags.get("dagster-location-hash") == location_hash
            and "dagster-multipex-server" in h.tags
            and h.tags.get("dagster-agent-id") == self._instance.instance_uuid
        ]

    def get_agent_id_for_server(self, handle: AcaServerHandle) -> str | None:
        return handle.tags.get("dagster-agent-id")

    def get_server_create_timestamp(self, handle: AcaServerHandle) -> float | None:
        return handle.create_timestamp

    def get_code_server_resource_limits(
        self, deployment_name: str, location_name: str
    ) -> "CloudContainerResourceLimits":
        metadata = self._actual_entries[(deployment_name, location_name)].code_location_deploy_data
        resources = (metadata.container_context or {}).get("aca", {}).get("server_resources", {})
        return {
            "aca": {
                "cpu_limit": resources.get("cpu"),
                "memory_limit": resources.get("memory"),
            }
        }

    def run_launcher(self) -> AcaRunLauncher:
        launcher = AcaRunLauncher(
            inst_data=None,
            subscription_id=self._subscription_id,
            resource_group=self._resource_group,
            region=self._region,
            environment_id=self._get_environment_id(),
            env_vars=list(self.env_vars),
            run_resources=dict(self.run_resources),
            identity_id=self._identity_id,
            run_job_replica_timeout=self._run_job_replica_timeout,
        )
        launcher.register_instance(self._instance)
        return launcher
