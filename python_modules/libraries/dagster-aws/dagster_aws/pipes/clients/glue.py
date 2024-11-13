import time
from typing import TYPE_CHECKING, Any, Dict, Optional, Union, cast

import boto3
import dagster._check as check
from botocore.exceptions import ClientError
from dagster import PipesClient
from dagster._annotations import experimental, public
from dagster._core.definitions.resource_annotation import TreatAsResourceParam
from dagster._core.errors import DagsterExecutionInterruptedError
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster._core.execution.context.compute import OpExecutionContext
from dagster._core.pipes.client import (
    PipesClientCompletedInvocation,
    PipesContextInjector,
    PipesMessageReader,
)
from dagster._core.pipes.utils import open_pipes_session

from dagster_aws.pipes.message_readers import PipesCloudWatchLogReader, PipesCloudWatchMessageReader

if TYPE_CHECKING:
    from mypy_boto3_glue.client import GlueClient
    from mypy_boto3_glue.type_defs import StartJobRunRequestRequestTypeDef


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
        client: Optional["GlueClient"] = None,
        forward_termination: bool = True,
    ):
        self._client: GlueClient = client or boto3.client("glue")
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
        context: Union[OpExecutionContext, AssetExecutionContext],
        start_job_run_params: "StartJobRunRequestRequestTypeDef",
        extras: Optional[Dict[str, Any]] = None,
    ) -> PipesClientCompletedInvocation:
        """Start a Glue job, enriched with the pipes protocol.

        See also: `AWS API Documentation <https://docs.aws.amazon.com/goto/WebAPI/glue-2017-03-31/StartJobRun>`_

        Args:
            context (Union[OpExecutionContext, AssetExecutionContext]): The context of the currently executing Dagster op or asset.
            start_job_run_params (Dict): Parameters for the ``start_job_run`` boto3 Glue client call.
            extras (Optional[Dict[str, Any]]): Additional Dagster metadata to pass to the Glue job.

        Returns:
            PipesClientCompletedInvocation: Wrapper containing results reported by the external
            process.
        """
        params = start_job_run_params

        params["Arguments"] = params.get("Arguments") or {}
        job_name = cast(str, params["JobName"])

        with open_pipes_session(
            context=context,
            message_reader=self._message_reader,
            context_injector=self._context_injector,
            extras=extras,
        ) as session:
            pipes_args = session.get_bootstrap_cli_arguments()

            params["Arguments"].update(pipes_args)  # pyright: ignore (reportAttributeAccessIssue)

            try:
                run_id = self._client.start_job_run(**params)["JobRunId"]

            except ClientError as err:
                context.log.error(
                    "Couldn't create job %s. Here's why: %s: %s",
                    job_name,
                    err.response["Error"]["Code"],  # pyright: ignore (reportTypedDictNotRequiredAccess)
                    err.response["Error"]["Message"],  # pyright: ignore (reportTypedDictNotRequiredAccess)
                )
                raise

            response = self._client.get_job_run(JobName=job_name, RunId=run_id)
            log_group = response["JobRun"]["LogGroupName"]  # pyright: ignore (reportTypedDictNotRequiredAccess)
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

            # Glue is dumping both stdout and stderr to the same log group called */output
            if isinstance(self._message_reader, PipesCloudWatchMessageReader):
                session.report_launched(
                    {
                        "extras": {"log_group": f"{log_group}/output", "log_stream": run_id},
                    }
                )
            if isinstance(self._message_reader, PipesCloudWatchMessageReader):
                self._message_reader.add_log_reader(
                    PipesCloudWatchLogReader(
                        client=self._message_reader.client,
                        log_group=f"{log_group}/output",
                        log_stream=run_id,
                        start_time=int(session.created_at.timestamp() * 1000),
                    ),
                )

        return PipesClientCompletedInvocation(session)

    def _wait_for_job_run_completion(self, job_name: str, run_id: str) -> Dict[str, Any]:
        while True:
            response = self._client.get_job_run(JobName=job_name, RunId=run_id)
            # https://docs.aws.amazon.com/glue/latest/dg/job-run-statuses.html
            if response["JobRun"]["JobRunState"] in [  # pyright: ignore (reportTypedDictNotRequiredAccess)
                "FAILED",
                "SUCCEEDED",
                "STOPPED",
                "TIMEOUT",
                "ERROR",
            ]:
                return response  # pyright: ignore (reportReturnType)
            time.sleep(5)

    def _terminate_job_run(
        self, context: Union[OpExecutionContext, AssetExecutionContext], job_name: str, run_id: str
    ):
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
                f"Something went wrong during Glue job run termination: {response['errors']}"  # pyright: ignore (reportGeneralTypeIssues)
            )
