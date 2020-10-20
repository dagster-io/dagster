import pytest
from dagster import check
from dagster.core.test_utils import environ
from dagster_celery_k8s.config import get_celery_engine_config
from dagster_celery_k8s.executor import CELERY_K8S_CONFIG_KEY
from dagster_celery_k8s.launcher import _get_validated_celery_k8s_executor_config


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
        check.CheckError,
        match="Description: celery-k8s execution must be configured in pipeline execution config to"
        " launch runs with CeleryK8sRunLauncher",
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
