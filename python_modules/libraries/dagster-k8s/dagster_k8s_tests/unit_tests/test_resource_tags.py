import pytest
from dagster_k8s.job import (
    K8S_RESOURCE_REQUIREMENTS_KEY,
    USER_DEFINED_K8S_CONFIG_KEY,
    UserDefinedDagsterK8sConfig,
    get_user_defined_k8s_config,
)

from dagster import DynamicOutput, DynamicOutputDefinition, pipeline, solid
from dagster.core.errors import DagsterInvalidConfigError
from dagster.core.execution.api import create_execution_plan
from dagster.core.execution.plan.state import KnownExecutionState


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


def test_tags_to_plan():
    @solid
    def blank(_):
        pass

    @pipeline
    def k8s_ready():
        blank.tag(
            {
                USER_DEFINED_K8S_CONFIG_KEY: {
                    "container_config": {
                        "resources": {
                            "requests": {"cpu": "250m", "memory": "64Mi"},
                            "limits": {"cpu": "500m", "memory": "2560Mi"},
                        }
                    }
                }
            }
        )()

    plan = create_execution_plan(k8s_ready)
    step = list(plan.step_dict.values())[0]

    user_defined_k8s_config = get_user_defined_k8s_config(step.tags)

    assert user_defined_k8s_config.container_config
    assert user_defined_k8s_config.container_config["resources"]
    resources = user_defined_k8s_config.container_config["resources"]
    assert resources["requests"]["cpu"] == "250m"
    assert resources["requests"]["memory"] == "64Mi"
    assert resources["limits"]["cpu"] == "500m"
    assert resources["limits"]["memory"] == "2560Mi"


def test_tags_to_dynamic_plan():
    @solid(
        tags={
            USER_DEFINED_K8S_CONFIG_KEY: {
                "container_config": {
                    "resources": {
                        "requests": {"cpu": "500m", "memory": "128Mi"},
                        "limits": {"cpu": "1000m", "memory": "1Gi"},
                    }
                }
            }
        }
    )
    def multiply_inputs(_, x):
        return 2 * x

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
        },
        output_defs=[DynamicOutputDefinition()],
    )
    def emit(_):
        for i in range(3):
            yield DynamicOutput(value=i, mapping_key=str(i))

    @pipeline
    def k8s_ready():
        return emit().map(multiply_inputs)

    known_state = KnownExecutionState(
        {},
        {
            emit.name: {"result": ["0", "1", "2"]},
        },
    )
    plan = create_execution_plan(k8s_ready, known_state=known_state)

    emit_step = plan.get_step_by_key(emit.name)
    user_defined_k8s_config = get_user_defined_k8s_config(emit_step.tags)

    assert user_defined_k8s_config.container_config
    assert user_defined_k8s_config.container_config["resources"]

    resources = user_defined_k8s_config.container_config["resources"]

    assert resources["requests"]["cpu"] == "250m"
    assert resources["requests"]["memory"] == "64Mi"
    assert resources["limits"]["cpu"] == "500m"
    assert resources["limits"]["memory"] == "2560Mi"

    for mapping_key in range(3):
        multiply_inputs_step = plan.get_step_by_key(f"{multiply_inputs.name}[{mapping_key}]")
        dynamic_step_user_defined_k8s_config = get_user_defined_k8s_config(
            multiply_inputs_step.tags
        )

        assert dynamic_step_user_defined_k8s_config.container_config
        assert dynamic_step_user_defined_k8s_config.container_config["resources"]

        resources = dynamic_step_user_defined_k8s_config.container_config["resources"]

        assert resources["requests"]["cpu"] == "500m"
        assert resources["requests"]["memory"] == "128Mi"
        assert resources["limits"]["cpu"] == "1000m"
        assert resources["limits"]["memory"] == "1Gi"


def test_bad_user_defined_k8s_config_tags():
    @pipeline(tags={USER_DEFINED_K8S_CONFIG_KEY: {"other": {}}})
    def my_pipeline():
        pass

    with pytest.raises(
        DagsterInvalidConfigError, match='Received unexpected config entry "other" at the root'
    ):
        get_user_defined_k8s_config(my_pipeline.tags)


def test_user_defined_config_from_tags():

    config_args = {
        "container_config": {
            "resources": {
                "requests": {"cpu": "500m", "memory": "128Mi"},
                "limits": {"cpu": "1000m", "memory": "1Gi"},
            }
        },
        "pod_template_spec_metadata": {"pod_template_spec_key": "pod_template_spec_value"},
        "pod_spec_config": {"pod_spec_config_key": "pod_spec_config_value"},
        "job_config": {"job_config_key": "job_config_value"},
        "job_metadata": {"job_metadata_key": "job_metadata_value"},
        "job_spec_config": {"job_spec_config_key": "job_spec_config_value"},
    }

    @pipeline(tags={USER_DEFINED_K8S_CONFIG_KEY: config_args})
    def my_pipeline():
        pass

    assert get_user_defined_k8s_config(my_pipeline.tags) == UserDefinedDagsterK8sConfig(
        **config_args
    )
