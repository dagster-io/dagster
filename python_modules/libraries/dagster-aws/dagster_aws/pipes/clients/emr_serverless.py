import sys
import time
from typing import TYPE_CHECKING, Any, Optional, Union, cast

import boto3
import dagster._check as check
from dagster import DagsterInvariantViolationError, PipesClient
from dagster._annotations import public
from dagster._core.definitions.metadata import RawMetadataMapping
from dagster._core.definitions.resource_annotation import TreatAsResourceParam
from dagster._core.errors import DagsterExecutionInterruptedError
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster._core.execution.context.compute import OpExecutionContext
from dagster._core.pipes.client import (
    PipesClientCompletedInvocation,
    PipesContextInjector,
    PipesMessageReader,
)
from dagster._core.pipes.context import PipesSession
from dagster._core.pipes.utils import PipesEnvContextInjector, open_pipes_session
from dagster._utils.merger import deep_merge_dicts

from dagster_aws.pipes.message_readers import PipesCloudWatchLogReader, PipesCloudWatchMessageReader

if TYPE_CHECKING:
    from mypy_boto3_emr_serverless.client import EMRServerlessClient
    from mypy_boto3_emr_serverless.literals import JobRunStateType
    from mypy_boto3_emr_serverless.type_defs import (
        GetJobRunResponseTypeDef,
        MonitoringConfigurationTypeDef,
        StartJobRunRequestTypeDef,
        StartJobRunResponseTypeDef,
    )

AWS_SERVICE_NAME = "EMR Serverless"


@public
class PipesEMRServerlessClient(PipesClient, TreatAsResourceParam):
    """A pipes client for running workloads on AWS EMR Serverless.

    Args:
        client (Optional[boto3.client]): The boto3 AWS EMR Serverless client used to interact with AWS EMR Serverless.
        context_injector (Optional[PipesContextInjector]): A context injector to use to inject
            context into AWS EMR Serverless workload. Defaults to :py:class:`PipesEnvContextInjector`.
        message_reader (Optional[PipesMessageReader]): A message reader to use to read messages
            from the AWS EMR Serverless workload. Defaults to :py:class:`PipesCloudWatchMessageReader`.
        forward_termination (bool): Whether to cancel the AWS EMR Serverless workload if the Dagster process receives a termination signal.
        poll_interval (float): The interval in seconds to poll the AWS EMR Serverless workload for status updates. Defaults to 5 seconds.
    """

    AWS_SERVICE_NAME = AWS_SERVICE_NAME

    def __init__(
        self,
        client: Optional["EMRServerlessClient"] = None,
        context_injector: Optional[PipesContextInjector] = None,
        message_reader: Optional[PipesMessageReader] = None,
        forward_termination: bool = True,
        poll_interval: float = 5.0,
    ):
        self._client: EMRServerlessClient = cast(
            "EMRServerlessClient", client or boto3.client("emr-serverless")
        )
        self._context_injector = context_injector or PipesEnvContextInjector()
        self._message_reader = message_reader or PipesCloudWatchMessageReader()
        self.forward_termination = check.bool_param(forward_termination, "forward_termination")
        self.poll_interval = poll_interval

    @property
    def client(self) -> "EMRServerlessClient":
        return self._client

    @property
    def context_injector(self) -> PipesContextInjector:
        return self._context_injector

    @property
    def message_reader(self) -> PipesMessageReader:
        return self._message_reader

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    @public
    def run(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        *,
        context: Union[OpExecutionContext, AssetExecutionContext],
        start_job_run_params: "StartJobRunRequestTypeDef",
        extras: Optional[dict[str, Any]] = None,
    ) -> PipesClientCompletedInvocation:
        """Run a workload on AWS EMR Serverless, enriched with the pipes protocol.

        Args:
            context (Union[OpExecutionContext, AssetExecutionContext]): The context of the currently executing Dagster op or asset.
            params (dict): Parameters for the ``start_job_run`` boto3 AWS EMR Serverless client call.
                See `Boto3 EMR Serverless API Documentation <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/emr-serverless/client/start_job_run.html>`_
            extras (Optional[Dict[str, Any]]): Additional information to pass to the Pipes session in the external process.

        Returns:
            PipesClientCompletedInvocation: Wrapper containing results reported by the external
            process.
        """
        with open_pipes_session(
            context=context,
            message_reader=self.message_reader,
            context_injector=self.context_injector,
            extras=extras,
        ) as session:
            start_job_run_params = self._enrich_start_params(context, session, start_job_run_params)
            start_response = self._start(context, start_job_run_params)
            try:
                completion_response = self._wait_for_completion(context, start_response)
                context.log.info(f"[pipes] {self.AWS_SERVICE_NAME} workload is complete!")
                self._read_messages(context, session, completion_response)
                return PipesClientCompletedInvocation(
                    session, metadata=self._extract_dagster_metadata(completion_response)
                )

            except DagsterExecutionInterruptedError:
                if self.forward_termination:
                    context.log.warning(
                        f"[pipes] Dagster process interrupted! Will terminate external {self.AWS_SERVICE_NAME} workload."
                    )
                    self._terminate(context, start_response)
                raise

    def _enrich_start_params(
        self,
        context: Union[OpExecutionContext, AssetExecutionContext],
        session: PipesSession,
        params: "StartJobRunRequestTypeDef",
    ) -> "StartJobRunRequestTypeDef":
        # inject Dagster tags
        tags = params.get("tags", {})
        params["tags"] = {**tags, **session.default_remote_invocation_info}

        # inject env variables via --conf spark.executorEnv.env.<key>=<value>
        dagster_env_vars = {}

        dagster_env_vars.update(session.get_bootstrap_env_vars())

        if "jobDriver" not in params:
            params["jobDriver"] = {}

        if "sparkSubmit" not in params["jobDriver"]:
            params["jobDriver"]["sparkSubmit"] = {}  # pyright: ignore[reportGeneralTypeIssues]

        params["jobDriver"]["sparkSubmit"]["sparkSubmitParameters"] = params.get(
            "jobDriver", {}
        ).get("sparkSubmit", {}).get("sparkSubmitParameters", "") + "".join(
            [
                f" --conf spark.emr-serverless.driverEnv.{key}={value}"
                for key, value in dagster_env_vars.items()
            ]
        )

        return cast("StartJobRunRequestTypeDef", params)

    def _start(
        self,
        context: Union[OpExecutionContext, AssetExecutionContext],
        params: "StartJobRunRequestTypeDef",
    ) -> "StartJobRunResponseTypeDef":
        response = self.client.start_job_run(**params)
        job_run_id = response["jobRunId"]

        context.log.info(
            f"[pipes] {self.AWS_SERVICE_NAME} job started with job_run_id {job_run_id}."
        )

        return response

    def _wait_for_completion(
        self,
        context: Union[OpExecutionContext, AssetExecutionContext],
        start_response: "StartJobRunResponseTypeDef",
    ) -> "GetJobRunResponseTypeDef":  # pyright: ignore[reportReturnType]
        job_run_id = start_response["jobRunId"]
        application_id = start_response["applicationId"]

        running_dashboard_url = None
        completed_dashboard_url = None

        while response := self.client.get_job_run(
            applicationId=start_response["applicationId"],
            jobRunId=job_run_id,
        ):
            state: JobRunStateType = response["jobRun"]["state"]

            # get dashboard url when it's ready (but only once)
            if state == "RUNNING" and running_dashboard_url is None:
                running_dashboard_url = self.client.get_dashboard_for_job_run(
                    applicationId=application_id, jobRunId=job_run_id
                )
                context.log.info(
                    f"[pipes] {self.AWS_SERVICE_NAME} job is running. Dashboard URL: {running_dashboard_url}"
                )
            # completed jobs have a different dashboard url
            elif state in ["SUCCEEDED", "FAILED", "CANCELLED"] and completed_dashboard_url is None:
                completed_dashboard_url = self.client.get_dashboard_for_job_run(
                    applicationId=application_id, jobRunId=job_run_id
                )
                context.log.info(
                    f"[pipes] {self.AWS_SERVICE_NAME} job is completed. Dashboard URL: {completed_dashboard_url}"
                )

            # check if the job is in a terminal state
            if state in ["FAILED", "CANCELLED", "CANCELLING"]:
                context.log.error(
                    f"[pipes] {self.AWS_SERVICE_NAME} job {job_run_id} terminated with state: {state}. Details:\n{response['jobRun'].get('stateDetails')}"
                )
                raise RuntimeError(
                    f"{self.AWS_SERVICE_NAME} job failed"
                )  # TODO: introduce something like DagsterPipesRemoteExecutionError
            elif state == "SUCCESS":
                context.log.info(
                    f"[pipes] {self.AWS_SERVICE_NAME} job {job_run_id} completed with state: {state}"
                )
                return response
            elif state in ["PENDING", "SUBMITTED", "SCHEDULED", "RUNNING", "QUEUED"]:
                time.sleep(self.poll_interval)
                continue
            else:
                raise DagsterInvariantViolationError(
                    f"Unexpected state for AWS EMR Serverless job {job_run_id}: {state}"
                )

    def _read_messages(
        self,
        context: Union[OpExecutionContext, AssetExecutionContext],
        session: PipesSession,
        response: "GetJobRunResponseTypeDef",
    ):
        application_id = response["jobRun"]["applicationId"]
        job_id = response["jobRun"]["jobRunId"]

        application = self.client.get_application(applicationId=application_id)["application"]

        # merge base monitoring configuration from application
        # with potential overrides from the job run
        application_monitoring_configuration = application.get("monitoringConfiguration", {})
        job_monitoring_configuration = (
            response["jobRun"].get("configurationOverrides", {}).get("monitoringConfiguration", {})
        )
        monitoring_configuration = cast(
            "MonitoringConfigurationTypeDef",
            deep_merge_dicts(application_monitoring_configuration, job_monitoring_configuration),
        )

        application_type = application["type"]

        if application_type == "Spark":
            worker_type = "SPARK_DRIVER"
        elif application_type == "Hive":
            worker_type = "HIVE_DRIVER"
        else:
            raise NotImplementedError(f"Application type {application_type} is not supported")

        if not isinstance(self.message_reader, PipesCloudWatchMessageReader):
            context.log.warning(
                f"[pipes] {self.message_reader} is not supported for {self.AWS_SERVICE_NAME}. Dagster won't be able to receive logs and messages from the job."
            )
            return

        # https://docs.aws.amazon.com/emr/latest/EMR-Serverless-UserGuide/logging.html#jobs-log-storage-cw

        # we can get cloudwatch logs from the known log group

        if (
            monitoring_configuration.get("cloudWatchLoggingConfiguration", {}).get("enabled")
            is not True
        ):
            context.log.warning(
                f"[pipes] Recieved {self.message_reader}, but CloudWatch logging is not enabled for {self.AWS_SERVICE_NAME} job. Dagster won't be able to receive logs and messages from the job."
            )
            return

        if log_types := monitoring_configuration.get("cloudWatchLoggingConfiguration", {}).get(
            "logTypes"
        ):
            # get the configured output streams
            # but limit them with "stdout" and "stderr"
            output_streams = list(
                map(
                    lambda x: x.lower(),
                    set(log_types.get(worker_type, ["STDOUT", "STDERR"])) & {"stdout", "stderr"},
                )
            )
        else:
            output_streams = ["stdout", "stderr"]

        log_group = monitoring_configuration.get("logGroupName") or "/aws/emr-serverless"

        attempt = response["jobRun"].get("attempt")

        if attempt is not None and attempt > 1:
            log_stream = (
                f"/applications/{application_id}/jobs/{job_id}/attempts/{attempt}/{worker_type}"
            )
        else:
            log_stream = f"/applications/{application_id}/jobs/{job_id}/{worker_type}"

        if log_stream_prefix := monitoring_configuration.get(
            "cloudWatchLoggingConfiguration", {}
        ).get("logStreamNamePrefix"):
            log_stream = f"{log_stream_prefix}{log_stream}"

        output_files = {
            "stdout": sys.stdout,
            "stderr": sys.stderr,
        }

        # update MessageReader params so it can start receiving messages
        if isinstance(self.message_reader, PipesCloudWatchMessageReader):
            session.report_launched(
                {
                    "extras": {
                        "log_group": log_group,
                        "log_stream": f"{log_stream}/stdout",
                    }
                }
            )

            # now add LogReaders for stdout and stderr logs
            for output_stream in output_streams:
                output_file = output_files[output_stream]
                context.log.debug(
                    f"[pipes] Adding PipesCloudWatchLogReader for group {log_group} stream {log_stream}/{output_stream}"
                )
                self.message_reader.add_log_reader(
                    PipesCloudWatchLogReader(
                        client=self.message_reader.client,
                        log_group=log_group,
                        log_stream=f"{log_stream}/{output_stream}",
                        target_stream=output_file,
                        start_time=int(session.created_at.timestamp() * 1000),
                        debug_info=output_stream,
                    ),
                )

    def _extract_dagster_metadata(self, response: "GetJobRunResponseTypeDef") -> RawMetadataMapping:
        metadata: RawMetadataMapping = {}

        job_run = response["jobRun"]

        metadata["AWS EMR Serverless Application ID"] = job_run["applicationId"]
        metadata["AWS EMR Serverless Job Run ID"] = job_run["jobRunId"]

        # TODO: it would be great to add a url to EMR Studio page for this run
        # such urls look like: https://es-638xhdetxum2td9nc3a45evmn.emrstudio-prod.eu-north-1.amazonaws.com/#/serverless-applications/00fm4oe0607u5a1d
        # but we need to get the Studio ID from the application_id
        # which is not possible with the current AWS API

        return metadata

    def _terminate(
        self,
        context: Union[OpExecutionContext, AssetExecutionContext],
        start_response: "StartJobRunResponseTypeDef",
    ):
        job_run_id = start_response["jobRunId"]
        application_id = start_response["applicationId"]
        context.log.info(f"[pipes] Terminating {self.AWS_SERVICE_NAME} job run {job_run_id}")
        self.client.cancel_job_run(applicationId=application_id, jobRunId=job_run_id)
