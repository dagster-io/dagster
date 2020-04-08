import os
import uuid

import pytest
from dagster_k8s import get_celery_engine_config

from dagster.core.storage.pipeline_run import PipelineRun
from dagster.utils import load_yaml_from_path, merge_dicts
from dagster.utils.yaml_utils import merge_yamls

from .conftest import environments_path
from .utils import parse_raw_res, wait_for_job_success


@pytest.mark.integration
def test_k8s_run_launcher(dagster_instance):  # pylint: disable=redefined-outer-name
    run_id = uuid.uuid4().hex
    environment_dict = load_yaml_from_path(os.path.join(environments_path(), 'env.yaml'))
    pipeline_name = 'demo_pipeline'
    tags = {'key': 'value'}
    run = PipelineRun.create_empty_run(pipeline_name, run_id, environment_dict, tags)

    dagster_instance.launch_run(run)
    success, raw_logs = wait_for_job_success('dagster-job-%s' % run_id)
    result = parse_raw_res(raw_logs.split('\n'))

    assert success
    assert not result.get('errors')
    assert result['data']
    assert (
        result['data']['startPipelineExecutionForCreatedRun']['__typename']
        == 'StartPipelineExecutionSuccess'
    )
    assert 'PipelineSuccessEvent' in {
        log['__typename']: log
        for log in result['data']['startPipelineExecutionForCreatedRun']['run']['logs']['nodes']
    }


@pytest.mark.integration
def test_k8s_run_launcher_celery(dagster_instance):  # pylint: disable=redefined-outer-name
    run_id = uuid.uuid4().hex
    environment_dict = merge_dicts(
        merge_yamls(
            [
                os.path.join(environments_path(), 'env.yaml'),
                os.path.join(environments_path(), 'env_filesystem.yaml'),
            ]
        ),
        get_celery_engine_config(),
    )

    assert 'celery' in environment_dict['execution']

    pipeline_name = 'demo_pipeline_celery'
    tags = {'key': 'value'}
    run = PipelineRun.create_empty_run(pipeline_name, run_id, environment_dict, tags)

    dagster_instance.launch_run(run)
    success, raw_logs = wait_for_job_success('dagster-job-%s' % run_id)
    result = parse_raw_res(raw_logs.split('\n'))

    assert success
    assert not result.get('errors')
    assert result['data']
    # this is bad test but proves that we got celery configured properly
    # to get it working would involve relying on s3 / gcs for storage
    assert result['data']['startPipelineExecutionForCreatedRun']['__typename'] == 'PythonError'
    assert (
        'Must use S3 or GCS storage with non-local Celery broker: pyamqp://test:test@dagster-rabbitmq:5672// and backend: amqp'
        in result['data']['startPipelineExecutionForCreatedRun']['message']
    )


@pytest.mark.integration
def test_failing_k8s_run_launcher(dagster_instance):
    run_id = uuid.uuid4().hex
    environment_dict = {'blah blah this is wrong': {}}
    pipeline_name = 'demo_pipeline'
    run = PipelineRun.create_empty_run(pipeline_name, run_id, environment_dict)

    dagster_instance.launch_run(run)
    success, raw_logs = wait_for_job_success('dagster-job-%s' % run_id)
    result = parse_raw_res(raw_logs.split('\n'))

    assert success
    assert not result.get('errors')
    assert result['data']
    assert (
        result['data']['startPipelineExecutionForCreatedRun']['__typename']
        == 'PipelineConfigValidationInvalid'
    )
    assert len(result['data']['startPipelineExecutionForCreatedRun']['errors']) == 2

    assert set(
        error['reason'] for error in result['data']['startPipelineExecutionForCreatedRun']['errors']
    ) == {'FIELD_NOT_DEFINED', 'MISSING_REQUIRED_FIELD',}
