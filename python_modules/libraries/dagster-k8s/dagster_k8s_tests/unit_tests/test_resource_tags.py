import pytest
from dagster import pipeline, solid
from dagster.core.errors import DagsterInvalidConfigError
from dagster_k8s.job import (
    K8S_RESOURCE_REQUIREMENTS_KEY,
    USER_DEFINED_K8S_CONFIG_KEY,
    UserDefinedDagsterK8sConfig,
    get_user_defined_k8s_config,
)


# CPU units are millicpu
# Memory units are MiB
def test_backcompat_resource_tags():
    @solid(
        tags={
            K8S_RESOURCE_REQUIREMENTS_KEY: {
                "requests": {"cpu": "250m", "memory": "64Mi"},
                "limits": {"cpu": "500m", "memory": "2560Mi"},
            }
        }
    )
    def resource_tags_solid(_):
        pass

    user_defined_k8s_config = get_user_defined_k8s_config(resource_tags_solid.tags)

    assert user_defined_k8s_config.container_config
    assert user_defined_k8s_config.container_config["resources"]
    resources = user_defined_k8s_config.container_config["resources"]
    assert resources["requests"]["cpu"] == "250m"
    assert resources["requests"]["memory"] == "64Mi"
    assert resources["limits"]["cpu"] == "500m"
    assert resources["limits"]["memory"] == "2560Mi"


def test_bad_deprecated_resource_tags():
    @pipeline(
        tags={
            K8S_RESOURCE_REQUIREMENTS_KEY: {
                "other": {"cpu": "250m", "memory": "64Mi"},
            }
        }
    )
    def resource_tags_pipeline():
        pass

    with pytest.raises(DagsterInvalidConfigError):
        get_user_defined_k8s_config(resource_tags_pipeline.tags)


def test_user_defined_k8s_config_tags():
    @solid(
        tags={
            USER_DEFINED_K8S_CONFIG_KEY: {
                "container_config": {
                    "resources": {
                        "requests": {"cpu": "250m", "memory": "64Mi"},
                        "limits": {"cpu": "500m", "memory": "2560Mi"},
                    }
                }
            }
        }
    )
    def my_solid(_):
        pass

    user_defined_k8s_config = get_user_defined_k8s_config(my_solid.tags)

    assert user_defined_k8s_config.container_config
    assert user_defined_k8s_config.container_config["resources"]
    resources = user_defined_k8s_config.container_config["resources"]
    assert resources["requests"]["cpu"] == "250m"
    assert resources["requests"]["memory"] == "64Mi"
    assert resources["limits"]["cpu"] == "500m"
    assert resources["limits"]["memory"] == "2560Mi"

    @solid
    def no_resource_tags_solid(_):
        pass

    user_defined_k8s_config = get_user_defined_k8s_config(no_resource_tags_solid.tags)
    assert user_defined_k8s_config == UserDefinedDagsterK8sConfig()


def test_bad_user_defined_k8s_config_tags():
    @pipeline(tags={USER_DEFINED_K8S_CONFIG_KEY: {"other": {}}})
    def my_solid():
        pass

    with pytest.raises(DagsterInvalidConfigError):
        get_user_defined_k8s_config(my_solid.tags)
