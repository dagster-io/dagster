import json

import pytest
from dagster_k8s.job import K8S_RESOURCE_REQUIREMENTS_KEY, get_k8s_resource_requirements

from dagster import pipeline, solid
from dagster.core.errors import DagsterInvalidConfigError


# CPU units are millicpu
# Memory units are MiB
def test_resource_tags():
    @solid(
        tags={
            K8S_RESOURCE_REQUIREMENTS_KEY: {
                'requests': {'cpu': '250m', 'memory': '64Mi'},
                'limits': {'cpu': '500m', 'memory': '2560Mi'},
            }
        }
    )
    def resource_tags_solid(_):
        pass

    resources = get_k8s_resource_requirements(resource_tags_solid.tags)

    assert resources == json.loads(json.dumps(resources))
    assert resources['requests']['cpu'] == '250m'
    assert resources['requests']['memory'] == '64Mi'
    assert resources['limits']['cpu'] == '500m'
    assert resources['limits']['memory'] == '2560Mi'

    @solid
    def no_resource_tags_solid(_):
        pass

    no_resources = get_k8s_resource_requirements(no_resource_tags_solid.tags)
    assert no_resources == None


def test_pipeline_resource_tags():
    @pipeline(
        tags={
            K8S_RESOURCE_REQUIREMENTS_KEY: {
                'requests': {'cpu': '250m', 'memory': '64Mi'},
                'limits': {'cpu': '500m', 'memory': '2560Mi'},
            }
        }
    )
    def resource_tags_pipeline():
        pass

    resources = get_k8s_resource_requirements(resource_tags_pipeline.tags)

    assert resources == json.loads(json.dumps(resources))
    assert resources['requests']['cpu'] == '250m'
    assert resources['requests']['memory'] == '64Mi'
    assert resources['limits']['cpu'] == '500m'
    assert resources['limits']['memory'] == '2560Mi'

    @pipeline
    def no_resource_tags_pipeline():
        pass

    no_resources = get_k8s_resource_requirements(no_resource_tags_pipeline.tags)
    assert no_resources == None


def test_bad_resource_tags():
    @pipeline(tags={K8S_RESOURCE_REQUIREMENTS_KEY: {'other': {'cpu': '250m', 'memory': '64Mi'},}})
    def resource_tags_pipeline():
        pass

    with pytest.raises(DagsterInvalidConfigError):
        get_k8s_resource_requirements(resource_tags_pipeline.tags)
