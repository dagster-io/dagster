import datetime
import json

import boto3
import pytest

from dagster import execute_pipeline, ModeDefinition, PipelineDefinition, solid
from dagster_aws.cloudwatch import cloudwatch_logger
from dagster_aws.cloudwatch.loggers import millisecond_timestamp


TEST_CLOUDWATCH_LOG_GROUP_NAME = '/dagster-test/test-cloudwatch-logging'
TEST_CLOUDWATCH_LOG_STREAM_NAME = 'test-logging'


def permissioned_and_connected():
    try:
        client = boto3.client('logs', 'us-west-1')
        client.describe_log_groups(logGroupNamePrefix=TEST_CLOUDWATCH_LOG_GROUP_NAME)
        res = client.describe_log_streams(
            logGroupName=TEST_CLOUDWATCH_LOG_GROUP_NAME,
            logStreamNamePrefix=TEST_CLOUDWATCH_LOG_STREAM_NAME,
        )
        if TEST_CLOUDWATCH_LOG_STREAM_NAME in (
            log_stream['logStreamName'] for log_stream in res['logStreams']
        ):
            return True
        else:
            return False
    except:  # pylint: disable=bare-except
        return False


cloudwatch_test = pytest.mark.skipif(
    not permissioned_and_connected(),
    reason='Not credentialed for cloudwatch tests or could not connect to AWS',
)


@solid(name='hello_cloudwatch')
def hello_cloudwatch(context):
    context.log.info('Hello, Cloudwatch!')


def define_hello_cloudwatch_pipeline():
    return PipelineDefinition(
        [hello_cloudwatch],
        name='hello_cloudwatch_pipeline',
        mode_defs=[ModeDefinition(logger_defs={'cloudwatch': cloudwatch_logger})],
    )


@cloudwatch_test
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
                            'aws_region': 'us-east-1',
                        }
                    }
                }
            },
        )


@cloudwatch_test
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
                            'aws_region': 'us-west-1',
                        }
                    }
                }
            },
        )


# TODO: Test bad region


@cloudwatch_test
def test_cloudwatch_logging():
    res = execute_pipeline(
        define_hello_cloudwatch_pipeline(),
        {
            'loggers': {
                'cloudwatch': {
                    'config': {
                        'log_group_name': TEST_CLOUDWATCH_LOG_GROUP_NAME,
                        'log_stream_name': TEST_CLOUDWATCH_LOG_STREAM_NAME,
                        'aws_region': 'us-west-1',
                    }
                }
            }
        },
    )

    client = boto3.client('logs', 'us-west-1')

    now = millisecond_timestamp(datetime.datetime.utcnow())

    # This is implicitly assuming that we're not running these tests with too much concurrency, etc.
    events = client.get_log_events(
        endTime=now,
        logGroupName=TEST_CLOUDWATCH_LOG_GROUP_NAME,
        logStreamName=TEST_CLOUDWATCH_LOG_STREAM_NAME,
        limit=100,
    )['events']

    found_orig_message = False
    for parsed_msg in (json.loads(event['message']) for event in events):
        if parsed_msg['dagster_meta']['run_id'] == res.run_id:
            if parsed_msg['dagster_meta']['orig_message'] == 'Hello, Cloudwatch!':
                found_orig_message = True
                break

    assert found_orig_message
