import json
import subprocess
from typing import List

import pytest
from kubernetes.client import models
from schema.subschema import kubernetes
from schema.subschema.user_deployments import UserDeployment, UserDeployments
from schema.values import HelmValues

from .helm_template import HelmTemplate


@pytest.fixture(name="template")
def helm_template() -> HelmTemplate:
    return HelmTemplate(output="templates/deployment-user.yaml", model=models.V1Deployment)


def create_simple_user_deployment(name: str) -> UserDeployment:
    return UserDeployment(
        name=name,
        image=kubernetes.Image(repository=f"repo/{name}", tag="tag1", pullPolicy="Always"),
        dagsterApiGrpcArgs=["-m", name],
        port=3030,
    )


def create_complex_user_deployment(name: str) -> UserDeployment:
    return UserDeployment(
        name=name,
        image=kubernetes.Image(repository=f"repo/{name}", tag="tag1", pullPolicy="Always"),
        dagsterApiGrpcArgs=["-m", name],
        port=3030,
        annotations=kubernetes.Annotations.parse_obj(
            {"annotation_1": "an_annotation_1", "annotation_2": "an_annotation_2"}
        ),
        nodeSelector=kubernetes.NodeSelector.parse_obj(
            {"node_selector_1": "node_type_1", "node_selector_2": "node_type_2"}
        ),
        affinity=kubernetes.Affinity.parse_obj(
            {
                "nodeAffinity": {
                    "requiredDuringSchedulingIgnoredDuringExecution": {
                        "nodeSelectorTerms": [
                            {
                                "matchExpressions": [
                                    {
                                        "key": "kubernetes.io/e2e-az-name",
                                        "operator": "In",
                                        "values": ["e2e-az1", "e2e-az2"],
                                    }
                                ]
                            }
                        ]
                    }
                }
            }
        ),
        tolerations=kubernetes.Tolerations.parse_obj(
            [{"key": "key1", "operator": "Exists", "effect": "NoSchedule"}]
        ),
        podSecurityContext=kubernetes.PodSecurityContext.parse_obj(
            {"runAsUser": 1000, "runAsGroup": 3000}
        ),
        securityContext=kubernetes.SecurityContext.parse_obj(
            {"runAsUser": 1000, "runAsGroup": 3000}
        ),
        resources=kubernetes.Resources.parse_obj(
            {
                "requests": {"memory": "64Mi", "cpu": "250m"},
                "limits": {"memory": "128Mi", "cpu": "500m"},
            }
        ),
    )


@pytest.fixture(name="single_user_deployment_values")
def helm_values_single_user_deployment() -> HelmValues:
    return HelmValues.construct(
        userDeployments=UserDeployments(
            enabled=True,
            deployments=[create_simple_user_deployment("simple-deployment-one")],
        )
    )


@pytest.fixture(name="single_complex_user_deployment_values")
def helm_values_single_complex_user_deployment() -> HelmValues:
    return HelmValues.construct(
        userDeployments=UserDeployments(
            enabled=True,
            deployments=[create_complex_user_deployment("complex-deployment-one")],
        )
    )


@pytest.fixture(name="multi_user_deployment_values")
def helm_values_multi_user_deployment() -> HelmValues:
    return HelmValues.construct(
        userDeployments=UserDeployments(
            enabled=True,
            deployments=[
                create_simple_user_deployment("simple-deployment-one"),
                create_simple_user_deployment("simple-deployment-two"),
            ],
        )
    )


@pytest.fixture(name="multi_complex_user_deployment_values")
def helm_values_multi_complex_user_deployment() -> HelmValues:
    return HelmValues.construct(
        userDeployments=UserDeployments(
            enabled=True,
            deployments=[
                create_complex_user_deployment("complex-deployment-one"),
                create_complex_user_deployment("complex-deployment-two"),
                create_simple_user_deployment("simple-deployment-three"),
            ],
        )
    )


def assert_user_deployment_template(
    t: HelmTemplate, templates: List[models.V1Deployment], values: HelmValues
):
    for template, deployment_values in zip(templates, values.userDeployments.deployments):
        # Assert simple stuff
        assert template.metadata.labels["deployment"] == deployment_values.name
        assert len(template.spec.template.spec.containers) == 1
        assert template.spec.template.spec.containers[0].image == deployment_values.image.name
        assert (
            template.spec.template.spec.containers[0].image_pull_policy
            == deployment_values.image.pullPolicy
        )

        # Assert annotations
        if deployment_values.annotations:
            template_deployment_annotations = t.api_client.sanitize_for_serialization(
                template.metadata.annotations
            )
            template_deployment_pod_annotations = t.api_client.sanitize_for_serialization(
                template.spec.template.metadata.annotations
            )
            annotations_values = json.loads(deployment_values.annotations.json(exclude_none=True))

            assert template_deployment_annotations == annotations_values
            assert template_deployment_pod_annotations.items() >= annotations_values.items()

        # Assert node selector
        if deployment_values.nodeSelector:
            template_node_selector = t.api_client.sanitize_for_serialization(
                template.spec.template.spec.node_selector
            )
            node_selector_values = json.loads(
                deployment_values.nodeSelector.json(exclude_none=True)
            )

            assert template_node_selector == node_selector_values

        # Assert affinity
        if deployment_values.affinity:
            template_affinity = t.api_client.sanitize_for_serialization(
                template.spec.template.spec.affinity
            )
            affinity_values = json.loads(deployment_values.affinity.json(exclude_none=True))

            assert template_affinity == affinity_values

        # Assert tolerations
        if deployment_values.tolerations:
            template_tolerations = t.api_client.sanitize_for_serialization(
                template.spec.template.spec.tolerations
            )
            tolerations_values = json.loads(deployment_values.tolerations.json(exclude_none=True))

            assert template_tolerations == tolerations_values

        # Assert pod security context
        if deployment_values.podSecurityContext:
            template_pod_security_context = t.api_client.sanitize_for_serialization(
                template.spec.template.spec.security_context
            )
            pod_security_context_values = json.loads(
                deployment_values.podSecurityContext.json(exclude_none=True)
            )

            assert template_pod_security_context == pod_security_context_values

        # Assert security context
        if deployment_values.securityContext:
            template_container_security_context = t.api_client.sanitize_for_serialization(
                template.spec.template.spec.containers[0].security_context
            )
            security_context_values = json.loads(
                deployment_values.securityContext.json(exclude_none=True)
            )

            assert template_container_security_context == security_context_values

        # Assert resources
        if deployment_values.resources:
            template_resources = t.api_client.sanitize_for_serialization(
                template.spec.template.spec.containers[0].resources
            )
            resource_values = json.loads(deployment_values.resources.json(exclude_none=True))

            assert template_resources == resource_values


def test_deployments_do_not_render(template: HelmTemplate, capsys):
    with pytest.raises(subprocess.CalledProcessError):
        values = HelmValues.construct(
            userDeployments=UserDeployments(enabled=False, deployments=[])
        )
        template.render(values)

        _, err = capsys.readouterr()
        assert "Error: could not find template" in err


def test_single_deployment_render(
    template: HelmTemplate, single_user_deployment_values: HelmValues
):
    user_deployments = template.render(single_user_deployment_values)

    assert len(user_deployments) == 1

    assert_user_deployment_template(template, user_deployments, single_user_deployment_values)


def test_multi_deployment_render(template: HelmTemplate, multi_user_deployment_values: HelmValues):
    user_deployments = template.render(multi_user_deployment_values)

    assert len(user_deployments) == 2

    assert_user_deployment_template(template, user_deployments, multi_user_deployment_values)


def test_single_complex_deployment_render(
    template: HelmTemplate, single_complex_user_deployment_values: HelmValues
):
    user_deployments = template.render(single_complex_user_deployment_values)

    assert len(user_deployments) == 1

    assert_user_deployment_template(
        template, user_deployments, single_complex_user_deployment_values
    )


def test_multi_complex_deployment_render(
    template: HelmTemplate, multi_complex_user_deployment_values: HelmValues
):
    user_deployments = template.render(multi_complex_user_deployment_values)

    assert len(user_deployments) == 3

    assert_user_deployment_template(
        template, user_deployments, multi_complex_user_deployment_values
    )
