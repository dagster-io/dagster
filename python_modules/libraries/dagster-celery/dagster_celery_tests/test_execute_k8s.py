# pylint doesn't know about pytest fixtures
# pylint: disable=unused-argument

import os
import sys

import pytest
from dagster_k8s_tests.utils import wait_for_job_and_get_logs

from dagster.utils import git_repository_root, merge_dicts
from dagster.utils.yaml_utils import merge_yamls

sys.path.append(os.path.join(git_repository_root(), 'python_modules', 'libraries', 'dagster-k8s'))
from dagster_k8s_tests.cluster import (  # isort:skip, pylint:disable=unused-import
    dagster_instance,
    run_launcher,
)
from dagster_k8s_tests.test_project import test_project_environments_path  # isort:skip


@pytest.mark.integration
@pytest.mark.skipif(sys.version_info < (3, 5), reason="Very slow on Python 2")
def test_execute_on_celery(  # pylint: disable=redefined-outer-name
    dagster_docker_image, dagster_instance, helm_namespace
):
    environment_dict = merge_dicts(
        merge_yamls(
            [
                os.path.join(test_project_environments_path(), 'env.yaml'),
                os.path.join(test_project_environments_path(), 'env_s3.yaml'),
            ]
        ),
        {
            'execution': {
                'celery-k8s': {
                    'config': {
                        'broker': {'env': 'DAGSTER_K8S_CELERY_BROKER'},
                        'backend': {'env': 'DAGSTER_K8S_CELERY_BACKEND'},
                        'job_image': dagster_docker_image,
                        'job_namespace': helm_namespace,
                        'instance_config_map': 'dagster-instance',
                        'postgres_password_secret': 'dagster-postgresql-secret',
                        'image_pull_policy': 'Always',
                        'env_config_maps': ['dagster-job-runner-env'],
                    }
                }
            },
        },
    )

    pipeline_name = 'demo_pipeline_celery'
    run = dagster_instance.create_run(
        pipeline_name=pipeline_name, environment_dict=environment_dict, mode='default'
    )

    dagster_instance.launch_run(run.run_id)

    result = wait_for_job_and_get_logs(
        job_name='dagster-run-%s' % run.run_id, namespace=helm_namespace
    )

    assert not result.get('errors')
    assert result['data']
    assert (
        result['data']['startPipelineExecutionForCreatedRun']['__typename']
        == 'StartPipelineRunSuccess'
    )
