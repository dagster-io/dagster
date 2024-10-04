import base64
import random
import string
import sys
from contextlib import contextmanager
from typing import Any, Dict, Generator, Iterator, List, Optional, Sequence, TextIO, TypedDict

import boto3
import dagster._check as check
from botocore.exceptions import ClientError
from dagster._annotations import experimental
from dagster._core.pipes.client import PipesMessageReader, PipesParams
from dagster._core.pipes.context import PipesMessageHandler
from dagster._core.pipes.utils import (
    PipesBlobStoreMessageReader,
    PipesLogReader,
    extract_message_or_forward_to_file,
    extract_message_or_forward_to_stdout,
)
from dagster_pipes import PipesDefaultMessageWriter


class PipesS3MessageReader(PipesBlobStoreMessageReader):
    """Message reader that reads messages by periodically reading message chunks from a specified S3
    bucket.

    If `log_readers` is passed, this reader will also start the passed readers
    when the first message is received from the external process.

    Args:
        interval (float): interval in seconds between attempts to download a chunk
        bucket (str): The S3 bucket to read from.
        client (WorkspaceClient): A boto3 client.
        log_readers (Optional[Sequence[PipesLogReader]]): A set of log readers for logs on S3.
    """

    def __init__(
        self,
        *,
        interval: float = 10,
        bucket: str,
        client: boto3.client,  # pyright: ignore (reportGeneralTypeIssues)
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

    def messages_are_readable(self, params: PipesParams) -> bool:
        key_prefix = params.get("key_prefix")
        if key_prefix is not None:
            try:
                self.client.head_object(Bucket=self.bucket, Key=f"{key_prefix}/1.json")
                return True
            except ClientError:
                return False
        else:
            return False

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


class CloudWatchEvent(TypedDict):
    timestamp: int
    message: str
    ingestionTime: int


@experimental
class PipesCloudWatchMessageReader(PipesMessageReader):
    """Message reader that consumes AWS CloudWatch logs to read pipes messages."""

    def __init__(self, client: Optional[boto3.client] = None):  # pyright: ignore (reportGeneralTypeIssues)
        """Args:
        client (boto3.client): boto3 CloudWatch client.
        """
        self.client = client or boto3.client("logs")

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
        self,
        log_group: str,
        log_stream: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        output_file: TextIO = sys.stdout,
    ) -> None:
        """Reads logs from AWS CloudWatch and forwards them to Dagster for events extraction and logging.

        Args:
            log_group (str): CloudWatch log group name
            log_stream (str): CLoudWatch log stream name
            start_time (Optional[int]): The start of the time range, expressed as the number of
                milliseconds after ``Jan 1, 1970 00:00:00 UTC``. Only events with a timestamp equal to this
                time or later are included.
            end_time (Optional[int]): The end of the time range, expressed as the number of
                milliseconds after ``Jan 1, 1970 00:00:00 UTC``. Events with a timestamp equal to or
                later than this time are not included.
            output_file: (Optional[TextIO]): A file to write the logs to. Defaults to sys.stdout.
        """
        handler = check.not_none(
            self._handler, "Can only consume logs within context manager scope."
        )

        for events_batch in self._get_all_cloudwatch_events(
            log_group=log_group, log_stream=log_stream, start_time=start_time, end_time=end_time
        ):
            for event in events_batch:
                for log_line in event["message"].splitlines():
                    extract_message_or_forward_to_file(handler, log_line, output_file)

    def no_messages_debug_text(self) -> str:
        return "Attempted to read messages by extracting them from CloudWatch logs directly."

    def _get_all_cloudwatch_events(
        self,
        log_group: str,
        log_stream: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
    ) -> Generator[List[CloudWatchEvent], None, None]:
        """Returns batches of CloudWatch events until the stream is complete or end_time."""
        params: Dict[str, Any] = {
            "logGroupName": log_group,
            "logStreamName": log_stream,
        }

        if start_time is not None:
            params["startTime"] = start_time
        if end_time is not None:
            params["endTime"] = end_time

        response = self.client.get_log_events(**params)

        while events := response.get("events"):
            yield events

            params["nextToken"] = response["nextForwardToken"]

            response = self.client.get_log_events(**params)
