import os
import uuid

import pytest

from dagster.core.storage.pipeline_run import PipelineRun
from dagster.utils import load_yaml_from_path

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
    assert result['data']['startPipelineExecution']['__typename'] == 'StartPipelineExecutionSuccess'


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
        result['data']['startPipelineExecution']['__typename'] == 'PipelineConfigValidationInvalid'
    )
    assert len(result['data']['startPipelineExecution']['errors']) == 2

    assert set(error['reason'] for error in result['data']['startPipelineExecution']['errors']) == {
        'FIELD_NOT_DEFINED',
        'MISSING_REQUIRED_FIELD',
    }
