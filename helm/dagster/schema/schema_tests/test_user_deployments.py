import json
import subprocess
from typing import List

import pytest
from kubernetes.client import models
from schema.charts.dagster.values import DagsterHelmValues
from schema.charts.dagster_user_deployments.subschema.user_deployments import (
    UserDeployment,
    UserDeployments,
)
from schema.charts.utils import kubernetes

from .helm_template import HelmTemplate


@pytest.fixture(name="template")
def helm_template() -> HelmTemplate:
    return HelmTemplate(
        output="charts/dagster-user-deployments/templates/deployment-user.yaml",
        model=models.V1Deployment,
    )


@pytest.fixture(name="full_template")
def full_helm_template() -> HelmTemplate:
    return HelmTemplate()


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
def helm_values_single_user_deployment() -> DagsterHelmValues:
    return DagsterHelmValues.construct(
        dagsterUserDeployments=UserDeployments(
            enabled=True,
            enableSubchart=True,
            deployments=[create_simple_user_deployment("simple-deployment-one")],
        )
    )


@pytest.fixture(name="single_complex_user_deployment_values")
def helm_values_single_complex_user_deployment() -> DagsterHelmValues:
    return DagsterHelmValues.construct(
        dagsterUserDeployments=UserDeployments(
            enabled=True,
            enableSubchart=True,
            deployments=[create_complex_user_deployment("complex-deployment-one")],
        )
    )


@pytest.fixture(name="multi_user_deployment_values")
def helm_values_multi_user_deployment() -> DagsterHelmValues:
    return DagsterHelmValues.construct(
        dagsterUserDeployments=UserDeployments(
            enabled=True,
            enableSubchart=True,
            deployments=[
                create_simple_user_deployment("simple-deployment-one"),
                create_simple_user_deployment("simple-deployment-two"),
            ],
        )
    )


@pytest.fixture(name="multi_complex_user_deployment_values")
def helm_values_multi_complex_user_deployment() -> DagsterHelmValues:
    return DagsterHelmValues.construct(
        dagsterUserDeployments=UserDeployments(
            enabled=True,
            enableSubchart=True,
            deployments=[
                create_complex_user_deployment("complex-deployment-one"),
                create_complex_user_deployment("complex-deployment-two"),
                create_simple_user_deployment("simple-deployment-three"),
            ],
        )
    )


def assert_user_deployment_template(
    t: HelmTemplate, templates: List[models.V1Deployment], values: DagsterHelmValues
):
    for template, deployment_values in zip(templates, values.dagsterUserDeployments.deployments):
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


@pytest.mark.parametrize(
    "user_deployments",
    [
        UserDeployments(
            enabled=False,
            enableSubchart=False,
            deployments=[create_simple_user_deployment("simple-deployment-one")],
        ),
        UserDeployments(
            enabled=False,
            enableSubchart=True,
            deployments=[create_simple_user_deployment("simple-deployment-one")],
        ),
        UserDeployments(
            enabled=True,
            enableSubchart=False,
            deployments=[create_simple_user_deployment("simple-deployment-one")],
        ),
    ],
    ids=[
        "user deployments disabled, subchart disabled",
        "user deployments disabled, subchart enabled",
        "user deployments enabled, subchart disabled",
    ],
)
def test_deployments_do_not_render(
    user_deployments: UserDeployments, template: HelmTemplate, capsys
):
    with pytest.raises(subprocess.CalledProcessError):
        values = DagsterHelmValues.construct(dagsterUserDeployments=user_deployments)
        template.render(values)

        _, err = capsys.readouterr()
        assert "Error: could not find template" in err


def test_single_deployment_render(
    template: HelmTemplate, single_user_deployment_values: DagsterHelmValues
):
    user_deployments = template.render(single_user_deployment_values)

    assert len(user_deployments) == 1

    assert_user_deployment_template(template, user_deployments, single_user_deployment_values)


def test_multi_deployment_render(
    template: HelmTemplate, multi_user_deployment_values: DagsterHelmValues
):
    user_deployments = template.render(multi_user_deployment_values)

    assert len(user_deployments) == 2

    assert_user_deployment_template(template, user_deployments, multi_user_deployment_values)


def test_single_complex_deployment_render(
    template: HelmTemplate, single_complex_user_deployment_values: DagsterHelmValues
):
    user_deployments = template.render(single_complex_user_deployment_values)

    assert len(user_deployments) == 1

    assert_user_deployment_template(
        template, user_deployments, single_complex_user_deployment_values
    )


def test_multi_complex_deployment_render(
    template: HelmTemplate, multi_complex_user_deployment_values: DagsterHelmValues
):
    user_deployments = template.render(multi_complex_user_deployment_values)

    assert len(user_deployments) == 3

    assert_user_deployment_template(
        template, user_deployments, multi_complex_user_deployment_values
    )


@pytest.mark.parametrize(
    "user_deployments",
    [
        UserDeployments(
            enabled=False,
            enableSubchart=True,
            deployments=[create_simple_user_deployment("simple-deployment-one")],
        ),
    ],
    ids=[
        "user deployments disabled, subchart enabled",
    ],
)
def test_chart_does_not_render(
    user_deployments: UserDeployments, full_template: HelmTemplate, capsys
):
    with pytest.raises(subprocess.CalledProcessError):
        values = DagsterHelmValues.construct(dagsterUserDeployments=user_deployments)
        full_template.render(values)

        _, err = capsys.readouterr()
        assert (
            "dagster-user-deployments subchart cannot be enabled if workspace.yaml is not created."
            in err
        )


@pytest.mark.parametrize(
    "user_deployments",
    [
        UserDeployments(
            enabled=True,
            enableSubchart=False,
            deployments=[
                create_simple_user_deployment("simple-deployment-one"),
            ],
        ),
        UserDeployments(
            enabled=True,
            enableSubchart=False,
            deployments=[
                create_complex_user_deployment("complex-deployment-one"),
                create_complex_user_deployment("complex-deployment-two"),
                create_simple_user_deployment("simple-deployment-three"),
            ],
        ),
    ],
    ids=[
        "single user deployment enabled, subchart disabled",
        "multiple user deployments enabled, subchart disabled",
    ],
)
def test_chart_does_render(user_deployments: UserDeployments, full_template: HelmTemplate):
    values = DagsterHelmValues.construct(dagsterUserDeployments=user_deployments)
    templates = full_template.render(values)

    assert templates


@pytest.mark.parametrize(
    "user_deployments",
    [
        UserDeployments(
            enabled=True,
            enableSubchart=True,
            deployments=[
                create_simple_user_deployment("simple-deployment-one"),
            ],
        ),
        UserDeployments(
            enabled=True,
            enableSubchart=True,
            deployments=[
                create_complex_user_deployment("complex-deployment-one"),
                create_complex_user_deployment("complex-deployment-two"),
                create_simple_user_deployment("simple-deployment-three"),
            ],
        ),
    ],
    ids=[
        "single user deployment enabled",
        "multiple user deployments enabled",
    ],
)
def test_user_deployment_checksum_unchanged(
    user_deployments: UserDeployments, template: HelmTemplate
):
    values = DagsterHelmValues.construct(dagsterUserDeployments=user_deployments)

    pre_upgrade_templates = template.render(values)
    post_upgrade_templates = template.render(values)

    # User deployment templates with the same Helm values should not redeploy in a Helm upgrade
    for pre_upgrade_user_deployment, post_upgrade_user_deployment in zip(
        pre_upgrade_templates, post_upgrade_templates
    ):
        pre_upgrade_checksum = pre_upgrade_user_deployment.spec.template.metadata.annotations[
            "checksum/dagster-user-deployment"
        ]
        post_upgrade_checksum = post_upgrade_user_deployment.spec.template.metadata.annotations[
            "checksum/dagster-user-deployment"
        ]

        assert pre_upgrade_checksum == post_upgrade_checksum


@pytest.mark.parametrize(
    "user_deployments",
    [
        (
            UserDeployments(
                enabled=True,
                enableSubchart=True,
                deployments=[
                    create_simple_user_deployment("deployment-one"),
                    create_simple_user_deployment("deployment-two"),
                ],
            ),
            UserDeployments(
                enabled=True,
                enableSubchart=True,
                deployments=[
                    create_complex_user_deployment("deployment-one"),
                    create_complex_user_deployment("deployment-two"),
                ],
            ),
        )
    ],
    ids=["multiple user deployments change"],
)
def test_user_deployment_checksum_changes(
    user_deployments: UserDeployments, template: HelmTemplate
):
    pre_upgrade_user_deployments, post_upgrade_user_deployments = user_deployments

    pre_upgrade_values = DagsterHelmValues.construct(
        dagsterUserDeployments=pre_upgrade_user_deployments
    )
    post_upgrade_values = DagsterHelmValues.construct(
        dagsterUserDeployments=post_upgrade_user_deployments
    )

    pre_upgrade_templates = template.render(pre_upgrade_values)
    post_upgrade_templates = template.render(post_upgrade_values)

    # User deployment templates with the same Helm values should not redeploy in a Helm upgrade
    for pre_upgrade_user_deployment, post_upgrade_user_deployment in zip(
        pre_upgrade_templates, post_upgrade_templates
    ):
        pre_upgrade_checksum = pre_upgrade_user_deployment.spec.template.metadata.annotations[
            "checksum/dagster-user-deployment"
        ]
        post_upgrade_checksum = post_upgrade_user_deployment.spec.template.metadata.annotations[
            "checksum/dagster-user-deployment"
        ]

        assert pre_upgrade_checksum != post_upgrade_checksum
