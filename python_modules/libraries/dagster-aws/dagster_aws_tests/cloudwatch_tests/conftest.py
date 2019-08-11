import boto3
import pytest

TEST_CLOUDWATCH_LOG_GROUP_NAME = '/dagster-test/test-cloudwatch-logging'
TEST_CLOUDWATCH_LOG_STREAM_NAME = 'test-logging'
AWS_REGION = 'us-west-1'


@pytest.fixture(scope='session')
def cloudwatch_client():
    client = boto3.client('logs', AWS_REGION)
    client.describe_log_groups(logGroupNamePrefix=TEST_CLOUDWATCH_LOG_GROUP_NAME)
    res = client.describe_log_streams(
        logGroupName=TEST_CLOUDWATCH_LOG_GROUP_NAME,
        logStreamNamePrefix=TEST_CLOUDWATCH_LOG_STREAM_NAME,
    )
    assert TEST_CLOUDWATCH_LOG_STREAM_NAME in (
        log_stream['logStreamName'] for log_stream in res['logStreams']
    )
    yield client
