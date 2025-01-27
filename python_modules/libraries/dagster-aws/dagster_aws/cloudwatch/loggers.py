import datetime
import logging
from typing import Optional

import boto3
from dagster import (
    Field,
    StringSource,
    _check as check,
    _seven,
    logger,
)
from dagster._core.utils import coerce_valid_log_level

# The maximum batch size is 1,048,576 bytes, and this size is calculated as the sum of all event
# messages in UTF-8, plus 26 bytes for each log event.
MAXIMUM_BATCH_SIZE = 1048576
OVERHEAD = 26

EPOCH = datetime.datetime(1970, 1, 1)


# For real
def millisecond_timestamp(dt):
    td = dt - EPOCH
    microsecond_timestamp = (
        td.days * 24 * 60 * 60 * 1000000 + td.seconds * 1000000 + td.microseconds
    )
    return int(microsecond_timestamp / 1000)


class CloudwatchLogsHandler(logging.Handler):
    def __init__(
        self,
        log_group_name,
        log_stream_name,
        aws_region=None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        endpoint_url: Optional[str] = None,
        use_ssl: bool = True,
        aws_session_token: Optional[str] = None,
        verify: Optional[bool] = None,
    ):
        self.client = boto3.client(
            "logs",
            region_name=aws_region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            endpoint_url=endpoint_url,
            use_ssl=use_ssl,
            aws_session_token=aws_session_token,
            verify=verify,
        )
        self.log_group_name = check.str_param(log_group_name, "log_group_name")
        # Maybe we should make this optional, and default to the run_id
        self.log_stream_name = check.str_param(log_stream_name, "log_stream_name")
        self.overhead = OVERHEAD
        self.maximum_batch_size = MAXIMUM_BATCH_SIZE
        self.sequence_token = None

        self.check_log_group()
        self.check_log_stream()

        super().__init__()

    def check_log_group(self):
        # Check that log group exists
        log_group_exists = False
        next_token = None
        while not log_group_exists:
            describe_log_group_kwargs = {"logGroupNamePrefix": self.log_group_name}
            if next_token is not None:
                describe_log_group_kwargs["nextToken"] = next_token

            res = self.client.describe_log_groups(**describe_log_group_kwargs)
            if self.log_group_name in (log_group["logGroupName"] for log_group in res["logGroups"]):
                log_group_exists = True
                break
            else:
                next_token = res.get("nextToken")
                if next_token is None:
                    break

        if not log_group_exists:
            raise Exception(
                "Failed to initialize Cloudwatch logger: Could not find log group with name "
                f"{self.log_group_name}"
            )

    def check_log_stream(self):
        # Check that log stream exists
        log_stream_exists = False
        next_token = None
        while not log_stream_exists:
            describe_log_stream_kwargs = {
                "logGroupName": self.log_group_name,
                "logStreamNamePrefix": self.log_stream_name,
            }
            if next_token is not None:
                describe_log_stream_kwargs["nextToken"] = next_token

            res = self.client.describe_log_streams(**describe_log_stream_kwargs)
            for log_stream in res["logStreams"]:
                if self.log_stream_name == log_stream["logStreamName"]:
                    log_stream_exists = True
                    self.sequence_token = log_stream.get("uploadSequenceToken")
                break
            else:
                next_token = res.get("nextToken")
                if next_token is None:
                    break

        if not log_stream_exists:
            raise Exception(
                "Failed to initialize Cloudwatch logger: Could not find log stream with name "
                f"{self.log_stream_name}"
            )

    def log_error(self, record, exc):
        logging.critical("Error while logging!")
        try:
            logging.error(f"Attempted to log: {_seven.json.dumps(record.__dict__)}")
        except Exception:
            pass
        logging.exception(str(exc))

    def emit(self, record):
        self._emit(record, retry=False)

    def retry(self, record):
        self._emit(record, retry=True)

    def _emit(self, record, retry=False):
        message = _seven.json.dumps(record.__dict__)
        timestamp = millisecond_timestamp(
            datetime.datetime.strptime(record.dagster_meta["log_timestamp"], "%Y-%m-%dT%H:%M:%S.%f")
        )
        params = {
            "logGroupName": self.log_group_name,
            "logStreamName": self.log_stream_name,
            "logEvents": [{"timestamp": timestamp, "message": message}],
        }
        if self.sequence_token is not None:
            params["sequenceToken"] = self.sequence_token

        res = None
        try:
            res = self.client.put_log_events(**params)
            self.sequence_token = res["nextSequenceToken"]
            log_events_rejected = res.get("rejectedLogEventsInfo")
            if log_events_rejected is not None:
                logging.error(f"Cloudwatch logger: log events rejected: {res}")
        except self.client.exceptions.InvalidSequenceTokenException as exc:
            if not retry:
                self.check_log_stream()
                self.retry(record)
            else:
                self.log_error(record, exc)
        except self.client.exceptions.DataAlreadyAcceptedException:
            logging.error(f"Cloudwatch logger: log events already accepted: {res}")
        except self.client.exceptions.InvalidParameterException:
            logging.error(f"Cloudwatch logger: Invalid parameter exception while logging: {res}")
        except self.client.exceptions.ResourceNotFoundException:
            logging.error(
                "Cloudwatch logger: Resource not found. Check that the log stream or log group "
                f"was not deleted: {res}"
            )
        except self.client.exceptions.ServiceUnavailableException:
            if not retry:
                self.retry(record)
            else:
                logging.error(f"Cloudwatch logger: Service unavailable: {res}")
        except self.client.exceptions.ServiceUnavailableException:
            if not retry:
                self.retry(record)
            else:
                logging.error(
                    "Cloudwatch logger: Unrecognized client. Check your AWS access key id and "
                    f"secret key: {res}"
                )


@logger(
    {
        "log_level": Field(str, is_required=False, default_value="INFO"),
        "name": Field(str, is_required=False, default_value="dagster"),
        "log_group_name": Field(str, description="The name of the log group"),
        "log_stream_name": Field(str, description="The name of the log stream"),
        "aws_region": Field(
            StringSource,
            is_required=False,
            description=(
                "Specifies a custom region for the S3 session. Default is chosen through "
                "the ordinary boto3 credential chain."
            ),
        ),
        "aws_secret_access_key": Field(StringSource, is_required=False),
        "aws_access_key_id": Field(StringSource, is_required=False),
    },
    description="The default colored console logger.",
)
def cloudwatch_logger(init_context):
    """This logger provides support for sending Dagster logs to AWS CloudWatch.

    Example:
        .. code-block:: python

            from dagster import job, op
            from dagster_aws.cloudwatch import cloudwatch_logger

            @op
            def hello_op(context):
                context.log.info('Hello, Cloudwatch!')
                context.log.error('This is an error')

            @job(logger_defs={'cloudwatch': cloudwatch_logger})
            def hello_cloudwatch():
                hello_op()

            hello_cloudwatch.execute_in_process(
                run_config={
                    'loggers': {
                        'cloudwatch': {
                            'config': {
                                'log_group_name': '/dagster-test/test-cloudwatch-logging',
                                'log_stream_name': 'test-logging',
                                'aws_region': 'us-west-1'
                            }
                        }
                    }
                }
            )
    """
    level = coerce_valid_log_level(init_context.logger_config["log_level"])
    name = init_context.logger_config["name"]

    klass = logging.getLoggerClass()
    logger_ = klass(name, level=level)

    logger_.addHandler(
        CloudwatchLogsHandler(
            init_context.logger_config["log_group_name"],
            init_context.logger_config["log_stream_name"],
            aws_region=init_context.logger_config.get("aws_region"),
            aws_secret_access_key=init_context.logger_config.get("aws_secret_access_key"),
            aws_access_key_id=init_context.logger_config.get("aws_access_key_id"),
        )
    )
    return logger_
