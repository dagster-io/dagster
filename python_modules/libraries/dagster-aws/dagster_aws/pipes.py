import base64
import json
import os
import random
import string
import time
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Dict, Iterator, Literal, Mapping, Optional, Sequence

import boto3
import dagster._check as check
from botocore.exceptions import ClientError
from dagster import PipesClient
from dagster._annotations import experimental
from dagster._core.definitions.resource_annotation import TreatAsResourceParam
from dagster._core.execution.context.compute import OpExecutionContext
from dagster._core.pipes.client import (
    PipesClientCompletedInvocation,
    PipesContextInjector,
    PipesMessageReader,
    PipesParams,
)
from dagster._core.pipes.context import PipesMessageHandler
from dagster._core.pipes.utils import (
    PipesBlobStoreMessageReader,
    PipesEnvContextInjector,
    PipesLogReader,
    extract_message_or_forward_to_stdout,
    open_pipes_session,
)
from dagster_pipes import PipesDefaultMessageWriter

if TYPE_CHECKING:
    from dagster_pipes import PipesContextData

_CONTEXT_FILENAME = "context.json"


class PipesS3ContextInjector(PipesContextInjector):
    """A context injector that injects context by writing to a temporary S3 location.

    Args:
        bucket (str): The S3 bucket to write to.
        client (boto3.client): A boto3 client to use to write to S3.
        key_prefix (Optional[str]): An optional prefix to use for the S3 key. Defaults to a random
            string.

    """

    def __init__(self, *, bucket: str, client: boto3.client):
        super().__init__()
        self.bucket = check.str_param(bucket, "bucket")
        self.client = client

    @contextmanager
    def inject_context(self, context: "PipesContextData") -> Iterator[PipesParams]:
        key_prefix = "".join(random.choices(string.ascii_letters, k=30))
        key = os.path.join(key_prefix, _CONTEXT_FILENAME)
        self.client.put_object(
            Body=json.dumps(context).encode("utf-8"), Bucket=self.bucket, Key=key
        )
        yield {"bucket": self.bucket, "key": key}
        self.client.delete_object(Bucket=self.bucket, Key=key)

    def no_messages_debug_text(self) -> str:
        return (
            "Attempted to inject context via a temporary file in s3. Expected"
            " PipesS3ContextLoader to be explicitly passed to open_dagster_pipes in the external"
            " process."
        )


class PipesS3MessageReader(PipesBlobStoreMessageReader):
    """Message reader that reads messages by periodically reading message chunks from a specified S3
    bucket.

    If `log_readers` is passed, this reader will also start the passed readers
    when the first message is received from the external process.

    Args:
        interval (float): interval in seconds between attempts to download a chunk
        bucket (str): The S3 bucket to read from.
        client (WorkspaceClient): A boto3 client.
        log_readers (Optional[Sequence[PipesLogReader]]): A set of readers for logs on S3.
    """

    def __init__(
        self,
        *,
        interval: float = 10,
        bucket: str,
        client: boto3.client,
        log_readers: Optional[Sequence[PipesLogReader]] = None,
    ):
        super().__init__(
            interval=interval,
            log_readers=log_readers,
        )
        self.bucket = check.str_param(bucket, "bucket")
        self.client = client

    @contextmanager
    def get_params(self) -> Iterator[PipesParams]:
        key_prefix = "".join(random.choices(string.ascii_letters, k=30))
        yield {"bucket": self.bucket, "key_prefix": key_prefix}

    def download_messages_chunk(self, index: int, params: PipesParams) -> Optional[str]:
        key = f"{params['key_prefix']}/{index}.json"
        try:
            obj = self.client.get_object(Bucket=self.bucket, Key=key)
            return obj["Body"].read().decode("utf-8")
        except ClientError:
            return None

    def no_messages_debug_text(self) -> str:
        return (
            f"Attempted to read messages from S3 bucket {self.bucket}. Expected"
            " PipesS3MessageWriter to be explicitly passed to open_dagster_pipes in the external"
            " process."
        )


class PipesLambdaLogsMessageReader(PipesMessageReader):
    """Message reader that consumes buffered pipes messages that were flushed on exit from the
    final 4k of logs that are returned from issuing a sync lambda invocation. This means messages
    emitted during the computation will only be processed once the lambda completes.

    Limitations: If the volume of pipes messages exceeds 4k, messages will be lost and it is
    recommended to switch to PipesS3MessageWriter & PipesS3MessageReader.
    """

    @contextmanager
    def read_messages(
        self,
        handler: PipesMessageHandler,
    ) -> Iterator[PipesParams]:
        self._handler = handler
        try:
            # use buffered stdio to shift the pipes messages to the tail of logs
            yield {PipesDefaultMessageWriter.BUFFERED_STDIO_KEY: PipesDefaultMessageWriter.STDERR}
        finally:
            self._handler = None

    def consume_lambda_logs(self, response) -> None:
        handler = check.not_none(
            self._handler, "Can only consume logs within context manager scope."
        )

        log_result = base64.b64decode(response["LogResult"]).decode("utf-8")

        for log_line in log_result.splitlines():
            extract_message_or_forward_to_stdout(handler, log_line)

    def no_messages_debug_text(self) -> str:
        return (
            "Attempted to read messages by extracting them from the tail of lambda logs directly."
        )


@experimental
class PipesCloudWatchMessageReader(PipesMessageReader):
    """Message reader that consumes AWS CloudWatch logs to read pipes messages."""

    @contextmanager
    def read_messages(
        self,
        handler: PipesMessageHandler,
    ) -> Iterator[PipesParams]:
        self._handler = handler
        try:
            # use buffered stdio to shift the pipes messages to the tail of logs
            yield {PipesDefaultMessageWriter.BUFFERED_STDIO_KEY: PipesDefaultMessageWriter.STDERR}
        finally:
            self._handler = None

    def consume_cloudwatch_logs(
        self, client: boto3.client, log_group: str, log_stream: str
    ) -> None:
        raise NotImplementedError("CloudWatch logs are not yet supported in the pipes protocol.")

    def no_messages_debug_text(self) -> str:
        return "Attempted to read messages by extracting them from the tail of CloudWatch logs directly."


class PipesLambdaEventContextInjector(PipesEnvContextInjector):
    def no_messages_debug_text(self) -> str:
        return "Attempted to inject context via the lambda event input."


class PipesLambdaClient(PipesClient, TreatAsResourceParam):
    """A pipes client for invoking AWS lambda.

    By default context is injected via the lambda input event and messages are parsed out of the
    4k tail of logs. S3

    Args:
        client (boto3.client): The boto lambda client used to call invoke.
        context_injector (Optional[PipesContextInjector]): A context injector to use to inject
            context into the lambda function. Defaults to :py:class:`PipesLambdaEventContextInjector`.
        message_reader (Optional[PipesMessageReader]): A message reader to use to read messages
            from the lambda function. Defaults to :py:class:`PipesLambdaLogsMessageReader`.
    """

    def __init__(
        self,
        client: boto3.client,
        context_injector: Optional[PipesContextInjector] = None,
        message_reader: Optional[PipesMessageReader] = None,
    ):
        self._client = client
        self._message_reader = message_reader or PipesLambdaLogsMessageReader()
        self._context_injector = context_injector or PipesLambdaEventContextInjector()

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    def run(
        self,
        *,
        function_name: str,
        event: Mapping[str, Any],
        context: OpExecutionContext,
    ) -> PipesClientCompletedInvocation:
        """Synchronously invoke a lambda function, enriched with the pipes protocol.

        Args:
            function_name (str): The name of the function to use.
            event (Mapping[str, Any]): A JSON serializable object to pass as input to the lambda.
            context (OpExecutionContext): The context of the currently executing Dagster op or asset.

        Returns:
            PipesClientCompletedInvocation: Wrapper containing results reported by the external
            process.
        """
        with open_pipes_session(
            context=context,
            message_reader=self._message_reader,
            context_injector=self._context_injector,
        ) as session:
            other_kwargs = {}
            if isinstance(self._message_reader, PipesLambdaLogsMessageReader):
                other_kwargs["LogType"] = "Tail"

            if isinstance(self._context_injector, PipesLambdaEventContextInjector):
                payload_data = {
                    **event,
                    **session.get_bootstrap_env_vars(),
                }
            else:
                payload_data = event

            response = self._client.invoke(
                FunctionName=function_name,
                InvocationType="RequestResponse",
                Payload=json.dumps(payload_data),
                **other_kwargs,
            )
            if isinstance(self._message_reader, PipesLambdaLogsMessageReader):
                self._message_reader.consume_lambda_logs(response)

            if "FunctionError" in response:
                err_payload = json.loads(response["Payload"].read().decode("utf-8"))

                raise Exception(
                    f"Lambda Function Error ({response['FunctionError']}):\n{json.dumps(err_payload, indent=2)}"
                )

        # should probably have a way to return the lambda result payload
        return PipesClientCompletedInvocation(session)


class PipesGlueContextInjector(PipesS3ContextInjector):
    def no_messages_debug_text(self) -> str:
        return "Attempted to inject context via Glue job arguments."


class PipesGlueLogsMessageReader(PipesCloudWatchMessageReader):
    def no_messages_debug_text(self) -> str:
        return "Attempted to read messages by extracting them from the tail of CloudWatch logs directly."


@experimental
class PipesGlueClient(PipesClient, TreatAsResourceParam):
    """A pipes client for invoking AWS Glue jobs.

    Args:
        client (boto3.client): The boto Glue client used to call invoke.
        context_injector (Optional[PipesContextInjector]): A context injector to use to inject
            context into the Glue job, for example, :py:class:`PipesGlueContextInjector`.
        message_reader (Optional[PipesMessageReader]): A message reader to use to read messages
            from the glue job run. Defaults to :py:class:`PipesGlueLogsMessageReader`.
    """

    def __init__(
        self,
        client: boto3.client,
        context_injector: PipesContextInjector,
        message_reader: Optional[PipesMessageReader] = None,
    ):
        self._client = client
        self._context_injector = context_injector
        self._message_reader = message_reader or PipesCloudWatchMessageReader()

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

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

            try:
                response = self._client.start_job_run(**params)
                run_id = response["JobRunId"]
                context.log.info(f"Started AWS Glue job {job_name} run: {run_id}")
                response = self._wait_for_job_run_completion(job_name, run_id)

                if response["JobRun"]["JobRunState"] == "FAILED":
                    raise RuntimeError(
                        f"Glue job {job_name} run {run_id} failed:\n{response['JobRun']['ErrorMessage']}"
                    )
                else:
                    context.log.info(f"Glue job {job_name} run {run_id} completed successfully")

            except ClientError as err:
                context.log.error(
                    "Couldn't create job %s. Here's why: %s: %s",
                    job_name,
                    err.response["Error"]["Code"],
                    err.response["Error"]["Message"],
                )
                raise

        # TODO: get logs from CloudWatch. there are 2 separate streams for stdout and driver stderr to read from
        # the log group can be found in the response from start_job_run, and the log stream is the job run id
        # worker logs have log streams like: <job_id>_<worker_id> but we probably don't need to read those

        # should probably have a way to return the lambda result payload
        return PipesClientCompletedInvocation(session)

    def _wait_for_job_run_completion(self, job_name: str, run_id: str) -> Dict[str, Any]:
        while True:
            response = self._client.get_job_run(JobName=job_name, RunId=run_id)
            if response["JobRun"]["JobRunState"] in ["FAILED", "SUCCEEDED"]:
                return response
            time.sleep(5)
