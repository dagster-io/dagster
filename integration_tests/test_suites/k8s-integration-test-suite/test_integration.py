import datetime
import os
import time

import pytest
from dagster_k8s.test import wait_for_job_and_get_raw_logs
from dagster_k8s.utils import wait_for_job
from dagster_test.test_project import (
    ReOriginatedExternalPipelineForTest,
    get_test_project_external_pipeline,
    test_project_environments_path,
)

from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.core.test_utils import create_run_for_test
from dagster.utils import load_yaml_from_path


@pytest.mark.integration
def test_k8s_run_launcher_default(dagster_instance, helm_namespace):
    run_config = load_yaml_from_path(os.path.join(test_project_environments_path(), "env.yaml"))
    pipeline_name = "demo_pipeline"
    tags = {"key": "value"}
    run = create_run_for_test(
        dagster_instance,
        pipeline_name=pipeline_name,
        run_config=run_config,
        tags=tags,
        mode="default",
    )

    dagster_instance.launch_run(
        run.run_id,
        ReOriginatedExternalPipelineForTest(get_test_project_external_pipeline(pipeline_name)),
    )

    result = wait_for_job_and_get_raw_logs(
        job_name="dagster-run-%s" % run.run_id, namespace=helm_namespace
    )

    assert "PIPELINE_SUCCESS" in result, "no match, result: {}".format(result)


@pytest.mark.integration
def test_failing_k8s_run_launcher(dagster_instance, helm_namespace):
    run_config = {"blah blah this is wrong": {}}
    pipeline_name = "demo_pipeline"
    run = create_run_for_test(dagster_instance, pipeline_name=pipeline_name, run_config=run_config)

    dagster_instance.launch_run(
        run.run_id,
        ReOriginatedExternalPipelineForTest(get_test_project_external_pipeline(pipeline_name)),
    )
    result = wait_for_job_and_get_raw_logs(
        job_name="dagster-run-%s" % run.run_id, namespace=helm_namespace
    )

    assert "PIPELINE_SUCCESS" not in result, "no match, result: {}".format(result)

    event_records = dagster_instance.all_logs(run.run_id)

    assert any(
        ['Undefined field "blah blah this is wrong"' in str(event) for event in event_records]
    )
    assert any(['Missing required field "solids"' in str(event) for event in event_records])


@pytest.mark.integration
def test_k8s_run_launcher_terminate(dagster_instance, helm_namespace):
    pipeline_name = "slow_pipeline"

    tags = {"key": "value"}
    run = create_run_for_test(
        dagster_instance, pipeline_name=pipeline_name, run_config=None, tags=tags, mode="default",
    )

    dagster_instance.launch_run(
        run.run_id,
        ReOriginatedExternalPipelineForTest(get_test_project_external_pipeline(pipeline_name)),
    )

    wait_for_job(job_name="dagster-run-%s" % run.run_id, namespace=helm_namespace)

    timeout = datetime.timedelta(0, 30)
    start_time = datetime.datetime.now()
    while datetime.datetime.now() < start_time + timeout:
        if dagster_instance.run_launcher.can_terminate(run_id=run.run_id):
            break
        time.sleep(5)

    assert dagster_instance.run_launcher.can_terminate(run_id=run.run_id)
    assert dagster_instance.run_launcher.terminate(run_id=run.run_id)

    start_time = datetime.datetime.now()
    pipeline_run = None
    while datetime.datetime.now() < start_time + timeout:
        pipeline_run = dagster_instance.get_run_by_id(run.run_id)
        if pipeline_run.status == PipelineRunStatus.FAILURE:
            break
        time.sleep(5)

    assert pipeline_run.status == PipelineRunStatus.FAILURE

    assert not dagster_instance.run_launcher.terminate(run_id=run.run_id)
