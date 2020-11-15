import datetime
import json
import time

import boto3
import pytest
from dagster import ModeDefinition, execute_pipeline, pipeline, solid
from dagster_aws.cloudwatch import cloudwatch_logger
from dagster_aws.cloudwatch.loggers import millisecond_timestamp
from moto import mock_logs

from .conftest import AWS_REGION, TEST_CLOUDWATCH_LOG_GROUP_NAME, TEST_CLOUDWATCH_LOG_STREAM_NAME

TEN_MINUTES_MS = 10 * 60 * 1000  # in milliseconds
NUM_POLL_ATTEMPTS = 5


@solid
def hello_cloudwatch(context):
    context.log.info("Hello, Cloudwatch!")
    context.log.error("This is an error")


@pipeline(mode_defs=[ModeDefinition(logger_defs={"cloudwatch": cloudwatch_logger})])
def hello_cloudwatch_pipeline():
    hello_cloudwatch()


@pytest.fixture
def region():
    return "us-east-1"


@pytest.fixture
def cloudwatch_client(region):
    with mock_logs():
        yield boto3.client("logs", region_name=region)


@pytest.fixture
def log_group(cloudwatch_client):
    name = "/dagster-test/test-cloudwatch-logging"
    cloudwatch_client.create_log_group(logGroupName=name)
    return name


@pytest.fixture
def log_stream(cloudwatch_client, log_group):
    name = "test-logging"
    cloudwatch_client.create_log_stream(logGroupName=log_group, logStreamName=name)
    return name


def test_cloudwatch_logging_bad_log_group_name(region, cloudwatch_client, log_stream):
    with pytest.raises(
        Exception,
        match="Failed to initialize Cloudwatch logger: Could not find log group with name fake-log-group",
    ):
        execute_pipeline(
            hello_cloudwatch_pipeline,
            {
                "loggers": {
                    "cloudwatch": {
                        "config": {
                            "log_group_name": "fake-log-group",
                            "log_stream_name": log_stream,
                            "aws_region": region,
                        }
                    }
                }
            },
        )


def test_cloudwatch_logging_bad_log_stream_name(region, cloudwatch_client, log_group):
    with pytest.raises(
        Exception,
        match="Failed to initialize Cloudwatch logger: Could not find log stream with name fake-log-stream",
    ):
        execute_pipeline(
            hello_cloudwatch_pipeline,
            {
                "loggers": {
                    "cloudwatch": {
                        "config": {
                            "log_group_name": log_group,
                            "log_stream_name": "fake-log-stream",
                            "aws_region": region,
                        }
                    }
                }
            },
        )


# TODO: Test bad region


def test_cloudwatch_logging(region, cloudwatch_client, log_group, log_stream):
    res = execute_pipeline(
        hello_cloudwatch_pipeline,
        {
            "loggers": {
                "cloudwatch": {
                    "config": {
                        "log_group_name": log_group,
                        "log_stream_name": log_stream,
                        "aws_region": region
                    }
                }
            }
        },
    )

    now = millisecond_timestamp(datetime.datetime.utcnow())

    attempt_num = 0

    found_orig_message = False

    while not found_orig_message and attempt_num < NUM_POLL_ATTEMPTS:
        # Hack: the get_log_events call below won't include events logged in the pipeline execution
        # above if we query too soon after completion.
        time.sleep(1)

        # This is implicitly assuming that we're not running these tests with too much concurrency, etc.
        events = cloudwatch_client.get_log_events(
            startTime=now - TEN_MINUTES_MS,
            logGroupName=log_group,
            logStreamName=log_stream,
            limit=100,
        )["events"]

        for parsed_msg in (json.loads(event["message"]) for event in events):
            if parsed_msg["dagster_meta"]["run_id"] == res.run_id:
                if parsed_msg["dagster_meta"]["orig_message"] == "Hello, Cloudwatch!":
                    found_orig_message = True
                    break

        attempt_num += 1

    assert found_orig_message
