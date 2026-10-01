# ruff: noqa: SLF001
import asyncio
import logging
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock, create_autospec

import pytest
from azure.core.exceptions import HttpResponseError
from azure.mgmt.appcontainers.models import (
    Configuration,
    Container,
    ContainerApp,
    ContainerResources,
    Ingress,
    ManagedServiceIdentity,
    RegistryCredentials,
    Scale,
    SystemData,
)
from azure.mgmt.appcontainers.operations import (
    ContainerAppsOperations,
    JobsExecutionsOperations,
    JobsOperations,
    ManagedEnvironmentsOperations,
)
from dagster._check import CheckError
from dagster._core.test_utils import instance_for_test
from dagster._utils.merger import merge_dicts
from dagster_azure.container_apps import SHARED_ACA_SCHEMA, AcaRunLauncher
from dagster_cloud.api.dagster_cloud_api import UserCodeDeploymentType
from dagster_cloud.instance import DagsterCloudAgentInstance
from dagster_cloud.workspace.aca import launcher as aca_launcher_module
from dagster_cloud.workspace.aca.handle import AcaServerHandle
from dagster_cloud.workspace.aca.launcher import AcaCodeServerStartupError, AcaUserCodeLauncher
from dagster_cloud.workspace.aca.utils import ACA_NAME_MAX_LEN, unique_aca_resource_name
from dagster_cloud.workspace.config_schema.aca import SHARED_ACA_CONFIG
from dagster_cloud.workspace.user_code_launcher import (
    DEFAULT_SERVER_PROCESS_STARTUP_TIMEOUT,
    SHARED_USER_CODE_LAUNCHER_CONFIG,
    UserCodeLauncherEntry,
)
from dagster_cloud.workspace.user_code_launcher.utils import (
    deterministic_label_for_location,
    get_code_server_port,
    get_grpc_server_env,
)
from dagster_cloud_cli.core.workspace import CodeLocationDeployData

ENVIRONMENT_ID = (
    "/subscriptions/sub/resourceGroups/rg/providers/Microsoft.App/managedEnvironments/env"
)
IDENTITY_ID = (
    "/subscriptions/sub/resourceGroups/rg/providers"
    "/Microsoft.ManagedIdentity/userAssignedIdentities/agent"
)
ACR_IMAGE = "myacr.azurecr.io/user-code:1"
FQDN = "server-abc123.internal.happy-hill-1234.eastus.azurecontainerapps.io"
CREATED_AT = datetime(2026, 9, 14, 12, 0, tzinfo=timezone.utc)
DEPLOYMENT = "prod"
LOCATION = "my_location"


def _fake_client() -> MagicMock:
    """Stand-in for ContainerAppsAPIClient that only answers to real SDK attributes.

    The SDK attaches operation groups as instance attributes, so each group is
    autospecced separately and the client is pinned to exactly those names. A typo
    in an operation group or method name raises instead of returning a mock.
    """
    client = MagicMock(
        spec_set=["container_apps", "managed_environments", "jobs", "jobs_executions"]
    )
    client.container_apps = create_autospec(ContainerAppsOperations, instance=True)
    client.managed_environments = create_autospec(ManagedEnvironmentsOperations, instance=True)
    client.jobs = create_autospec(JobsOperations, instance=True)
    client.jobs_executions = create_autospec(JobsExecutionsOperations, instance=True)
    client.managed_environments.get.return_value = MagicMock(id=ENVIRONMENT_ID)
    return client


def _container_app(
    *,
    name: str = "server-abc123",
    fqdn: str | None = FQDN,
    tags: dict[str, str] | None = None,
    running_status: str | None = None,
    created_at: datetime | None = CREATED_AT,
) -> ContainerApp:
    """Build a ContainerApp the way Azure would return it, read-only fields included."""
    ingress = Ingress() if fqdn else None
    app = ContainerApp(location="eastus", tags=tags, configuration=Configuration(ingress=ingress))
    # These are server-populated and read-only in the model, so the constructors drop
    # them, but they are plain attributes in Python and can be set afterwards.
    if ingress is not None:
        ingress.fqdn = fqdn
    app.name = name
    app.running_status = running_status
    app.system_data = SystemData(created_at=created_at) if created_at else None
    return app


@contextmanager
def _aca_instance(
    user_code_launcher_overrides: dict[str, Any] | None = None,
) -> Iterator[tuple[DagsterCloudAgentInstance, AcaUserCodeLauncher, MagicMock]]:
    with instance_for_test(
        {
            "instance_class": {
                "module": "dagster_cloud",
                "class": "DagsterCloudAgentInstance",
            },
            "user_code_launcher": {
                "module": "dagster_cloud.workspace.aca.launcher",
                "class": "AcaUserCodeLauncher",
                "config": merge_dicts(
                    {
                        "subscription_id": "sub",
                        "resource_group": "rg",
                        "environment_name": "env",
                    },
                    user_code_launcher_overrides or {},
                ),
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
        assert isinstance(instance, DagsterCloudAgentInstance)
        launcher = instance.user_code_launcher
        assert isinstance(launcher, AcaUserCodeLauncher)
        client = _fake_client()
        # _get_aca_client returns this if already set, so no real credential is ever built.
        launcher._aca_client = client
        yield instance, launcher, client


def _entry(
    *,
    image: str | None = ACR_IMAGE,
    container_context: dict[str, Any] | None = None,
    cloud_context_env: dict[str, Any] | None = None,
    update_timestamp: float = 1_700_000_000.0,
) -> UserCodeLauncherEntry:
    return UserCodeLauncherEntry(
        code_location_deploy_data=CodeLocationDeployData(
            image=image,
            package_name="my_package",
            container_context=container_context or {},
            cloud_context_env=cloud_context_env or {},
        ),
        update_timestamp=update_timestamp,
    )


def _spin_up(
    launcher: AcaUserCodeLauncher,
    client: MagicMock,
    entry: UserCodeLauncherEntry,
    *,
    returned_app: ContainerApp | None = None,
):
    client.container_apps.begin_create_or_update.return_value.result.return_value = (
        returned_app if returned_app is not None else _container_app()
    )
    server = launcher._start_new_server_spinup(DEPLOYMENT, LOCATION, entry)
    (_, app_name, app_spec), _ = client.container_apps.begin_create_or_update.call_args
    assert isinstance(app_spec, ContainerApp)
    return server, app_name, app_spec


# Narrowing helpers: every field on the Azure models is Optional.
def _configuration(app: ContainerApp) -> Configuration:
    assert app.configuration is not None
    return app.configuration


def _ingress(app: ContainerApp) -> Ingress:
    ingress = _configuration(app).ingress
    assert ingress is not None
    return ingress


def _container(app: ContainerApp) -> Container:
    assert app.template is not None and app.template.containers is not None
    (container,) = app.template.containers
    return container


def _scale(app: ContainerApp) -> Scale:
    assert app.template is not None and app.template.scale is not None
    return app.template.scale


def _resources(app: ContainerApp) -> ContainerResources:
    resources = _container(app).resources
    assert resources is not None
    return resources


def _env(app: ContainerApp) -> dict[str | None, str | None]:
    env = _container(app).env
    assert env is not None
    return {e.name: e.value for e in env}


def _identity(app: ContainerApp) -> ManagedServiceIdentity:
    assert app.identity is not None
    return app.identity


def _registry(app: ContainerApp) -> RegistryCredentials:
    registries = _configuration(app).registries
    assert registries is not None
    (registry,) = registries
    return registry


class TestFakeClient:
    def test_rejects_unknown_sdk_attributes(self):
        client = _fake_client()
        with pytest.raises(AttributeError):
            client.container_app  # noqa: B018
        with pytest.raises(AttributeError):
            client.container_apps.create_or_update  # noqa: B018
        with pytest.raises(TypeError):
            client.container_apps.get("rg")  # missing container_app_name


class TestConfig:
    def test_config_type_composes_own_shared_aca_and_base_fields(self):
        schema = AcaUserCodeLauncher.config_type()
        for own in (
            "subscription_id",
            "resource_group",
            "environment_name",
            "region",
            "server_process_startup_timeout",
        ):
            assert own in schema, own
        assert set(SHARED_ACA_SCHEMA) <= set(schema)
        assert set(SHARED_USER_CODE_LAUNCHER_CONFIG) <= set(schema)

    def test_dagster_cloud_schema_mirror_matches_dagster_azure(self):
        """config_schema/aca.py redeclares the shared fields to avoid importing dagster-azure.
        Keep the two in lockstep so a field added on one side is not silently rejected on the other.
        """
        assert set(SHARED_ACA_CONFIG) == set(SHARED_ACA_SCHEMA)

    def test_default_instance(self):
        with _aca_instance() as (_, launcher, _):
            assert launcher.env_vars == []
            assert launcher.server_resources == {}
            assert launcher.run_resources == {}
            assert launcher._region == "eastus"
            assert launcher._identity_id is None
            assert (
                launcher._server_process_startup_timeout == DEFAULT_SERVER_PROCESS_STARTUP_TIMEOUT
            )
            assert launcher.requires_images is True
            assert launcher.user_code_deployment_type == UserCodeDeploymentType.ACA

    def test_overrides(self):
        with _aca_instance(
            {
                "region": "westeurope",
                "identity_id": IDENTITY_ID,
                "server_process_startup_timeout": 42,
                "env_vars": ["A=1"],
                "server_resources": {"cpu": "1", "memory": "2Gi"},
                "run_resources": {"cpu": "2", "memory": "4Gi"},
                "run_job_replica_timeout": 300,
                "agent_metrics": {"enabled": True},
                "code_server_metrics": {"enabled": True},
            }
        ) as (_, launcher, _):
            assert launcher.agent_metrics_enabled is True
            assert launcher.code_server_metrics_enabled is True
            assert launcher._region == "westeurope"
            assert launcher._identity_id == IDENTITY_ID
            assert launcher._server_process_startup_timeout == 42
            assert launcher.env_vars == ["A=1"]
            assert launcher.server_resources == {"cpu": "1", "memory": "2Gi"}
            assert launcher.run_resources == {"cpu": "2", "memory": "4Gi"}
            assert launcher._run_job_replica_timeout == 300


class TestClient:
    def test_client_creation_quiets_sdk_header_logging(self, monkeypatch):
        """azure.core logs every request/response header at INFO unless its logger is raised."""
        monkeypatch.setenv("AZURE_CLIENT_ID", "x")  # keep DefaultAzureCredential from probing
        sdk_logger = logging.getLogger("azure.core.pipeline.policies.http_logging_policy")
        sdk_logger.setLevel(logging.NOTSET)
        with _aca_instance() as (_, launcher, _):
            launcher._aca_client = None  # undo the fake so the real client path runs
            launcher._get_aca_client()
        assert sdk_logger.level == logging.WARNING


class TestNaming:
    def test_unique_name_fits_aca_limits_and_varies_per_call(self):
        first = unique_aca_resource_name("Prod_Deployment" * 4, "My.Location" * 4)
        second = unique_aca_resource_name("Prod_Deployment" * 4, "My.Location" * 4)
        for name in (first, second):
            assert 2 <= len(name) <= ACA_NAME_MAX_LEN
            assert name == name.lower()
            assert name.strip("-") == name
            assert all(c.isalnum() or c == "-" for c in name)
        assert first != second


class TestStartNewServerSpinup:
    def test_creates_container_app_and_returns_server(self):
        with _aca_instance() as (_, launcher, client):
            server, app_name, app_spec = _spin_up(launcher, client, _entry())

            client.managed_environments.get.assert_called_once_with("rg", "env")
            client.container_apps.begin_create_or_update.assert_called_once()
            (rg, _, _), _ = client.container_apps.begin_create_or_update.call_args
            assert rg == "rg"
            client.container_apps.begin_create_or_update.return_value.result.assert_called_once_with(
                timeout=180
            )

            # "<location>-<deployment>" sanitised for ACA, plus a 6-char uniqueness suffix.
            assert app_name.startswith("mylocation-prod-")
            assert len(app_name) == len("mylocation-prod-") + 6 <= ACA_NAME_MAX_LEN
            assert app_spec.location == "eastus"
            assert app_spec.managed_environment_id == ENVIRONMENT_ID

            handle = server.server_handle
            assert isinstance(handle, AcaServerHandle)
            assert handle.app_name == app_name
            assert handle.hostname == FQDN
            assert handle.create_timestamp == CREATED_AT.timestamp()
            # The agent dials the ingress on port 80 (h2c), not the container's target port.
            assert server.server_endpoint.host == FQDN
            assert server.server_endpoint.port == 80
            assert server.server_endpoint.socket is None

    def test_ingress_is_internal_http2_to_code_server_port(self):
        with _aca_instance() as (_, launcher, client):
            _, _, app_spec = _spin_up(launcher, client, _entry())
            ingress = _ingress(app_spec)
            assert ingress.external is False
            assert ingress.target_port == get_code_server_port()
            assert ingress.transport == "http2"
            assert ingress.allow_insecure is True
            assert _configuration(app_spec).active_revisions_mode == "Single"
            scale = _scale(app_spec)
            assert (scale.min_replicas, scale.max_replicas) == (1, 1)

    def test_container_runs_grpc_server_with_expected_env(self):
        with _aca_instance() as (instance, launcher, client):
            entry = _entry()
            _, _, app_spec = _spin_up(launcher, client, entry)
            container = _container(app_spec)
            metadata = entry.code_location_deploy_data

            assert container.name == "server"
            assert container.image == ACR_IMAGE
            assert container.command == metadata.get_grpc_server_command()
            expected_env = get_grpc_server_env(
                metadata,
                get_code_server_port(),
                LOCATION,
                instance.ref_for_deployment(DEPLOYMENT),
            )
            assert _env(app_spec) == {k: str(v) for k, v in expected_env.items()}

    def test_default_resources(self):
        with _aca_instance() as (_, launcher, client):
            _, _, app_spec = _spin_up(launcher, client, _entry())
            assert _resources(app_spec).cpu == 0.5
            assert _resources(app_spec).memory == "2.0Gi"

    def test_launcher_and_location_config_merge_into_container(self):
        with _aca_instance(
            {
                "env_vars": ["FROM_LAUNCHER=1"],
                "server_resources": {"cpu": "500m", "memory": "1Gi"},
            }
        ) as (_, launcher, client):
            entry = _entry(
                cloud_context_env={"FROM_CLOUD": "1"},
                container_context={
                    "aca": {
                        "env_vars": ["FROM_LOCATION=1"],
                        "server_resources": {"memory": "4Gi"},
                    }
                },
            )
            _, _, app_spec = _spin_up(launcher, client, entry)
            env = _env(app_spec)
            assert env["FROM_LAUNCHER"] == "1"
            assert env["FROM_CLOUD"] == "1"
            assert env["FROM_LOCATION"] == "1"
            # millicpu string is normalised; memory is overridden per key by the location.
            assert _resources(app_spec).cpu == 0.5
            assert _resources(app_spec).memory == "4Gi"

    def test_identity_and_acr_registry(self):
        with _aca_instance({"identity_id": IDENTITY_ID}) as (_, launcher, client):
            _, _, app_spec = _spin_up(launcher, client, _entry())
            identity = _identity(app_spec)
            assert identity.type == "UserAssigned"
            assert identity.user_assigned_identities is not None
            assert set(identity.user_assigned_identities) == {IDENTITY_ID}
            registry = _registry(app_spec)
            assert registry.server == "myacr.azurecr.io"
            assert registry.identity == IDENTITY_ID

    def test_no_identity_means_no_identity_or_registry_blocks(self):
        with _aca_instance() as (_, launcher, client):
            _, _, app_spec = _spin_up(launcher, client, _entry())
            assert app_spec.identity is None
            assert _configuration(app_spec).registries is None

    def test_tags_let_the_agent_find_its_own_servers(self):
        with _aca_instance() as (instance, launcher, client):
            _, _, app_spec = _spin_up(launcher, client, _entry(update_timestamp=123.0))
            assert app_spec.tags == {
                "dagster-deployment": DEPLOYMENT,
                "dagster-location": "mylocation",  # underscores are not legal in ACA names
                "dagster-location-hash": deterministic_label_for_location(DEPLOYMENT, LOCATION),
                "dagster-agent-id": instance.instance_uuid,
                "managed-by": "dagster-cloud-agent",
                "dagster-grpc-server": "1",
                "dagster-server-timestamp": "123.0",
            }

    def test_missing_image_fails_before_creating_anything(self):
        with _aca_instance() as (_, launcher, client):
            with pytest.raises(CheckError, match="no container image"):
                launcher._start_new_server_spinup(DEPLOYMENT, LOCATION, _entry(image=None))
            client.container_apps.begin_create_or_update.assert_not_called()

    def test_failed_create_deletes_the_partial_app_and_reraises(self):
        with _aca_instance() as (_, launcher, client):
            client.container_apps.begin_create_or_update.return_value.result.side_effect = (
                RuntimeError("ContainerAppOperationError: failed to resolve registry")
            )
            with pytest.raises(RuntimeError, match="failed to resolve registry"):
                launcher._start_new_server_spinup(DEPLOYMENT, LOCATION, _entry())
            (_, app_name, _), _ = client.container_apps.begin_create_or_update.call_args
            client.container_apps.begin_delete.assert_called_once_with("rg", app_name)

    def test_cleanup_failure_from_azure_does_not_mask_the_create_error(self):
        with _aca_instance() as (_, launcher, client):
            client.container_apps.begin_create_or_update.return_value.result.side_effect = (
                RuntimeError("create failed")
            )
            client.container_apps.begin_delete.side_effect = HttpResponseError("delete failed")
            with pytest.raises(RuntimeError, match="create failed"):
                launcher._start_new_server_spinup(DEPLOYMENT, LOCATION, _entry())
            client.container_apps.begin_delete.assert_called_once()

    def test_unexpected_cleanup_failure_is_not_swallowed(self):
        with _aca_instance() as (_, launcher, client):
            client.container_apps.begin_create_or_update.return_value.result.side_effect = (
                RuntimeError("create failed")
            )
            client.container_apps.begin_delete.side_effect = TypeError("bug in cleanup")
            with pytest.raises(TypeError, match="bug in cleanup"):
                launcher._start_new_server_spinup(DEPLOYMENT, LOCATION, _entry())

    def test_app_without_fqdn_is_an_error(self):
        with _aca_instance() as (_, launcher, client):
            with pytest.raises(CheckError, match="no ingress FQDN"):
                _spin_up(launcher, client, _entry(), returned_app=_container_app(fqdn=None))


class TestServerHandles:
    def _apps(self, instance: DagsterCloudAgentInstance) -> list[ContainerApp]:
        location_hash = deterministic_label_for_location(DEPLOYMENT, LOCATION)
        mine = {
            "dagster-location": "mylocation",
            "dagster-location-hash": location_hash,
            "dagster-agent-id": instance.instance_uuid,
        }
        return [
            _container_app(name="grpc-mine", tags={**mine, "dagster-grpc-server": "1"}),
            _container_app(name="pex-mine", tags={**mine, "dagster-multipex-server": "1"}),
            _container_app(
                name="grpc-other-agent",
                tags={**mine, "dagster-grpc-server": "1", "dagster-agent-id": "someone-else"},
            ),
            _container_app(
                name="grpc-other-location",
                tags={**mine, "dagster-grpc-server": "1", "dagster-location-hash": "nope"},
            ),
            _container_app(name="untagged", tags={}),
            _container_app(name="no-fqdn", tags={**mine, "dagster-grpc-server": "1"}, fqdn=None),
        ]

    def test_list_server_handles_skips_apps_without_dagster_tags_or_fqdn(self):
        with _aca_instance() as (instance, launcher, client):
            client.container_apps.list_by_resource_group.return_value = self._apps(instance)
            handles = launcher._list_server_handles()
            client.container_apps.list_by_resource_group.assert_called_once_with("rg")
            assert {h.app_name for h in handles} == {
                "grpc-mine",
                "pex-mine",
                "grpc-other-agent",
                "grpc-other-location",
            }
            grpc_mine = next(h for h in handles if h.app_name == "grpc-mine")
            assert grpc_mine.hostname == FQDN
            assert grpc_mine.create_timestamp == CREATED_AT.timestamp()
            assert launcher.get_server_create_timestamp(grpc_mine) == CREATED_AT.timestamp()
            assert launcher.get_agent_id_for_server(grpc_mine) == instance.instance_uuid

    def test_handles_for_location_filter_by_hash_kind_and_agent(self):
        with _aca_instance() as (instance, launcher, client):
            client.container_apps.list_by_resource_group.return_value = self._apps(instance)
            standalone = launcher._get_standalone_dagster_server_handles_for_location(
                DEPLOYMENT, LOCATION
            )
            assert [h.app_name for h in standalone] == ["grpc-mine"]
            multipex = launcher._get_multipex_server_handles_for_location(DEPLOYMENT, LOCATION)
            assert [h.app_name for h in multipex] == ["pex-mine"]

    def test_remove_server_handle_deletes_the_app(self):
        with _aca_instance() as (_, launcher, client):
            handle = AcaServerHandle(
                app_name="grpc-mine", hostname=FQDN, tags={}, create_timestamp=None
            )
            launcher._remove_server_handle(handle)
            client.container_apps.begin_delete.assert_called_once_with("rg", "grpc-mine")


class TestPollUntilRunning:
    @pytest.fixture(autouse=True)
    def _no_sleep(self, monkeypatch):
        monkeypatch.setattr(aca_launcher_module, "_DEFAULT_SERVER_POLL_INTERVAL_SECS", 0)

    def test_returns_once_running(self):
        with _aca_instance() as (_, launcher, client):
            client.container_apps.get.side_effect = [
                _container_app(running_status="Provisioning"),
                _container_app(running_status="Running"),
            ]
            asyncio.run(launcher._poll_until_running("app"))
            assert client.container_apps.get.call_count == 2
            client.container_apps.get.assert_called_with("rg", "app")

    def test_logs_each_status_change_once(self, caplog):
        with _aca_instance() as (_, launcher, client):
            client.container_apps.get.side_effect = [
                _container_app(running_status="Provisioning"),
                _container_app(running_status="Provisioning"),
                _container_app(running_status="Provisioning"),
                _container_app(running_status="Running"),
            ]
            with caplog.at_level(logging.INFO):
                asyncio.run(launcher._poll_until_running("app"))
        status_lines = [m for m in caplog.messages if "status:" in m]
        assert status_lines == [
            "Container App 'app' status: 'Provisioning'",
            "Container App 'app' status: 'Running'",
        ]
        assert any("is running after" in m for m in caplog.messages)

    @pytest.mark.parametrize("status", ["Stopped", "Failed", "Degraded"])
    def test_terminal_status_raises(self, status):
        with _aca_instance() as (_, launcher, client):
            client.container_apps.get.return_value = _container_app(running_status=status)
            with pytest.raises(AcaCodeServerStartupError, match=status):
                asyncio.run(launcher._poll_until_running("app"))

    def test_times_out(self, monkeypatch):
        monkeypatch.setattr(aca_launcher_module, "_DEFAULT_SERVER_STARTUP_TIMEOUT_SECS", 0)
        with _aca_instance() as (_, launcher, client):
            client.container_apps.get.return_value = _container_app(running_status="Provisioning")
            with pytest.raises(AcaCodeServerStartupError, match="Timed out"):
                asyncio.run(launcher._poll_until_running("app"))

    def test_assert_app_not_stopped(self):
        with _aca_instance() as (_, launcher, client):
            client.container_apps.get.return_value = _container_app(running_status="Running")
            launcher._assert_app_not_stopped("app")
            client.container_apps.get.return_value = _container_app(running_status="Stopped")
            with pytest.raises(AcaCodeServerStartupError, match="Stopped"):
                launcher._assert_app_not_stopped("app")


class TestRunLauncher:
    def test_run_launcher_mirrors_user_code_launcher_config(self):
        with _aca_instance(
            {
                "region": "westeurope",
                "identity_id": IDENTITY_ID,
                "env_vars": ["A=1"],
                "run_resources": {"cpu": "2", "memory": "4Gi"},
                "run_job_replica_timeout": 300,
            }
        ) as (instance, launcher, client):
            run_launcher = launcher.run_launcher()
            assert isinstance(run_launcher, AcaRunLauncher)
            client.managed_environments.get.assert_called_once_with("rg", "env")
            assert run_launcher._environment_id == ENVIRONMENT_ID
            assert run_launcher._resource_group == "rg"
            assert run_launcher._region == "westeurope"
            assert run_launcher.identity_id == IDENTITY_ID
            assert list(run_launcher.env_vars) == ["A=1"]
            assert run_launcher.run_resources == {"cpu": "2", "memory": "4Gi"}
            assert run_launcher.run_job_replica_timeout == 300
            assert run_launcher._instance is instance

    def test_code_server_resource_limits_come_from_location_container_context(self):
        with _aca_instance() as (_, launcher, _):
            launcher._actual_entries[(DEPLOYMENT, LOCATION)] = _entry(
                container_context={"aca": {"server_resources": {"cpu": "1", "memory": "2Gi"}}}
            )
            assert launcher.get_code_server_resource_limits(DEPLOYMENT, LOCATION) == {
                "aca": {"cpu_limit": "1", "memory_limit": "2Gi"}
            }
