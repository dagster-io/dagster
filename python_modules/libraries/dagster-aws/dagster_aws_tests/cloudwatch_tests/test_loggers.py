import datetime
import json
import time

import pytest
from dagster_aws.cloudwatch import cloudwatch_logger
from dagster_aws.cloudwatch.loggers import millisecond_timestamp

from dagster import ModeDefinition, PipelineDefinition, execute_pipeline, solid

from .conftest import AWS_REGION, TEST_CLOUDWATCH_LOG_GROUP_NAME, TEST_CLOUDWATCH_LOG_STREAM_NAME

TEN_MINUTES_MS = 10 * 60 * 1000  # in milliseconds
NUM_POLL_ATTEMPTS = 5


@solid(name='hello_cloudwatch')
def hello_cloudwatch(context):
    context.log.info('Hello, Cloudwatch!')


def define_hello_cloudwatch_pipeline():
    return PipelineDefinition(
        [hello_cloudwatch],
        name='hello_cloudwatch_pipeline',
        mode_defs=[ModeDefinition(logger_defs={'cloudwatch': cloudwatch_logger})],
    )


def test_cloudwatch_logging_bad_log_group_name():
    with pytest.raises(
        Exception,
        match='Failed to initialize Cloudwatch logger: Could not find log group with name foo',
    ):
        execute_pipeline(
            define_hello_cloudwatch_pipeline(),
            {
                'loggers': {
                    'cloudwatch': {
                        'config': {
                            'log_group_name': 'foo',
                            'log_stream_name': 'bar',
                            'aws_region': 'us-east-1',  # different region
                        }
                    }
                }
            },
        )


def test_cloudwatch_logging_bad_log_stream_name():
    with pytest.raises(
        Exception,
        match='Failed to initialize Cloudwatch logger: Could not find log stream with name bar',
    ):
        execute_pipeline(
            define_hello_cloudwatch_pipeline(),
            {
                'loggers': {
                    'cloudwatch': {
                        'config': {
                            'log_group_name': TEST_CLOUDWATCH_LOG_GROUP_NAME,
                            'log_stream_name': 'bar',
                            'aws_region': AWS_REGION,
                        }
                    }
                }
            },
        )


# TODO: Test bad region


def test_cloudwatch_logging(cloudwatch_client):
    res = execute_pipeline(
        define_hello_cloudwatch_pipeline(),
        {
            'loggers': {
                'cloudwatch': {
                    'config': {
                        'log_group_name': TEST_CLOUDWATCH_LOG_GROUP_NAME,
                        'log_stream_name': TEST_CLOUDWATCH_LOG_STREAM_NAME,
                        'aws_region': AWS_REGION,
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
            logGroupName=TEST_CLOUDWATCH_LOG_GROUP_NAME,
            logStreamName=TEST_CLOUDWATCH_LOG_STREAM_NAME,
            limit=100,
        )['events']

        for parsed_msg in (json.loads(event['message']) for event in events):
            if parsed_msg['dagster_meta']['run_id'] == res.run_id:
                if parsed_msg['dagster_meta']['orig_message'] == 'Hello, Cloudwatch!':
                    found_orig_message = True
                    break

        attempt_num += 1

    assert found_orig_message
