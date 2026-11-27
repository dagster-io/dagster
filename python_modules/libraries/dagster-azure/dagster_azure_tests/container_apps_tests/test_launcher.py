from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock, create_autospec, patch

import pytest
from azure.mgmt.appcontainers.models import (
    Container,
    ContainerResources,
    Job,
    JobConfiguration,
    JobExecutionRunningState,
    ManagedServiceIdentity,
    ManagedServiceIdentityType,
    RegistryCredentials,
)
from azure.mgmt.appcontainers.operations import JobsExecutionsOperations, JobsOperations
from dagster import DagsterInstance, job, op, reconstructable
from dagster._check import CheckError
from dagster._core.events import DagsterEventType
from dagster._core.launcher import LaunchRunContext
from dagster._core.launcher.base import WorkerStatus
from dagster._core.origin import JobPythonOrigin
from dagster._core.remote_representation.handle import RepositoryHandle
from dagster._core.storage.dagster_run import DagsterRun
from dagster._core.test_utils import (
    create_run_for_test,
    in_process_test_workspace,
    instance_for_test,
)
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._grpc.types import ExecuteRunArgs
from dagster._utils.hosted_user_process import remote_job_from_recon_job
from dagster_azure.container_apps.launcher import AcaRunLauncher
from dagster_azure.container_apps.utils import sanitize_aca_name

JOB_NAME_TAG = "azure/container_apps/job_name"
ENVIRONMENT_ID = (
    "/subscriptions/sub/resourceGroups/rg/providers/Microsoft.App/managedEnvironments/env"
)
IDENTITY_ID = (
    "/subscriptions/sub/resourceGroups/rg/providers"
    "/Microsoft.ManagedIdentity/userAssignedIdentities/agent"
)
ACR_IMAGE = "myacr.azurecr.io/user-code:1"


def _make_launcher(**overrides: Any) -> AcaRunLauncher:
    kwargs: dict[str, Any] = dict(
        inst_data=None,
        subscription_id="sub",
        resource_group="rg",
        region="eastus",
        environment_id=ENVIRONMENT_ID,
        env_vars=None,
        run_resources=None,
        identity_id=None,
        run_job_replica_timeout=None,
    )
    kwargs.update(overrides)
    return AcaRunLauncher(**kwargs)


@pytest.fixture
def launcher() -> AcaRunLauncher:
    return _make_launcher()


def _fake_client() -> MagicMock:
    """A stand-in for ContainerAppsAPIClient whose surface matches the real SDK.

    The SDK client attaches its operation groups as instance attributes, so a plain
    autospec of the client class would not know about them. Instead we autospec each
    operation group the launcher uses and pin the client to exactly those attributes,
    so that a misspelled operation group or method (for example ``client.job_execution``
    instead of ``client.jobs_executions``) raises instead of silently returning a mock.
    """
    client = MagicMock(spec_set=["jobs", "jobs_executions"])
    client.jobs = create_autospec(JobsOperations, instance=True)
    client.jobs_executions = create_autospec(JobsExecutionsOperations, instance=True)
    return client


def _mk_execution(status: str, start_time: int | datetime = 0):
    exec_mock = MagicMock()
    exec_mock.status = status
    exec_mock.start_time = start_time
    exec_mock.name = "exec"
    return exec_mock


def _mk_run(*, job_name: str | None = None):
    run = MagicMock()
    run.tags = {}
    if job_name:
        run.tags[JOB_NAME_TAG] = job_name
    return run


@op
def noop_op() -> None:
    pass


@job
def fake_job() -> None:
    noop_op()


def _python_origin(
    *, image: str | None, container_context: dict[str, Any] | None = None
) -> JobPythonOrigin:
    origin = reconstructable(fake_job).get_python_origin()
    return origin._replace(
        repository_origin=origin.repository_origin._replace(
            container_image=image,
            container_context=container_context or {},
        )
    )


# Narrowing helpers: the Azure models declare every field Optional, so pull the
# pieces we assert on through one place that checks they were actually set.
def _config(job_obj: Job) -> JobConfiguration:
    assert job_obj.configuration is not None
    return job_obj.configuration


def _container(job_obj: Job) -> Container:
    assert job_obj.template is not None and job_obj.template.containers is not None
    (container,) = job_obj.template.containers
    return container


def _resources(job_obj: Job) -> ContainerResources:
    resources = _container(job_obj).resources
    assert resources is not None
    return resources


def _env(job_obj: Job) -> dict[str | None, str | None]:
    env = _container(job_obj).env
    assert env is not None
    return {e.name: e.value for e in env}


def _identity(job_obj: Job) -> ManagedServiceIdentity:
    assert job_obj.identity is not None
    return job_obj.identity


def _registry(job_obj: Job) -> RegistryCredentials:
    registries = _config(job_obj).registries
    assert registries is not None
    (registry,) = registries
    return registry


@contextmanager
def _launch(
    launcher: AcaRunLauncher,
    *,
    image: str | None = ACR_IMAGE,
    container_context: dict[str, Any] | None = None,
) -> Iterator[tuple[DagsterInstance, DagsterRun, MagicMock, Job]]:
    """Launch a run through a real (ephemeral) instance and a fake Azure client.

    Yields the instance, the run as stored, the fake client, and the ``Job`` object the
    launcher handed to ``begin_create_or_update``.
    """
    client = _fake_client()
    recon_job = reconstructable(fake_job)
    python_origin = _python_origin(image=image, container_context=container_context)

    with (
        patch.object(launcher, "_get_client", return_value=client),
        instance_for_test() as instance,
        in_process_test_workspace(
            instance, LoadableTargetOrigin(python_file=__file__)
        ) as workspace,
    ):
        location = workspace.get_code_location(workspace.code_location_names[0])
        repo_handle = RepositoryHandle.from_location(
            repository_name=recon_job.repository.get_definition().name,
            code_location=location,
        )
        remote_job = remote_job_from_recon_job(
            recon_job, op_selection=None, repository_handle=repo_handle
        )
        run = create_run_for_test(
            instance,
            job_name=fake_job.name,
            remote_job_origin=remote_job.get_remote_origin(),
            job_code_origin=python_origin,
        )
        launcher.register_instance(instance)
        launcher.launch_run(LaunchRunContext(run, workspace))

        (_, _, job_obj), _ = client.jobs.begin_create_or_update.call_args
        assert isinstance(job_obj, Job)
        stored_run = instance.get_run_by_id(run.run_id)
        assert stored_run is not None
        yield instance, stored_run, client, job_obj


class TestFakeClient:
    def test_rejects_unknown_operation_groups_and_methods(self):
        """Documents why the tests use a spec'd client rather than a bare MagicMock:
        the bug that escaped to live testing was a misspelled SDK attribute.
        """
        client = _fake_client()
        with pytest.raises(AttributeError):
            client.job_execution  # noqa: B018
        with pytest.raises(AttributeError):
            client.jobs.begin_create  # noqa: B018
        with pytest.raises(TypeError):
            client.jobs.begin_start("rg")  # missing job_name


class TestConfigType:
    def test_required_fields_enumerated(self):
        schema = AcaRunLauncher.config_type()
        for required in ("subscription_id", "resource_group", "region", "environment_id"):
            assert required in schema, f"missing required field: {required}"

    def test_optional_fields_present(self):
        schema = AcaRunLauncher.config_type()
        for optional in (
            "env_vars",
            "run_resources",
            "identity_id",
            "run_job_replica_timeout",
        ):
            assert optional in schema

    def test_legacy_password_auth_fields_removed(self):
        schema = AcaRunLauncher.config_type()
        for legacy in (
            "registry_server",
            "registry_username",
            "registry_password_secret_name",
        ):
            assert legacy not in schema, f"{legacy!r} was retired in favor of MI-based ACR pull"

    def test_from_config_value_round_trips_through_schema(self):
        """Every optional key may be absent from dagster.yaml; the constructor must accept that."""
        launcher = AcaRunLauncher.from_config_value(
            MagicMock(),
            {
                "subscription_id": "sub",
                "resource_group": "rg",
                "region": "eastus",
                "environment_id": ENVIRONMENT_ID,
            },
        )
        assert launcher.env_vars == []
        assert launcher.run_resources == {}
        assert launcher.identity_id is None
        assert launcher.run_job_replica_timeout is None


class TestClient:
    def test_client_creation_quiets_sdk_header_logging(self, launcher, monkeypatch):
        """azure.core logs every request/response header at INFO unless its logger is raised."""
        import logging

        monkeypatch.setenv("AZURE_CLIENT_ID", "x")  # keep DefaultAzureCredential from probing
        sdk_logger = logging.getLogger("azure.core.pipeline.policies.http_logging_policy")
        sdk_logger.setLevel(logging.NOTSET)
        launcher._get_client()  # noqa: SLF001
        assert sdk_logger.level == logging.WARNING

    def test_from_config_value_passes_every_field_through(self):
        launcher = AcaRunLauncher.from_config_value(
            MagicMock(),
            {
                "subscription_id": "sub",
                "resource_group": "rg",
                "region": "westeurope",
                "environment_id": ENVIRONMENT_ID,
                "env_vars": ["A=1"],
                "run_resources": {"cpu": "1", "memory": "2Gi"},
                "identity_id": IDENTITY_ID,
                "run_job_replica_timeout": 300,
            },
        )
        assert launcher.env_vars == ["A=1"]
        assert launcher.run_resources == {"cpu": "1", "memory": "2Gi"}
        assert launcher.identity_id == IDENTITY_ID
        assert launcher.run_job_replica_timeout == 300
        assert launcher._region == "westeurope"  # noqa: SLF001


class TestProperties:
    def test_exposes_inputs_to_container_context(self, launcher):
        launcher._env_vars = ["A=1"]  # noqa: SLF001
        launcher._run_resources = {"cpu": "1"}  # noqa: SLF001
        launcher._identity_id = "id"  # noqa: SLF001
        assert list(launcher.env_vars) == ["A=1"]
        assert launcher.run_resources == {"cpu": "1"}
        assert launcher.identity_id == "id"


class TestLaunchRun:
    def test_creates_then_starts_job_and_records_it_on_the_run(self, launcher):
        with _launch(launcher) as (instance, run, client, job_obj):
            expected_name = sanitize_aca_name(f"dagster-run-{run.run_id}")

            client.jobs.begin_create_or_update.assert_called_once()
            (rg, name, _), _ = client.jobs.begin_create_or_update.call_args
            assert (rg, name) == ("rg", expected_name)
            # The launcher waits for the Job resource to exist, but not for the execution.
            client.jobs.begin_create_or_update.return_value.result.assert_called_once_with(
                timeout=30
            )
            client.jobs.begin_start.assert_called_once_with("rg", expected_name)
            client.jobs.begin_start.return_value.result.assert_not_called()

            assert run.tags[JOB_NAME_TAG] == expected_name
            engine_events = instance.all_logs(run.run_id, of_type=DagsterEventType.ENGINE_EVENT)
            assert any(expected_name in e.message for e in engine_events)

            assert job_obj.location == "eastus"
            assert job_obj.environment_id == ENVIRONMENT_ID

    def test_job_is_a_single_manual_execution_with_no_retries(self, launcher):
        with _launch(launcher) as (_, _, _, job_obj):
            cfg = _config(job_obj)
            assert cfg.trigger_type == "Manual"
            assert cfg.replica_retry_limit == 0
            assert cfg.manual_trigger_config is not None
            assert cfg.manual_trigger_config.replica_completion_count == 1
            assert cfg.manual_trigger_config.parallelism == 1
            # Default when neither launcher nor code location sets a timeout.
            assert cfg.replica_timeout == 24 * 60 * 60

    def test_container_runs_execute_run_with_stripped_origin(self, launcher):
        with _launch(launcher) as (instance, run, _, job_obj):
            container = _container(job_obj)
            assert container.name == "dagster-run"
            assert container.image == ACR_IMAGE

            origin = run.job_code_origin
            assert origin is not None
            stripped = origin._replace(
                repository_origin=origin.repository_origin._replace(container_context={})
            )
            expected = ExecuteRunArgs(
                job_origin=stripped, run_id=run.run_id, instance_ref=instance.get_ref()
            ).get_command_args()
            assert container.command is not None
            assert container.command == list(expected)
            assert container.command[-3:-1] == ["api", "execute_run"]

    def test_tags_identify_run_job_and_location(self, launcher):
        with _launch(launcher) as (_, run, _, job_obj):
            assert run.remote_job_origin is not None
            assert job_obj.tags == {
                "dagster-run-id": run.run_id,
                "dagster-job-name": fake_job.name,
                "dagster-location-name": run.remote_job_origin.location_name,
            }

    def test_without_identity_or_resources_azure_fields_are_omitted(self, launcher):
        with _launch(launcher) as (_, _, _, job_obj):
            assert job_obj.identity is None
            assert _config(job_obj).registries is None
            assert _container(job_obj).resources is None
            assert _env(job_obj) == {}

    def test_launcher_config_flows_into_job(self):
        launcher = _make_launcher(
            env_vars=["FROM_LAUNCHER=1"],
            run_resources={"cpu": "500m", "memory": "1Gi"},
            identity_id=IDENTITY_ID,
            run_job_replica_timeout=120,
        )
        with _launch(launcher) as (_, _, _, job_obj):
            assert _config(job_obj).replica_timeout == 120

            identity = _identity(job_obj)
            assert identity.type == ManagedServiceIdentityType.USER_ASSIGNED
            assert identity.user_assigned_identities is not None
            assert set(identity.user_assigned_identities) == {IDENTITY_ID}

            registry = _registry(job_obj)
            assert registry.server == "myacr.azurecr.io"
            assert registry.identity == IDENTITY_ID
            assert registry.password_secret_ref is None

            assert _resources(job_obj).cpu == 0.5
            assert _resources(job_obj).memory == "1Gi"
            assert _env(job_obj) == {"FROM_LAUNCHER": "1"}

    def test_code_location_container_context_extends_launcher_config(self):
        launcher = _make_launcher(
            env_vars=["FROM_LAUNCHER=1"],
            run_resources={"cpu": "1", "memory": "1Gi"},
            run_job_replica_timeout=120,
        )
        container_context = {
            "aca": {
                "env_vars": ["FROM_LOCATION=1"],
                "run_resources": {"memory": "4Gi"},
                "run_job_replica_timeout": 600,
            }
        }
        with _launch(launcher, container_context=container_context) as (_, _, _, job_obj):
            assert _env(job_obj) == {"FROM_LAUNCHER": "1", "FROM_LOCATION": "1"}
            # Per-key merge: location overrides memory, launcher cpu survives.
            assert _resources(job_obj).cpu == 1.0
            assert _resources(job_obj).memory == "4Gi"
            assert _config(job_obj).replica_timeout == 600

    def test_memory_only_resources(self):
        launcher = _make_launcher(run_resources={"memory": "512Mi"})
        with _launch(launcher) as (_, _, _, job_obj):
            assert _resources(job_obj).memory == "512Mi"
            assert _resources(job_obj).cpu is None

    def test_identity_without_acr_image_sets_identity_but_no_registry(self):
        launcher = _make_launcher(identity_id=IDENTITY_ID)
        with _launch(launcher, image="docker.io/library/python:3.12") as (_, _, _, job_obj):
            assert job_obj.identity is not None
            assert _config(job_obj).registries is None

    def test_missing_image_fails_before_calling_azure(self, launcher):
        client = _fake_client()
        with patch.object(launcher, "_get_client", return_value=client):
            with pytest.raises(CheckError, match="container image"):
                with _launch(launcher, image=None):
                    pass
        client.jobs.begin_create_or_update.assert_not_called()


class TestCheckRunWorkerHealth:
    def test_no_job_tag_returns_unknown(self, launcher):
        result = launcher.check_run_worker_health(_mk_run())
        assert result.status == WorkerStatus.UNKNOWN

    def test_no_executions_yet_returns_unknown(self, launcher, monkeypatch):
        fake_client = _fake_client()
        fake_client.jobs_executions.list.return_value = []
        monkeypatch.setattr(launcher, "_get_client", lambda: fake_client)
        result = launcher.check_run_worker_health(_mk_run(job_name="job"))
        assert result.status == WorkerStatus.UNKNOWN
        fake_client.jobs_executions.list.assert_called_once_with("rg", "job")

    @pytest.mark.parametrize(
        "azure_status,expected_worker_status",
        [
            (JobExecutionRunningState.RUNNING.value, WorkerStatus.RUNNING),
            (JobExecutionRunningState.PROCESSING.value, WorkerStatus.RUNNING),
            (JobExecutionRunningState.SUCCEEDED.value, WorkerStatus.SUCCESS),
            (JobExecutionRunningState.FAILED.value, WorkerStatus.FAILED),
            (JobExecutionRunningState.DEGRADED.value, WorkerStatus.FAILED),
            (JobExecutionRunningState.STOPPED.value, WorkerStatus.FAILED),
            # Azure's `JobExecutionRunningState` includes a literal "Unknown"
            # value; we map that (and any other undocumented value) to
            # WorkerStatus.UNKNOWN.
            (JobExecutionRunningState.UNKNOWN.value, WorkerStatus.UNKNOWN),
            ("WeirdUndocumentedValue", WorkerStatus.UNKNOWN),
        ],
    )
    def test_status_mapping(self, launcher, azure_status, expected_worker_status, monkeypatch):
        fake_client = _fake_client()
        fake_client.jobs_executions.list.return_value = [_mk_execution(azure_status)]
        monkeypatch.setattr(launcher, "_get_client", lambda: fake_client)
        result = launcher.check_run_worker_health(_mk_run(job_name="job"))
        assert result.status == expected_worker_status

    def test_every_sdk_status_is_handled(self):
        """If Microsoft adds a state to the enum, this fails so the mapping gets revisited."""
        handled = {
            JobExecutionRunningState.RUNNING,
            JobExecutionRunningState.PROCESSING,
            JobExecutionRunningState.SUCCEEDED,
            JobExecutionRunningState.FAILED,
            JobExecutionRunningState.DEGRADED,
            JobExecutionRunningState.STOPPED,
            JobExecutionRunningState.UNKNOWN,
        }
        assert set(JobExecutionRunningState) == handled

    def test_latest_execution_wins(self, launcher, monkeypatch):
        fake_client = _fake_client()
        fake_client.jobs_executions.list.return_value = [
            _mk_execution("Succeeded", start_time=10),
            _mk_execution("Running", start_time=20),
        ]
        monkeypatch.setattr(launcher, "_get_client", lambda: fake_client)
        result = launcher.check_run_worker_health(_mk_run(job_name="job"))
        assert result.status == WorkerStatus.RUNNING

    def test_execution_without_start_time_is_tolerated(self, launcher, monkeypatch):
        fake_client = _fake_client()
        never_started = MagicMock(status="Running", start_time=None, name="pending")
        started = _mk_execution("Succeeded", start_time=datetime(2026, 1, 1, tzinfo=timezone.utc))
        fake_client.jobs_executions.list.return_value = [never_started, started]
        monkeypatch.setattr(launcher, "_get_client", lambda: fake_client)
        result = launcher.check_run_worker_health(_mk_run(job_name="job"))
        assert result.status == WorkerStatus.SUCCESS

    def test_client_error_returns_unknown(self, launcher, monkeypatch):
        fake_client = _fake_client()
        fake_client.jobs_executions.list.side_effect = RuntimeError("boom")
        monkeypatch.setattr(launcher, "_get_client", lambda: fake_client)
        result = launcher.check_run_worker_health(_mk_run(job_name="job"))
        assert result.status == WorkerStatus.UNKNOWN

    def test_health_check_has_no_side_effects(self, launcher, monkeypatch):
        """Health checks must not delete resources — behavior to match other launchers."""
        fake_client = _fake_client()
        fake_client.jobs_executions.list.return_value = [_mk_execution("Succeeded")]
        monkeypatch.setattr(launcher, "_get_client", lambda: fake_client)
        launcher.check_run_worker_health(_mk_run(job_name="job"))
        fake_client.jobs.begin_delete.assert_not_called()
        fake_client.jobs.begin_stop_multiple_executions.assert_not_called()


class TestTerminate:
    def _prep(self, launcher, monkeypatch, *, run):
        fake_instance = MagicMock()
        fake_instance.get_run_by_id.return_value = run
        launcher.register_instance(fake_instance)
        fake_client = _fake_client()
        monkeypatch.setattr(launcher, "_get_client", lambda: fake_client)
        return fake_instance, fake_client

    def test_stop_and_delete_by_job_name(self, launcher, monkeypatch):
        # terminate discovers executions dynamically via stop_multiple_executions
        # rather than needing an execution id persisted on the run.
        run = MagicMock()
        run.is_finished = False
        run.tags = {JOB_NAME_TAG: "job"}
        fake_instance, fake_client = self._prep(launcher, monkeypatch, run=run)
        assert launcher.terminate("some-run-id") is True
        fake_instance.report_run_canceling.assert_called_once_with(run)
        fake_client.jobs.begin_stop_multiple_executions.assert_called_once_with("rg", "job")
        fake_client.jobs.begin_delete.assert_called_once_with("rg", "job")

    def test_missing_job_tag_returns_false(self, launcher, monkeypatch):
        run = MagicMock()
        run.is_finished = False
        run.tags = {}
        _, fake_client = self._prep(launcher, monkeypatch, run=run)
        assert launcher.terminate("some-run-id") is False
        fake_client.jobs.begin_delete.assert_not_called()

    def test_finished_run_is_not_touched(self, launcher, monkeypatch):
        run = MagicMock()
        run.is_finished = True
        run.tags = {JOB_NAME_TAG: "job"}
        fake_instance, fake_client = self._prep(launcher, monkeypatch, run=run)
        assert launcher.terminate("some-run-id") is False
        fake_instance.report_run_canceling.assert_not_called()
        fake_client.jobs.begin_delete.assert_not_called()

    def test_azure_error_returns_false(self, launcher, monkeypatch):
        run = MagicMock()
        run.is_finished = False
        run.tags = {JOB_NAME_TAG: "job"}
        _, fake_client = self._prep(launcher, monkeypatch, run=run)
        fake_client.jobs.begin_stop_multiple_executions.side_effect = RuntimeError("boom")
        assert launcher.terminate("some-run-id") is False
