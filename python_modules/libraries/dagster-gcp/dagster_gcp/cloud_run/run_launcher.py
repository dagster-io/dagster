import traceback
from typing import TYPE_CHECKING, Any, Mapping, Optional, Sequence

import tenacity
from dagster import (
    DagsterInstance,
    Field,
    Permissive,
    StringSource,
    _check as check,
)
from dagster._core.events import EngineEventData
from dagster._core.launcher.base import (
    CheckRunHealthResult,
    DagsterRun,
    LaunchRunContext,
    RunLauncher,
    WorkerStatus,
)
from dagster._grpc.types import ExecuteRunArgs
from dagster._serdes import ConfigurableClass, ConfigurableClassData
from google.api_core.exceptions import Conflict, ResourceExhausted, ServerError
from google.api_core.operation import Operation
from google.cloud import run_v2
from google.cloud.run_v2 import RunJobRequest
from google.cloud.run_v2.types import k8s_min
from typing_extensions import Self

if TYPE_CHECKING:
    from dagster._config.config_schema import UserConfigSchema


class CloudRunRunLauncher(RunLauncher, ConfigurableClass):
    """Run launcher for launching runs as a Google Cloud Run job."""

    def __init__(
        self,
        project: str,
        region: str,
        job_name_by_code_location: "dict[str, str]",
        run_job_retry: "dict[str, int]",
        inst_data: Optional[ConfigurableClassData] = None,
    ):
        self._inst_data = inst_data
        self.project = project
        self.region = region
        self.job_name_by_code_location = job_name_by_code_location

        self.run_job_retry_wait = run_job_retry["wait"]
        self.run_job_retry_timeout = run_job_retry["timeout"]

        self.jobs_client = run_v2.JobsClient()
        self.executions_client = run_v2.ExecutionsClient()

    def launch_run(self, context: LaunchRunContext) -> None:
        external_job_origin = check.not_none(context.dagster_run.external_job_origin)
        current_code_location = external_job_origin.location_name

        job_origin = check.not_none(context.job_code_origin)
        repository_origin = job_origin.repository_origin

        stripped_repository_origin = repository_origin._replace(container_context={})
        stripped_job_origin = job_origin._replace(repository_origin=stripped_repository_origin)

        args = ExecuteRunArgs(
            job_origin=stripped_job_origin,
            run_id=context.dagster_run.run_id,
            instance_ref=self._instance.get_ref(),
        )

        command_args = args.get_command_args()

        operation = self.create_execution(current_code_location, command_args)
        execution_id = operation.metadata.name.split("/")[-1]

        instance: DagsterInstance = self._instance
        instance.report_engine_event(
            message="Launched run in Cloud Run execution",
            dagster_run=context.dagster_run,
            engine_event_data=EngineEventData({"Execution ID": execution_id}),
            cls=self.__class__,
        )
        instance.add_run_tags(
            context.dagster_run.run_id, {"cloud_run_job_execution_id": execution_id}
        )

    def fully_qualified_job_name(self, code_location_name: str) -> str:
        try:
            job_name = self.job_name_by_code_location[code_location_name]
        except KeyError:
            raise Exception(f"No run launcher defined for code location: {code_location_name}")
        return f"projects/{self.project}/locations/{self.region}/jobs/{job_name}"

    def create_execution(self, code_location_name: str, args: Sequence[str]):
        job_name = self.fully_qualified_job_name(code_location_name)
        return self.execute_job(job_name, args=args)

    def execute_job(
        self,
        fully_qualified_job_name: str,
        timeout: str = "3600s",
        args: Optional[Sequence[str]] = None,
        env: Optional["dict[str, str]"] = None,
    ) -> Operation:
        request = RunJobRequest(name=fully_qualified_job_name)

        overrides = {}
        if args:
            overrides["args"] = args
        if env:
            overrides["env"] = [
                k8s_min.EnvVar(name=name, value=value) for name, value in env.items()
            ]

        container_overrides = [RunJobRequest.Overrides.ContainerOverride(**overrides)]

        request.overrides.container_overrides.extend(container_overrides)
        request.overrides.timeout = timeout

        @tenacity.retry(
            wait=tenacity.wait_fixed(self.run_job_retry_wait),
            stop=tenacity.stop_after_delay(self.run_job_retry_timeout),
            retry=tenacity.retry_if_exception_type(ResourceExhausted),
        )
        def run_job_with_retries_when_quota_exceeded(request: RunJobRequest):
            operation = self.jobs_client.run_job(request)
            return operation

        operation = run_job_with_retries_when_quota_exceeded(request)
        return operation

    def terminate(self, run_id: str) -> bool:
        instance: DagsterInstance = self._instance
        run = check.not_none(instance.get_run_by_id(run_id))
        execution_id = run.tags.get("cloud_run_job_execution_id")

        if not execution_id:
            self._instance.report_engine_event(
                message="Unable to identify Cloud Run execution ID for termination",
                dagster_run=run,
                cls=self.__class__,
            )
            return False

        instance.report_run_canceling(run)
        external_job_origin = check.not_none(run.external_job_origin)
        try:
            fully_qualified_execution_name = (
                f"{self.fully_qualified_job_name(external_job_origin.location_name)}"
                f"/executions/{execution_id}"
            )
            request = run_v2.CancelExecutionRequest(
                name=fully_qualified_execution_name,
            )
            self.executions_client.cancel_execution(request=request)
        except (ServerError, Conflict):
            self._instance.report_engine_event(
                message=f"Failed to terminate Cloud Run execution: {execution_id}. Error:\n{traceback.format_exc()}",
                dagster_run=run,
                cls=self.__class__,
            )
            return False

        instance.report_run_canceled(run)
        return True

    @property
    def inst_data(self) -> Optional[ConfigurableClassData]:
        return self._inst_data

    @classmethod
    def config_type(cls) -> "UserConfigSchema":
        return {
            "project": Field(
                StringSource,
                is_required=True,
                description="Google Cloud Platform project ID",
            ),
            "region": Field(
                StringSource,
                is_required=True,
                description="Google Cloud Platform region for the Cloud Run jobs",
            ),
            "job_name_by_code_location": Field(
                Permissive({}),
                is_required=True,
                description=(
                    "Job name for each code location. Each item in this map should be a key-value"
                    " pair where the key is the code location name and the value is the job name."
                ),
            ),
            "run_job_retry": Field(
                {
                    "wait": Field(
                        int,
                        is_required=False,
                        default_value=10,
                        description="Number of seconds to wait between retries",
                    ),
                    "timeout": Field(
                        int,
                        is_required=False,
                        default_value=300,
                        description="Number of seconds to wait before timing out",
                    ),
                },
                is_required=False,
                default_value={"wait": 10, "timeout": 300},
                description=(
                    "Retry configuration for run job requests. Note that the default Cloud Run "
                    "Admin API quota is quite low, which makes retries more likely."
                ),
            ),
        }

    @classmethod
    def from_config_value(
        cls, inst_data: ConfigurableClassData, config_value: Mapping[str, Any]
    ) -> Self:
        return cls(inst_data=inst_data, **config_value)

    @property
    def supports_check_run_worker_health(self):
        return True

    def check_run_worker_health(self, run: DagsterRun) -> CheckRunHealthResult:
        execution_id = run.tags.get("cloud_run_job_execution_id")

        if not execution_id:
            return CheckRunHealthResult(WorkerStatus.UNKNOWN)

        external_job_origin = check.not_none(run.external_job_origin)
        try:
            fully_qualified_execution_name = (
                f"{self.fully_qualified_job_name(external_job_origin.location_name)}"
                f"/executions/{execution_id}"
            )
            request = run_v2.GetExecutionRequest(name=fully_qualified_execution_name)
            execution = self.executions_client.get_execution(request=request)
            if execution.reconciling:
                return CheckRunHealthResult(WorkerStatus.RUNNING)
            elif execution.failed_count > 0 or execution.cancelled_count > 0:
                return CheckRunHealthResult(WorkerStatus.FAILED)
            elif execution.succeeded_count > 0:
                return CheckRunHealthResult(WorkerStatus.SUCCESS)
            else:
                return CheckRunHealthResult(
                    WorkerStatus.UNKNOWN, msg="Unable to determine execution status"
                )
        except (ServerError, Conflict):
            return CheckRunHealthResult(
                WorkerStatus.UNKNOWN, msg="Unable to fetch execution status"
            )
