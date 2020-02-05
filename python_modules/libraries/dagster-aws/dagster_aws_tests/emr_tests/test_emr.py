import copy
import gzip
import io
import threading
import time

import boto3
import pytest
from dagster_aws.emr import EmrClusterState, EmrError, EmrJobRunner
from dagster_aws.utils.mrjob.utils import _boto3_now
from moto import mock_emr, mock_s3

from dagster.seven import mock
from dagster.utils.test import create_test_pipeline_execution_context

REGION = 'us-west-1'


@mock_emr
def test_emr_create_cluster(emr_cluster_config):
    context = create_test_pipeline_execution_context()
    cluster = EmrJobRunner(region=REGION)
    cluster_id = cluster.run_job_flow(context, emr_cluster_config)
    assert cluster_id.startswith('j-')


@mock_emr
def test_emr_add_tags_and_describe_cluster(emr_cluster_config):
    context = create_test_pipeline_execution_context()
    emr = EmrJobRunner(region=REGION)

    cluster_id = emr.run_job_flow(context, emr_cluster_config)

    emr.add_tags(context, {'foobar': 'v1', 'baz': '123'}, cluster_id)

    tags = emr.describe_cluster(cluster_id)['Cluster']['Tags']

    assert {'Key': 'baz', 'Value': '123'} in tags
    assert {'Key': 'foobar', 'Value': 'v1'} in tags


@mock_emr
def test_emr_describe_cluster(emr_cluster_config):
    context = create_test_pipeline_execution_context()
    cluster = EmrJobRunner(region=REGION)
    cluster_id = cluster.run_job_flow(context, emr_cluster_config)
    cluster_info = cluster.describe_cluster(cluster_id)['Cluster']
    assert cluster_info['Name'] == 'test-emr'
    assert EmrClusterState(cluster_info['Status']['State']) == EmrClusterState.Waiting


@mock_emr
def test_emr_id_from_name(emr_cluster_config):
    context = create_test_pipeline_execution_context()
    cluster = EmrJobRunner(region=REGION)
    cluster_id = cluster.run_job_flow(context, emr_cluster_config)
    assert cluster.cluster_id_from_name('test-emr') == cluster_id

    with pytest.raises(EmrError) as exc_info:
        cluster.cluster_id_from_name('cluster-doesnt-exist')

    assert 'cluster cluster-doesnt-exist not found in region us-west-1' in str(exc_info.value)


def test_emr_construct_step_dict():
    cmd = ['pip', 'install', 'dagster']

    assert EmrJobRunner.construct_step_dict_for_command('test_step', cmd) == {
        'Name': 'test_step',
        'ActionOnFailure': 'CONTINUE',
        'HadoopJarStep': {'Jar': 'command-runner.jar', 'Args': cmd},
    }

    assert EmrJobRunner.construct_step_dict_for_command(
        'test_second_step', cmd, action_on_failure='CANCEL_AND_WAIT'
    ) == {
        'Name': 'test_second_step',
        'ActionOnFailure': 'CANCEL_AND_WAIT',
        'HadoopJarStep': {'Jar': 'command-runner.jar', 'Args': cmd},
    }


@mock_emr
def test_emr_log_location_for_cluster(emr_cluster_config):
    context = create_test_pipeline_execution_context()
    emr = EmrJobRunner(region=REGION)
    cluster_id = emr.run_job_flow(context, emr_cluster_config)
    assert emr.log_location_for_cluster(cluster_id) == ('emr-cluster-logs', 'elasticmapreduce/')

    # Should raise when the log URI is missing
    emr_cluster_config = copy.deepcopy(emr_cluster_config)
    del emr_cluster_config['LogUri']
    cluster_id = emr.run_job_flow(context, emr_cluster_config)
    with pytest.raises(EmrError) as exc_info:
        emr.log_location_for_cluster(cluster_id)

    assert 'Log URI not specified, cannot retrieve step execution logs' in str(exc_info.value)


@mock_emr
@mock_s3
def test_emr_retrieve_logs(emr_cluster_config):
    context = create_test_pipeline_execution_context()
    emr = EmrJobRunner(region=REGION)
    cluster_id = emr.run_job_flow(context, emr_cluster_config)
    assert emr.log_location_for_cluster(cluster_id) == ('emr-cluster-logs', 'elasticmapreduce/')

    s3 = boto3.resource('s3', region_name=REGION)
    s3.create_bucket(Bucket='emr-cluster-logs')  # pylint: disable=no-member

    def create_log():
        time.sleep(0.5)
        out = io.BytesIO()
        with gzip.GzipFile(fileobj=out, mode='w') as fo:
            fo.write('some log'.encode())

        prefix = 'elasticmapreduce/{cluster_id}/steps/{step_id}'.format(
            cluster_id=cluster_id, step_id='s-123456123456'
        )

        for name in ['stdout.gz', 'stderr.gz']:
            s3.Object('emr-cluster-logs', prefix + '/' + name).put(  # pylint: disable=no-member
                Body=out.getvalue()
            )

    thread = threading.Thread(target=create_log, args=())
    thread.daemon = True
    thread.start()

    stdout_log, stderr_log = emr.retrieve_logs_for_step_id(context, cluster_id, 's-123456123456')
    assert stdout_log == 'some log'
    assert stderr_log == 'some log'


@mock_s3
def test_wait_for_log():
    s3 = boto3.resource('s3', region_name=REGION)
    s3.create_bucket(Bucket='log_bucket')  # pylint: disable=no-member

    def create_log():
        time.sleep(0.5)
        out = io.BytesIO()
        with gzip.GzipFile(fileobj=out, mode='w') as fo:
            fo.write('foo bar'.encode())

        s3.Object('log_bucket', 'some_log_file').put(  # pylint: disable=no-member
            Body=out.getvalue()
        )

    thread = threading.Thread(target=create_log, args=())
    thread.daemon = True
    thread.start()

    context = create_test_pipeline_execution_context()
    emr = EmrJobRunner(region=REGION)
    res = emr.wait_for_log(
        context,
        log_bucket='log_bucket',
        log_key='some_log_file',
        waiter_delay=1,
        waiter_max_attempts=2,
    )
    assert res == 'foo bar'

    with pytest.raises(EmrError) as exc_info:
        emr.wait_for_log(
            context,
            log_bucket='log_bucket',
            log_key='does_not_exist',
            waiter_delay=1,
            waiter_max_attempts=1,
        )
    assert 'EMR log file did not appear on S3 after waiting' in str(exc_info.value)


@mock_emr
def test_emr_wait_for_step(emr_cluster_config):
    context = create_test_pipeline_execution_context()
    emr = EmrJobRunner(region=REGION, check_cluster_every=1)

    cluster_id = emr.run_job_flow(context, emr_cluster_config)

    step_name = 'test_step'
    step_cmd = ['ls', '/']
    step_ids = emr.add_job_flow_steps(
        context, cluster_id, [emr.construct_step_dict_for_command(step_name, step_cmd)]
    )

    def get_step_dict(step_id, step_state):
        return {
            'Step': {
                'Id': step_id,
                'Name': step_name,
                'Config': {'Jar': 'command-runner.jar', 'Properties': {}, 'Args': step_cmd},
                'ActionOnFailure': 'CONTINUE',
                'Status': {
                    'State': step_state,
                    'StateChangeReason': {'Message': 'everything is hosed'},
                    'Timeline': {'StartDateTime': _boto3_now()},
                },
            },
        }

    calls = {'num_calls': 0, 'final_state': 'COMPLETED'}

    def new_describe_step(_, cluster_id, step_id):
        calls['num_calls'] += 1

        if calls['num_calls'] == 1:
            return get_step_dict(step_id, 'PENDING')
        elif calls['num_calls'] == 2:
            return get_step_dict(step_id, 'RUNNING')
        else:
            return get_step_dict(step_id, calls['final_state'])

        return emr.describe_step(cluster_id, step_id)

    with mock.patch.object(EmrJobRunner, 'describe_step', new=new_describe_step):
        emr.wait_for_steps_to_complete(context, cluster_id, step_ids)

    calls['num_calls'] = 0
    calls['final_state'] = 'FAILED'
    with pytest.raises(EmrError) as exc_info:
        with mock.patch.object(EmrJobRunner, 'describe_step', new=new_describe_step):
            emr.wait_for_steps_to_complete(context, cluster_id, step_ids)
    assert 'step failed' in str(exc_info.value)
