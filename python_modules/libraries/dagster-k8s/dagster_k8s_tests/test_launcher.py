import os
import uuid

import yaml

from dagster.core.storage.pipeline_run import PipelineRun
from dagster.utils import load_yaml_from_path

from .conftest import docker_image, environments_path  # pylint: disable=unused-import
from .utils import parse_raw_res, remove_none_recursively, wait_for_job_success

EXPECTED_JOB_SPEC = '''
api_version: batch/v1
kind: Job
metadata:
  labels:
    app.kubernetes.io/instance: dagster
    app.kubernetes.io/name: dagster
    app.kubernetes.io/version: 0.6.6
  name: dagster-job-{run_id}
spec:
  backoff_limit: 4
  template:
    metadata:
      labels:
        app.kubernetes.io/instance: dagster
        app.kubernetes.io/name: dagster
        app.kubernetes.io/version: 0.6.6
      name: dagster-job-pod-{run_id}
    spec:
      containers:
      - args:
        - -p
        - startPipelineExecution
        - -v
        - '{{"executionParams": {{"environmentConfigData": {{"loggers": {{"console": {{"config":
          {{"log_level": "DEBUG"}}}}}}, "solids": {{"multiply_the_word": {{"config": {{"factor":
          2}}, "inputs": {{"word": {{"value": "bar"}}}}}}}}}}, "mode": "default", "selector":
          {{"name": "demo_pipeline", "solidSubset": null}}}}}}'
        command:
        - dagster-graphql
        env:
        - name: DAGSTER_HOME
          value: /opt/dagster/dagster_home
        image: {job_image}
        image_pull_policy: IfNotPresent
        name: dagster-job-{run_id}
        volume_mounts:
        - mount_path: /opt/dagster/dagster_home/dagster.yaml
          name: dagster-instance
          sub_path: dagster.yaml
      image_pull_secrets:
      - name: element-dev-key
      init_containers:
      - command:
        - sh
        - -c
        - until pg_isready -h dagster-postgresql -p 5432; do echo waiting for database;
          sleep 2; done;
        image: postgres:9.6.16
        name: check-db-ready
      restart_policy: Never
      service_account_name: dagit-admin
      volumes:
      - config_map:
          name: dagster-instance
        name: dagster-instance
'''


def test_valid_job_format(
    run_launcher, docker_image, environments_path
):  # pylint: disable=redefined-outer-name
    run_id = uuid.uuid4().hex
    environment_dict = load_yaml_from_path(os.path.join(environments_path, 'env.yaml'))
    pipeline_name = 'demo_pipeline'
    run = PipelineRun.create_empty_run(pipeline_name, run_id, environment_dict)
    job = run_launcher.construct_job(run)

    assert (
        yaml.dump(remove_none_recursively(job.to_dict()), default_flow_style=False).strip()
        == EXPECTED_JOB_SPEC.format(run_id=run_id, job_image=docker_image).strip()
    )


def test_k8s_run_launcher(run_launcher, environments_path):  # pylint: disable=redefined-outer-name
    run_id = uuid.uuid4().hex
    environment_dict = load_yaml_from_path(os.path.join(environments_path, 'env.yaml'))
    pipeline_name = 'demo_pipeline'
    run = PipelineRun.create_empty_run(pipeline_name, run_id, environment_dict)

    run_launcher.launch_run(run)
    success, raw_logs = wait_for_job_success('dagster-job-%s' % run_id)
    result = parse_raw_res(raw_logs.split('\n'))

    assert success
    assert not result.get('errors')
    assert result['data']
    assert result['data']['startPipelineExecution']['__typename'] == 'StartPipelineExecutionSuccess'


def test_failing_k8s_run_launcher(run_launcher):
    run_id = uuid.uuid4().hex
    environment_dict = {'blah blah this is wrong': {}}
    pipeline_name = 'demo_pipeline'
    run = PipelineRun.create_empty_run(pipeline_name, run_id, environment_dict)

    run_launcher.launch_run(run)
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
