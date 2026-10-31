import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from dagster import (
    Field,
    StringSource,
    _check as check,
)
from dagster._annotations import beta
from dagster._core.events import EngineEventData
from dagster._core.launcher.base import (
    CheckRunHealthResult,
    LaunchRunContext,
    RunLauncher,
    WorkerStatus,
)
from dagster._grpc.types import ExecuteRunArgs
from dagster._serdes import ConfigurableClass
from dagster._utils.cached_method import cached_method
from typing_extensions import Self

from dagster_azure.container_apps.container_context import SHARED_ACA_SCHEMA, AcaContainerContext
from dagster_azure.container_apps.resources import interpret_aca_cpu_str_as_millicpus
from dagster_azure.container_apps.utils import build_acr_registry_credentials, sanitize_aca_name

try:
    from azure.identity import DefaultAzureCredential
    from azure.mgmt.appcontainers import ContainerAppsAPIClient
    from azure.mgmt.appcontainers.models import (
        Container,
        ContainerResources,
        EnvironmentVar,
        Job,
        JobConfiguration,
        JobConfigurationManualTriggerConfig,
        JobExecutionRunningState,
        JobTemplate,
        ManagedServiceIdentity,
        ManagedServiceIdentityType,
        UserAssignedIdentity,
    )
except ImportError as e:
    raise ImportError(
        "The Azure Container Apps run launcher requires the azure-mgmt-appcontainers SDK. "
        "Install it with `pip install dagster-azure[container_apps]`."
    ) from e

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from dagster._core.storage.dagster_run import DagsterRun
    from dagster._serdes.config_class import ConfigurableClassData

logger = logging.getLogger(__name__)

_JOB_NAME_TAG = "azure/container_apps/job_name"
_CREATE_POLL_TIMEOUT_SECS = 30
_DEFAULT_REPLICA_TIMEOUT_SECS = 60 * 60 * 24


@beta
class AcaRunLauncher(RunLauncher, ConfigurableClass):
    """Runs each Dagster run in its own Azure Container Apps Job.

    Launching a run creates a Job for it and starts one execution; the run's worker process is
    that execution's container. The Job name is stored as a tag on the run so the launcher can
    later check whether the execution is still alive or stop it. Cancelling a run deletes its
    Job. Completed Jobs are left in place, so the resource group holds one Job per finished run.
    """

    def __init__(
        self,
        *,
        inst_data: "ConfigurableClassData | None",
        subscription_id: str,
        resource_group: str,
        region: str,
        environment_id: str,
        env_vars: "Sequence[str] | None",
        run_resources: "Mapping[str, Any] | None",
        identity_id: str | None,
        run_job_replica_timeout: int | None,
    ):
        self._inst_data = inst_data
        self._subscription_id = check.str_param(subscription_id, "subscription_id")
        self._resource_group = check.str_param(resource_group, "resource_group")
        self._region = check.str_param(region, "region")
        self._environment_id = check.str_param(environment_id, "environment_id")
        self._env_vars = check.opt_sequence_param(env_vars, "env_vars", of_type=str)
        self._run_resources = check.opt_mapping_param(run_resources, "run_resources", key_type=str)
        self._identity_id = check.opt_str_param(identity_id, "identity_id")
        self._run_job_replica_timeout = check.opt_int_param(
            run_job_replica_timeout, "run_job_replica_timeout"
        )
        super().__init__()

    @property
    def inst_data(self) -> "ConfigurableClassData | None":
        return self._inst_data

    @classmethod
    def config_type(cls) -> "Mapping[str, Any]":
        return {
            "subscription_id": Field(StringSource, description="Azure subscription ID."),
            "resource_group": Field(
                StringSource, description="Resource group that will hold Job resources."
            ),
            "region": Field(
                StringSource,
                description='Azure region for Job resources (e.g. "eastus", "westeurope").',
            ),
            "environment_id": Field(
                StringSource,
                description=(
                    "Full ARM resource ID of the Azure Container Apps managed environment "
                    "the Job should run in."
                ),
            ),
            **SHARED_ACA_SCHEMA,
        }

    @classmethod
    def from_config_value(
        cls, inst_data: "ConfigurableClassData", config_value: "Mapping[str, Any]"
    ) -> Self:
        return cls(
            inst_data=inst_data,
            subscription_id=config_value["subscription_id"],
            resource_group=config_value["resource_group"],
            region=config_value["region"],
            environment_id=config_value["environment_id"],
            env_vars=config_value.get("env_vars"),
            run_resources=config_value.get("run_resources"),
            identity_id=config_value.get("identity_id"),
            run_job_replica_timeout=config_value.get("run_job_replica_timeout"),
        )

    @property
    def env_vars(self) -> "Sequence[str]":
        return self._env_vars

    @property
    def run_resources(self) -> "Mapping[str, Any]":
        return self._run_resources

    @property
    def identity_id(self) -> str | None:
        return self._identity_id

    @property
    def run_job_replica_timeout(self) -> int | None:
        return self._run_job_replica_timeout

    @cached_method
    def _get_client(self) -> ContainerAppsAPIClient:
        # The SDK logs every request and response header at INFO, which drowns the agent log.
        logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(
            logging.WARNING
        )
        return ContainerAppsAPIClient(DefaultAzureCredential(), self._subscription_id)

    def _job_name_for_run(self, run_id: str) -> str:
        return sanitize_aca_name(f"dagster-run-{run_id}")

    def launch_run(self, context: LaunchRunContext) -> None:
        run = context.dagster_run
        container_context = AcaContainerContext.create_for_run(run, self)

        job_origin = check.not_none(context.job_code_origin)
        image = check.not_none(
            job_origin.repository_origin.container_image,
            "Run worker requires a container image on the repository origin.",
        )

        # The per-location settings were already applied to the Job above; leave them out of
        # the serialized origin so the container's command line stays short (same as ECS).
        stripped_repository_origin = job_origin.repository_origin._replace(container_context={})
        stripped_job_origin = job_origin._replace(repository_origin=stripped_repository_origin)

        args = ExecuteRunArgs(
            job_origin=stripped_job_origin,
            run_id=run.run_id,
            instance_ref=self._instance.get_ref(),
        )
        command = args.get_command_args()

        env = [
            EnvironmentVar(name=k, value=v)
            for k, v in container_context.get_environment_dict().items()
        ]

        resources = self._container_resources(container_context)
        registries = self._registry_config(container_context, image)
        identity = self._identity_config(container_context)
        replica_timeout = (
            container_context.run_job_replica_timeout
            if container_context.run_job_replica_timeout is not None
            else _DEFAULT_REPLICA_TIMEOUT_SECS
        )

        job_name = self._job_name_for_run(run.run_id)
        job = Job(
            location=self._region,
            environment_id=self._environment_id,
            identity=identity,
            configuration=JobConfiguration(
                trigger_type="Manual",
                replica_timeout=replica_timeout,
                replica_retry_limit=0,
                manual_trigger_config=JobConfigurationManualTriggerConfig(
                    replica_completion_count=1, parallelism=1
                ),
                registries=registries,
            ),
            template=JobTemplate(
                containers=[
                    Container(
                        name="dagster-run",
                        image=image,
                        command=list(command),
                        env=env,
                        resources=resources,
                    )
                ]
            ),
            # Azure tag names cannot contain "/".
            tags={
                "dagster-run-id": run.run_id,
                "dagster-job-name": run.job_name,
                "dagster-location-name": (
                    run.remote_job_origin.location_name if run.remote_job_origin is not None else ""
                ),
            },
        )

        client = self._get_client()
        # The Job resource must exist before it can be started, and Azure takes 30-50s to
        # create it, so every launch blocks the agent for that long and concurrent launches
        # serialize. TODO: create and start the Job off the agent's request thread, or start it
        # from the first health check, so launch_run can return as soon as the create is accepted.
        create_poller = client.jobs.begin_create_or_update(self._resource_group, job_name, job)
        create_poller.result(timeout=_CREATE_POLL_TIMEOUT_SECS)
        client.jobs.begin_start(self._resource_group, job_name)

        self._instance.add_run_tags(run.run_id, {_JOB_NAME_TAG: job_name})

        self._instance.report_engine_event(
            message=f"Launched run as Azure Container Apps Job {job_name!r}",
            dagster_run=run,
            engine_event_data=EngineEventData(
                {
                    "Azure Container Apps Job": job_name,
                }
            ),
            cls=self.__class__,
        )

    def terminate(self, run_id: str) -> bool:
        run = self._instance.get_run_by_id(run_id)
        if not run or run.is_finished:
            return False

        self._instance.report_run_canceling(run)
        job_name = run.tags.get(_JOB_NAME_TAG)
        if not job_name:
            return False

        client = self._get_client()
        # Like the ECS and K8s launchers, return once the requests are accepted rather than
        # waiting for Azure to finish them.
        try:
            client.jobs.begin_stop_multiple_executions(self._resource_group, job_name)
            client.jobs.begin_delete(self._resource_group, job_name)
        except Exception:
            logger.exception(
                "Error terminating Azure Container Apps Job %r for run %s", job_name, run_id
            )
            return False
        return True

    @property
    def supports_check_run_worker_health(self) -> bool:
        return True

    def check_run_worker_health(self, run: "DagsterRun") -> CheckRunHealthResult:
        job_name = run.tags.get(_JOB_NAME_TAG)
        if not job_name:
            return CheckRunHealthResult(WorkerStatus.UNKNOWN, "no Azure Job tag on run")

        client = self._get_client()
        try:
            executions = list(client.jobs_executions.list(self._resource_group, job_name))
        except Exception as e:
            logger.exception("Failed to list Azure Job executions for %r", job_name)
            return CheckRunHealthResult(WorkerStatus.UNKNOWN, str(e))

        if not executions:
            return CheckRunHealthResult(
                WorkerStatus.UNKNOWN, f"no executions yet for job {job_name!r}"
            )

        never_started = datetime.min.replace(tzinfo=timezone.utc)
        latest = max(
            executions,
            key=lambda e: getattr(e, "start_time", None) or never_started,
        )
        status = getattr(latest, "status", None)
        execution_name = getattr(latest, "name", None) or "<unknown>"

        if status in (
            JobExecutionRunningState.RUNNING.value,
            JobExecutionRunningState.PROCESSING.value,
        ):
            return CheckRunHealthResult(WorkerStatus.RUNNING)
        if status == JobExecutionRunningState.SUCCEEDED.value:
            return CheckRunHealthResult(WorkerStatus.SUCCESS)
        if status in (
            JobExecutionRunningState.FAILED.value,
            JobExecutionRunningState.DEGRADED.value,
            JobExecutionRunningState.STOPPED.value,
        ):
            return CheckRunHealthResult(
                WorkerStatus.FAILED,
                f"Azure Container Apps Job execution {execution_name!r} ended in status {status!r}",
            )
        return CheckRunHealthResult(WorkerStatus.UNKNOWN, f"unrecognized status {status!r}")

    def _container_resources(
        self, container_context: AcaContainerContext
    ) -> ContainerResources | None:
        cpu = container_context.run_resources.get("cpu")
        memory = container_context.run_resources.get("memory")
        kwargs: dict[str, Any] = {}
        if cpu is not None:
            millicpus = interpret_aca_cpu_str_as_millicpus(cpu)
            if millicpus is not None:
                kwargs["cpu"] = millicpus / 1000
        if memory is not None:
            kwargs["memory"] = memory
        return ContainerResources(**kwargs) if kwargs else None

    def _registry_config(self, container_context: AcaContainerContext, image: str):
        return build_acr_registry_credentials(container_context.identity_id, image)

    def _identity_config(self, container_context: AcaContainerContext):
        if not container_context.identity_id:
            return None
        return ManagedServiceIdentity(
            type=ManagedServiceIdentityType.USER_ASSIGNED,
            user_assigned_identities={container_context.identity_id: UserAssignedIdentity()},
        )
