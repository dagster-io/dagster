import json

import pytest
from dagster import pipeline, reconstructable
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.host_representation import (
    InProcessRepositoryLocationOrigin,
    RepositoryHandle,
    RepositoryLocationHandle,
)
from dagster.core.test_utils import create_run_for_test, environ, instance_for_test
from dagster.seven import mock
from dagster.utils.hosted_user_process import external_pipeline_from_recon_pipeline
from dagster_celery_k8s.config import get_celery_engine_config
from dagster_celery_k8s.executor import CELERY_K8S_CONFIG_KEY
from dagster_celery_k8s.launcher import (
    CeleryK8sRunLauncher,
    _get_validated_celery_k8s_executor_config,
)
from dagster_k8s.job import UserDefinedDagsterK8sConfig


def test_get_validated_celery_k8s_executor_config():
    res = _get_validated_celery_k8s_executor_config(
        {"execution": {CELERY_K8S_CONFIG_KEY: {"config": {"job_image": "foo"}}}}
    )

    assert res == {
        "backend": "rpc://",
        "retries": {"enabled": {}},
        "job_image": "foo",
        "image_pull_policy": "IfNotPresent",
        "load_incluster_config": True,
        "job_namespace": "default",
        "repo_location_name": "<<in_process>>",
    }

    with pytest.raises(
        DagsterInvariantViolationError,
        match="celery-k8s execution configuration must be present in the run config to use the CeleryK8sRunLauncher.",
    ):
        _get_validated_celery_k8s_executor_config({})

    with environ(
        {
            "DAGSTER_K8S_PIPELINE_RUN_IMAGE": "foo",
            "DAGSTER_K8S_PIPELINE_RUN_NAMESPACE": "default",
            "DAGSTER_K8S_PIPELINE_RUN_IMAGE_PULL_POLICY": "Always",
            "DAGSTER_K8S_PIPELINE_RUN_ENV_CONFIGMAP": "config-pipeline-env",
        }
    ):
        cfg = get_celery_engine_config()
        res = _get_validated_celery_k8s_executor_config(cfg)
        assert res == {
            "backend": "rpc://",
            "retries": {"enabled": {}},
            "job_image": "foo",
            "image_pull_policy": "Always",
            "env_config_maps": ["config-pipeline-env"],
            "load_incluster_config": True,
            "job_namespace": "default",
            "repo_location_name": "<<in_process>>",
        }

    # Test setting all possible config fields
    with environ(
        {
            "TEST_PIPELINE_RUN_NAMESPACE": "default",
            "TEST_CELERY_BROKER": "redis://some-redis-host:6379/0",
            "TEST_CELERY_BACKEND": "redis://some-redis-host:6379/0",
            "TEST_PIPELINE_RUN_IMAGE": "foo",
            "TEST_PIPELINE_RUN_IMAGE_PULL_POLICY": "Always",
            "TEST_K8S_PULL_SECRET_1": "super-secret-1",
            "TEST_K8S_PULL_SECRET_2": "super-secret-2",
            "TEST_SERVICE_ACCOUNT_NAME": "my-cool-service-acccount",
            "TEST_PIPELINE_RUN_ENV_CONFIGMAP": "config-pipeline-env",
            "TEST_SECRET": "config-secret-env",
        }
    ):

        cfg = {
            "execution": {
                CELERY_K8S_CONFIG_KEY: {
                    "config": {
                        "repo_location_name": "<<in_process>>",
                        "load_incluster_config": False,
                        "kubeconfig_file": "/some/kubeconfig/file",
                        "job_namespace": {"env": "TEST_PIPELINE_RUN_NAMESPACE"},
                        "broker": {"env": "TEST_CELERY_BROKER"},
                        "backend": {"env": "TEST_CELERY_BACKEND"},
                        "include": ["dagster", "dagit"],
                        "config_source": {
                            "task_annotations": """{'*': {'on_failure': my_on_failure}}"""
                        },
                        "retries": {"disabled": {}},
                        "job_image": {"env": "TEST_PIPELINE_RUN_IMAGE"},
                        "image_pull_policy": {"env": "TEST_PIPELINE_RUN_IMAGE_PULL_POLICY"},
                        "image_pull_secrets": [
                            {"name": {"env": "TEST_K8S_PULL_SECRET_1"}},
                            {"name": {"env": "TEST_K8S_PULL_SECRET_2"}},
                        ],
                        "service_account_name": {"env": "TEST_SERVICE_ACCOUNT_NAME"},
                        "env_config_maps": [{"env": "TEST_PIPELINE_RUN_ENV_CONFIGMAP"}],
                        "env_secrets": [{"env": "TEST_SECRET"}],
                    }
                }
            }
        }

        res = _get_validated_celery_k8s_executor_config(cfg)
        assert res == {
            "repo_location_name": "<<in_process>>",
            "load_incluster_config": False,
            "kubeconfig_file": "/some/kubeconfig/file",
            "job_namespace": "default",
            "backend": "redis://some-redis-host:6379/0",
            "broker": "redis://some-redis-host:6379/0",
            "include": ["dagster", "dagit"],
            "config_source": {"task_annotations": """{'*': {'on_failure': my_on_failure}}"""},
            "retries": {"disabled": {}},
            "job_image": "foo",
            "image_pull_policy": "Always",
            "image_pull_secrets": [{"name": "super-secret-1"}, {"name": "super-secret-2"}],
            "service_account_name": "my-cool-service-acccount",
            "env_config_maps": ["config-pipeline-env"],
            "env_secrets": ["config-secret-env"],
        }


def test_user_defined_k8s_config_in_run_tags(kubeconfig_file):
    # Construct a K8s run launcher in a fake k8s environment.
    mock_k8s_client_batch_api = mock.MagicMock()
    celery_k8s_run_launcher = CeleryK8sRunLauncher(
        instance_config_map="dagster-instance",
        postgres_password_secret="dagster-postgresql-secret",
        dagster_home="/opt/dagster/dagster_home",
        load_incluster_config=False,
        kubeconfig_file=kubeconfig_file,
        k8s_client_batch_api=mock_k8s_client_batch_api,
    )

    # Construct Dagster run tags with user defined k8s config.
    expected_resources = {
        "requests": {"cpu": "250m", "memory": "64Mi"},
        "limits": {"cpu": "500m", "memory": "2560Mi"},
    }
    user_defined_k8s_config = UserDefinedDagsterK8sConfig(
        container_config={"resources": expected_resources},
    )
    user_defined_k8s_config_json = json.dumps(user_defined_k8s_config.to_dict())
    tags = {"dagster-k8s/config": user_defined_k8s_config_json}

    # Create fake external pipeline.
    recon_pipeline = reconstructable(fake_pipeline)
    recon_repo = recon_pipeline.repository
    location_origin = InProcessRepositoryLocationOrigin(recon_repo)
    location_handle = RepositoryLocationHandle.create_from_repository_location_origin(
        location_origin,
    )
    repo_def = recon_repo.get_definition()
    repo_handle = RepositoryHandle(
        repository_name=repo_def.name,
        repository_location_handle=location_handle,
    )
    fake_external_pipeline = external_pipeline_from_recon_pipeline(
        recon_pipeline,
        solid_selection=None,
        repository_handle=repo_handle,
    )

    # Launch the run in a fake Dagster instance.
    with instance_for_test() as instance:
        celery_k8s_run_launcher.initialize(instance)
        pipeline_name = "demo_pipeline"
        run_config = {"execution": {"celery-k8s": {"config": {"job_image": "fake-image-name"}}}}
        run = create_run_for_test(
            instance,
            pipeline_name=pipeline_name,
            run_config=run_config,
            tags=tags,
        )
        celery_k8s_run_launcher.launch_run(instance, run, fake_external_pipeline)

    # Check that user defined k8s config was passed down to the k8s job.
    mock_method_calls = mock_k8s_client_batch_api.method_calls
    assert len(mock_method_calls) > 0
    method_name, _args, kwargs = mock_method_calls[0]
    assert method_name == "create_namespaced_job"
    job_resources = kwargs["body"].spec.template.spec.containers[0].resources
    assert job_resources == expected_resources


@pipeline
def fake_pipeline():
    pass
