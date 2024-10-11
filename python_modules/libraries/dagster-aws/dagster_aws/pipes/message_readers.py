import base64
import os
import random
import string
import sys
from contextlib import contextmanager
from typing import (
    IO,
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Generator,
    Iterator,
    List,
    Optional,
    Sequence,
    TextIO,
    TypedDict,
    cast,
)

import boto3
import dagster._check as check
from botocore.exceptions import ClientError
from dagster._annotations import experimental
from dagster._core.pipes.client import PipesLaunchedData, PipesMessageReader, PipesParams
from dagster._core.pipes.context import PipesMessageHandler
from dagster._core.pipes.utils import (
    PipesBlobStoreMessageReader,
    PipesChunkedLogReader,
    PipesLogReader,
    extract_message_or_forward_to_file,
    extract_message_or_forward_to_stdout,
)
from dagster_pipes import PipesDefaultMessageWriter

if TYPE_CHECKING:
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
        self.client: "S3Client" = client or boto3.client("s3")
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
    """Message reader that reads messages from S3. Can operate in two modes: reading messages from objects
    created by py:class:`dagster_pipes.PipesS3MessageWriter`, or reading messages from a specific S3 object
    (typically a normal log file). If `log_readers` is passed, this reader will also start the passed readers
    when the first message is received from the external process.

    - if `expect_s3_message_writer` is set to `True` (default), a py:class:`dagster_pipes.PipesS3MessageWriter`
        is expected to be used in the external process. The writer will write messages to a random S3 prefix in chunks,
        and this reader will read them in order.

    - if `expect_s3_message_writer` is set to `False`, this reader will read messages from a specific S3 object,
        typically created by an external service (for example, by dumping stdout/stderr containing Pipes messages).
        The object key can either be passed via corresponding constructor argument,
        or with `on_launched` method (if not known in advance).

    Args:
        interval (float): interval in seconds between attempts to download a chunk
        bucket (str): The S3 bucket to read from.
        client (Any): An optional boto3 client.
        expect_s3_message_writer (bool): Whether to expect a PipesS3MessageWriter to be used in the external process.
        key (Optional[str]): The S3 key to read from. If not set, the key must be passed via `on_launched`.
        log_readers (Optional[Sequence[PipesLogReader]]): A set of log readers for logs on S3.
    """

    def __init__(
        self,
        *,
        bucket: str,
        client: Optional["S3Client"] = None,
        expect_s3_message_writer: bool = True,
        key: Optional[str] = None,
        interval: float = 10,
        log_readers: Optional[Sequence[PipesLogReader]] = None,
    ):
        super().__init__(
            interval=interval,
            log_readers=log_readers,
        )

        self.bucket = check.str_param(bucket, "bucket")
        self.client: "S3Client" = client or boto3.client("s3")
        self.expect_s3_message_writer = expect_s3_message_writer
        self.key = key

        self.offset = 0

        if expect_s3_message_writer and key is not None:
            raise ValueError("key should not be set if expect_s3_message_writer is True")

    def on_launched(self, launched_payload: PipesLaunchedData) -> None:
        if not self.expect_s3_message_writer:
            self.key = launched_payload["extras"].get("key")

        self.launched_payload = launched_payload

    @contextmanager
    def get_params(self) -> Iterator[PipesParams]:
        if self.expect_s3_message_writer:
            key_prefix = "".join(random.choices(string.ascii_letters, k=30))
            yield {"bucket": self.bucket, "key_prefix": key_prefix}
        else:
            yield {PipesDefaultMessageWriter.STDIO_KEY: PipesDefaultMessageWriter.STDOUT}

    def messages_are_readable(self, params: PipesParams) -> bool:
        if self.expect_s3_message_writer:
            # we are supposed to be reading from {i}.json chunks created by the MessageWriter
            return _can_read_from_s3(
                client=self.client,
                bucket=params.get("bucket") or self.bucket,
                key=f"{params['key_prefix']}/1.json",
            )
        else:
            return _can_read_from_s3(client=self.client, bucket=self.bucket, key=self.key)

    def download_messages_chunk(self, index: int, params: PipesParams) -> Optional[str]:
        if self.expect_s3_message_writer:
            try:
                obj = self.client.get_object(
                    Bucket=self.bucket, Key=f"{params['key_prefix']}/{index}.json"
                )
                return obj["Body"].read().decode("utf-8")
            except ClientError:
                return None
        else:
            # we will be reading the same S3 object again and again
            key = cast(str, params.get("key") or self.key)
            try:
                text = (
                    self.client.get_object(Bucket=self.bucket, Key=key)["Body"]
                    .read()
                    .decode("utf-8")
                )
                next_text = text[self.offset :]
                self.offset = len(text)
                return next_text
            except ClientError:
                return None

    def no_messages_debug_text(self) -> str:
        if self.expect_s3_message_writer:
            return f"Attempted to read messages from S3 bucket {self.bucket}. Expected PipesS3MessageWriter to be explicitly passed to open_dagster_pipes in the external process."
        else:
            message = f"Attempted to read messages from S3 bucket {self.bucket}. The key is not set (yet)."

            if self.key is not None:
                message += f" Expected to read messages from S3 key {self.key}."
            else:
                message += " The `key` parameter was not set, should be provided via `on_launched`."

            message += " Please check if the object exists and is accessible."

            return message


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
