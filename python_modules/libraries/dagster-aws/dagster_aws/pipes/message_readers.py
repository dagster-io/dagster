import base64
import gzip
import os
import random
import string
import sys
from collections.abc import Generator, Iterator, Sequence
from contextlib import contextmanager
from datetime import datetime
from threading import Event, Thread
from typing import IO, TYPE_CHECKING, Any, Callable, Optional, cast

import boto3
import dagster._check as check
from botocore.exceptions import ClientError
from dagster import DagsterInvariantViolationError
from dagster._core.pipes.client import PipesLaunchedData, PipesMessageReader, PipesParams
from dagster._core.pipes.context import PipesMessageHandler
from dagster._core.pipes.utils import (
    PipesBlobStoreMessageReader,
    PipesChunkedLogReader,
    PipesLogReader,
    PipesThreadedMessageReader,
    extract_message_or_forward_to_stdout,
    forward_only_logs_to_file,
)
from dagster._utils.backoff import backoff
from dagster_pipes import PipesBlobStoreMessageWriter, PipesDefaultMessageWriter

if TYPE_CHECKING:
    from mypy_boto3_logs import CloudWatchLogsClient
    from mypy_boto3_logs.type_defs import OutputLogEventTypeDef
    from mypy_boto3_s3 import S3Client


def _can_read_from_s3(client: "S3Client", bucket: Optional[str], key: Optional[str]):
    if not bucket or not key:
        return False
    else:
        try:
            client.head_object(Bucket=bucket, Key=key)
            return True
        except ClientError:
            return False


def default_log_decode_fn(contents: bytes) -> str:
    return contents.decode("utf-8")


def gzip_log_decode_fn(contents: bytes) -> str:
    return gzip.decompress(contents).decode("utf-8")


class PipesS3LogReader(PipesChunkedLogReader):
    def __init__(
        self,
        *,
        bucket: str,
        key: str,
        client: Optional["S3Client"] = None,
        interval: float = 10,
        target_stream: Optional[IO[str]] = None,
        # TODO: maybe move this parameter to a different scope
        decode_fn: Optional[Callable[[bytes], str]] = None,
        debug_info: Optional[str] = None,
    ):
        self.bucket = bucket
        self.key = key
        self.client: S3Client = client or boto3.client("s3")
        self.decode_fn = decode_fn or default_log_decode_fn

        self.log_position = 0

        super().__init__(
            interval=interval, target_stream=target_stream or sys.stdout, debug_info=debug_info
        )

    @property
    def name(self) -> str:
        return f"PipesS3LogReader(s3://{os.path.join(self.bucket, self.key)})"

    def target_is_readable(self, params: PipesParams) -> bool:
        return _can_read_from_s3(
            client=self.client,
            bucket=self.bucket,
            key=self.key,
        )

    def download_log_chunk(self, params: PipesParams) -> Optional[str]:
        text = self.decode_fn(
            self.client.get_object(Bucket=self.bucket, Key=self.key)["Body"].read()
        )
        current_position = self.log_position
        self.log_position += len(text)

        return text[current_position:]


class PipesS3MessageReader(PipesBlobStoreMessageReader):
    """Message reader that reads messages by periodically reading message chunks from a specified S3
    bucket.

    If `log_readers` is passed, this reader will also start the passed readers
    when the first message is received from the external process.

    Args:
        interval (float): interval in seconds between attempts to download a chunk
        bucket (str): The S3 bucket to read from.
        client (boto3.client): A boto3 S3 client.
        log_readers (Optional[Sequence[PipesLogReader]]): A set of log readers for logs on S3.
        include_stdio_in_messages (bool): Whether to send stdout/stderr to Dagster via Pipes messages. Defaults to False.
    """

    def __init__(
        self,
        *,
        interval: float = 10,
        bucket: str,
        client: boto3.client,  # pyright: ignore (reportGeneralTypeIssues)
        log_readers: Optional[Sequence[PipesLogReader]] = None,
        include_stdio_in_messages: bool = False,
    ):
        super().__init__(
            interval=interval,
            log_readers=log_readers,
        )
        self.bucket = check.str_param(bucket, "bucket")
        self.include_stdio_in_messages = check.bool_param(
            include_stdio_in_messages, "include_stdio_in_messages"
        )
        self.client = client

    @contextmanager
    def get_params(self) -> Iterator[PipesParams]:
        key_prefix = "".join(random.choices(string.ascii_letters, k=30))
        yield {
            "bucket": self.bucket,
            "key_prefix": key_prefix,
            PipesBlobStoreMessageWriter.INCLUDE_STDIO_IN_MESSAGES_KEY: self.include_stdio_in_messages,
        }

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


# Number of retries to attempt getting cloudwatch logs when faced with a throttling exception.
DEFAULT_CLOUDWATCH_LOGS_MAX_RETRIES = 10


# Custom backoff delay_generator for get_log_events which adds some jitter
def get_log_events_delay_generator() -> Iterator[float]:
    i = 0.5
    while True:
        yield i
        i *= 2
        i += random.uniform(0, 1)


def get_log_events(
    client: "CloudWatchLogsClient",
    max_retries: Optional[int] = DEFAULT_CLOUDWATCH_LOGS_MAX_RETRIES,
    **log_params,
):
    max_retries = max_retries or DEFAULT_CLOUDWATCH_LOGS_MAX_RETRIES

    return backoff(
        fn=client.get_log_events,
        kwargs=log_params,
        retry_on=(client.exceptions.ThrottlingException,),
        max_retries=max_retries,
        delay_generator=get_log_events_delay_generator(),
    )


def tail_cloudwatch_events(
    client: "CloudWatchLogsClient",
    log_group: str,
    log_stream: str,
    start_time: Optional[int] = None,
    max_retries: Optional[int] = DEFAULT_CLOUDWATCH_LOGS_MAX_RETRIES,
) -> Generator[list["OutputLogEventTypeDef"], None, None]:
    """Yields events from a CloudWatch log stream."""
    params: dict[str, Any] = {
        "logGroupName": log_group,
        "logStreamName": log_stream,
    }

    if start_time is not None:
        params["startTime"] = start_time

    response = get_log_events(client=client, max_retries=max_retries, **params)

    while True:
        events = response.get("events")

        if events:
            yield events

        params["nextToken"] = response["nextForwardToken"]

        response = get_log_events(client=client, max_retries=max_retries, **params)


class PipesCloudWatchLogReader(PipesLogReader):
    def __init__(
        self,
        client=None,
        log_group: Optional[str] = None,
        log_stream: Optional[str] = None,
        target_stream: Optional[IO[str]] = None,
        start_time: Optional[int] = None,
        debug_info: Optional[str] = None,
        max_retries: Optional[int] = DEFAULT_CLOUDWATCH_LOGS_MAX_RETRIES,
    ):
        self.client = client or boto3.client("logs")
        self.log_group = log_group
        self.log_stream = log_stream
        self.target_stream = target_stream or sys.stdout
        self.thread = None
        self.start_time = start_time
        self._debug_info = debug_info
        self.max_retries = max_retries

    @property
    def debug_info(self) -> Optional[str]:
        return self._debug_info

    def target_is_readable(self, params: PipesParams) -> bool:
        log_group = params.get("log_group") or self.log_group
        log_stream = params.get("log_stream") or self.log_stream

        if log_group is not None and log_stream is not None:
            # check if the stream actually exists
            try:
                resp = self.client.describe_log_streams(
                    logGroupName=log_group,
                    logStreamNamePrefix=log_stream,
                )

                if resp.get("logStreams", []):
                    return True
                else:
                    return False
            except self.client.exceptions.ResourceNotFoundException:
                return False
        else:
            return False

    def start(self, params: PipesParams, is_session_closed: Event) -> None:
        if not self.target_is_readable(params):
            raise DagsterInvariantViolationError(
                "log_group and log_stream must be set either in the constructor or in Pipes params."
            )

        self.thread = Thread(
            target=self._start, kwargs={"params": params, "is_session_closed": is_session_closed}
        )
        self.thread.start()

    def _start(self, params: PipesParams, is_session_closed: Event) -> None:
        log_group = cast(str, params.get("log_group") or self.log_group)
        log_stream = cast(str, params.get("log_stream") or self.log_stream)
        start_time = cast(int, self.start_time or params.get("start_time"))

        for events in tail_cloudwatch_events(
            self.client, log_group, log_stream, start_time=start_time, max_retries=self.max_retries
        ):
            for event in events:
                for line in event.get("message", "").splitlines():
                    if line:
                        forward_only_logs_to_file(line, self.target_stream)

            if is_session_closed.is_set():
                return

    def stop(self) -> None:
        pass

    def is_running(self) -> bool:
        return self.thread is not None and self.thread.is_alive()


class PipesCloudWatchMessageReader(PipesThreadedMessageReader):
    """Message reader that consumes AWS CloudWatch logs to read pipes messages."""

    def __init__(
        self,
        client=None,
        log_group: Optional[str] = None,
        log_stream: Optional[str] = None,
        log_readers: Optional[Sequence[PipesLogReader]] = None,
        max_retries: Optional[int] = DEFAULT_CLOUDWATCH_LOGS_MAX_RETRIES,
    ):
        """Args:
        client (boto3.client): boto3 CloudWatch client.
        """
        self.client: CloudWatchLogsClient = client or boto3.client("logs")
        self.log_group = log_group
        self.log_stream = log_stream
        self.max_retries = max_retries

        self.start_time = datetime.now()

        super().__init__(log_readers=log_readers)

    def on_launched(self, launched_payload: PipesLaunchedData) -> None:
        if "log_group" in launched_payload["extras"]:
            self.log_group = launched_payload["extras"]["log_group"]

        if "log_stream" in launched_payload["extras"]:
            self.log_stream = launched_payload["extras"]["log_stream"]

        self.launched_payload = launched_payload

    @contextmanager
    def get_params(self) -> Iterator[PipesParams]:
        yield {PipesDefaultMessageWriter.STDIO_KEY: PipesDefaultMessageWriter.STDOUT}

    def messages_are_readable(self, params: PipesParams) -> bool:
        if self.log_group is not None and self.log_stream is not None:
            # check if the stream actually exists
            try:
                resp = self.client.describe_log_streams(
                    logGroupName=self.log_group,
                    logStreamNamePrefix=self.log_stream,
                )

                if resp.get("logStreams", []):
                    return True
                else:
                    return False
            except self.client.exceptions.ResourceNotFoundException:
                return False
        else:
            return False

    def download_messages(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, cursor: Optional[str], params: PipesParams
    ) -> Optional[tuple[str, str]]:
        params = {
            "logGroupName": self.log_group,
            "logStreamName": self.log_stream,
            "startTime": int(self.start_time.timestamp() * 1000),
        }

        if cursor is not None:
            params["nextToken"] = cursor

        response = get_log_events(client=self.client, max_retries=self.max_retries, **params)

        events = response.get("events")

        if not events:
            return None
        else:
            cursor = cast(str, response["nextForwardToken"])
            return cursor, "\n".join(
                cast(str, event.get("message")) for event in events if event.get("message")
            )

    def no_messages_debug_text(self) -> str:
        return "Attempted to read messages by extracting them from CloudWatch logs."
