import time
from typing import Any, Dict, Literal, Mapping, Optional

import boto3
import dagster._check as check
from botocore.exceptions import ClientError
from dagster import PipesClient
from dagster._annotations import experimental, public
from dagster._core.definitions.resource_annotation import TreatAsResourceParam
from dagster._core.errors import DagsterExecutionInterruptedError
from dagster._core.execution.context.compute import OpExecutionContext
from dagster._core.pipes.client import (
    PipesClientCompletedInvocation,
    PipesContextInjector,
    PipesMessageReader,
)
from dagster._core.pipes.utils import open_pipes_session

from dagster_aws.pipes.context_injectors import PipesS3ContextInjector
from dagster_aws.pipes.message_readers import PipesCloudWatchMessageReader


@experimental
class PipesGlueClient(PipesClient, TreatAsResourceParam):
    """A pipes client for invoking AWS Glue jobs.

    Args:
        context_injector (Optional[PipesContextInjector]): A context injector to use to inject
            context into the Glue job, for example, :py:class:`PipesS3ContextInjector`.
        message_reader (Optional[PipesMessageReader]): A message reader to use to read messages
            from the glue job run. Defaults to :py:class:`PipesCloudWatchsMessageReader`.
            When provided with :py:class:`PipesCloudWatchMessageReader`,
            it will be used to recieve logs and events from the ``.../output/<job-run-id>``
            CloudWatch log stream created by AWS Glue. Note that AWS Glue routes both
            ``stderr`` and ``stdout`` from the main job process into this LogStream.
        client (Optional[boto3.client]): The boto Glue client used to launch the Glue job
        forward_termination (bool): Whether to cancel the Glue job run when the Dagster process receives a termination signal.
    """

    def __init__(
        self,
        context_injector: PipesContextInjector,
        message_reader: Optional[PipesMessageReader] = None,
        client: Optional[boto3.client] = None,
        forward_termination: bool = True,
    ):
        self._client = client or boto3.client("glue")
        self._context_injector = context_injector
        self._message_reader = message_reader or PipesCloudWatchMessageReader()
        self.forward_termination = check.bool_param(forward_termination, "forward_termination")

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    @public
    def run(
        self,
        *,
        job_name: str,
        context: OpExecutionContext,
        extras: Optional[Dict[str, Any]] = None,
        arguments: Optional[Mapping[str, Any]] = None,
        job_run_id: Optional[str] = None,
        allocated_capacity: Optional[int] = None,
        timeout: Optional[int] = None,
        max_capacity: Optional[float] = None,
        security_configuration: Optional[str] = None,
        notification_property: Optional[Mapping[str, Any]] = None,
        worker_type: Optional[str] = None,
        number_of_workers: Optional[int] = None,
        execution_class: Optional[Literal["FLEX", "STANDARD"]] = None,
    ) -> PipesClientCompletedInvocation:
        """Start a Glue job, enriched with the pipes protocol.

        See also: `AWS API Documentation <https://docs.aws.amazon.com/goto/WebAPI/glue-2017-03-31/StartJobRun>`_

        Args:
            job_name (str): The name of the job to use.
            context (OpExecutionContext): The context of the currently executing Dagster op or asset.
            extras (Optional[Dict[str, Any]]): Additional Dagster metadata to pass to the Glue job.
            arguments (Optional[Dict[str, str]]): Arguments to pass to the Glue job Command
            job_run_id (Optional[str]): The ID of the previous job run to retry.
            allocated_capacity (Optional[int]): The amount of DPUs (Glue data processing units) to allocate to this job.
            timeout (Optional[int]): The job run timeout in minutes.
            max_capacity (Optional[float]): The maximum capacity for the Glue job in DPUs (Glue data processing units).
            security_configuration (Optional[str]): The name of the Security Configuration to be used with this job run.
            notification_property (Optional[Mapping[str, Any]]): Specifies configuration properties of a job run notification.
            worker_type (Optional[str]): The type of predefined worker that is allocated when a job runs.
            number_of_workers (Optional[int]): The number of workers that are allocated when a job runs.
            execution_class (Optional[Literal["FLEX", "STANDARD"]]): The execution property of a job run.

        Returns:
            PipesClientCompletedInvocation: Wrapper containing results reported by the external
            process.
        """
        with open_pipes_session(
            context=context,
            message_reader=self._message_reader,
            context_injector=self._context_injector,
            extras=extras,
        ) as session:
            arguments = arguments or {}

            pipes_args = session.get_bootstrap_cli_arguments()

            if isinstance(self._context_injector, PipesS3ContextInjector):
                arguments = {**arguments, **pipes_args}

            params = {
                "JobName": job_name,
                "Arguments": arguments,
                "JobRunId": job_run_id,
                "AllocatedCapacity": allocated_capacity,
                "Timeout": timeout,
                "MaxCapacity": max_capacity,
                "SecurityConfiguration": security_configuration,
                "NotificationProperty": notification_property,
                "WorkerType": worker_type,
                "NumberOfWorkers": number_of_workers,
                "ExecutionClass": execution_class,
            }

            # boto3 does not accept None as defaults for some of the parameters
            # so we need to filter them out
            params = {k: v for k, v in params.items() if v is not None}

            start_timestamp = time.time() * 1000  # unix time in ms

            try:
                run_id = self._client.start_job_run(**params)["JobRunId"]

            except ClientError as err:
                context.log.error(
                    "Couldn't create job %s. Here's why: %s: %s",
                    job_name,
                    err.response["Error"]["Code"],
                    err.response["Error"]["Message"],
                )
                raise

            response = self._client.get_job_run(JobName=job_name, RunId=run_id)
            log_group = response["JobRun"]["LogGroupName"]
            context.log.info(f"Started AWS Glue job {job_name} run: {run_id}")

            try:
                response = self._wait_for_job_run_completion(job_name, run_id)
            except DagsterExecutionInterruptedError:
                if self.forward_termination:
                    self._terminate_job_run(context=context, job_name=job_name, run_id=run_id)
                raise

            if status := response["JobRun"]["JobRunState"] != "SUCCEEDED":
                raise RuntimeError(
                    f"Glue job {job_name} run {run_id} completed with status {status} :\n{response['JobRun'].get('ErrorMessage')}"
                )
            else:
                context.log.info(f"Glue job {job_name} run {run_id} completed successfully")

            if isinstance(self._message_reader, PipesCloudWatchMessageReader):
                # TODO: consume messages in real-time via a background thread
                # so we don't have to wait for the job run to complete
                # before receiving any logs
                self._message_reader.consume_cloudwatch_logs(
                    f"{log_group}/output", run_id, start_time=int(start_timestamp)
                )

        return PipesClientCompletedInvocation(session)

    def _wait_for_job_run_completion(self, job_name: str, run_id: str) -> Dict[str, Any]:
        while True:
            response = self._client.get_job_run(JobName=job_name, RunId=run_id)
            # https://docs.aws.amazon.com/glue/latest/dg/job-run-statuses.html
            if response["JobRun"]["JobRunState"] in [
                "FAILED",
                "SUCCEEDED",
                "STOPPED",
                "TIMEOUT",
                "ERROR",
            ]:
                return response
            time.sleep(5)

    def _terminate_job_run(self, context: OpExecutionContext, job_name: str, run_id: str):
        """Creates a handler which will gracefully stop the Run in case of external termination.
        It will stop the Glue job before doing so.
        """
        context.log.warning(f"[pipes] execution interrupted, stopping Glue job run {run_id}...")
        response = self._client.batch_stop_job_run(JobName=job_name, JobRunIds=[run_id])
        runs = response["SuccessfulSubmissions"]
        if len(runs) > 0:
            context.log.warning(f"Successfully stopped Glue job run {run_id}.")
        else:
            context.log.warning(
                f"Something went wrong during Glue job run termination: {response['errors']}"
            )
