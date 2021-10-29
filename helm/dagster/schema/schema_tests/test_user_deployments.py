import json
import subprocess
from typing import List

import pytest
from dagster_k8s.models import k8s_model_from_dict
from kubernetes import client as k8s_client
from kubernetes.client import models
from schema.charts.dagster.subschema.global_ import Global
from schema.charts.dagster.values import DagsterHelmValues
from schema.charts.dagster_user_deployments.subschema.user_deployments import (
    UserDeployment,
    UserDeployments,
)
from schema.charts.dagster_user_deployments.values import DagsterUserDeploymentsHelmValues
from schema.charts.utils import kubernetes
from schema.utils.helm_template import HelmTemplate

from .utils import create_complex_user_deployment, create_simple_user_deployment


@pytest.fixture(name="template")
def helm_template() -> HelmTemplate:
    return HelmTemplate(
        helm_dir_path="helm/dagster",
        subchart_paths=["charts/dagster-user-deployments"],
        output="charts/dagster-user-deployments/templates/deployment-user.yaml",
        model=models.V1Deployment,
    )


@pytest.fixture(name="full_template")
def full_helm_template() -> HelmTemplate:
    return HelmTemplate(
        helm_dir_path="helm/dagster",
        subchart_paths=["charts/dagster-user-deployments"],
    )


@pytest.fixture(name="subchart_template")
def subchart_helm_template() -> HelmTemplate:
    return HelmTemplate(
        helm_dir_path="helm/dagster/charts/dagster-user-deployments",
        subchart_paths=[],
        output="templates/deployment-user.yaml",
        model=models.V1Deployment,
    )


def assert_user_deployment_template(
    t: HelmTemplate, templates: List[models.V1Deployment], values: DagsterHelmValues
):
    assert len(templates) == len(values.dagsterUserDeployments.deployments)

    for template, deployment_values in zip(templates, values.dagsterUserDeployments.deployments):
        # Assert simple stuff
        assert len(template.spec.template.spec.containers) == 1
        assert template.spec.template.spec.containers[0].image == deployment_values.image.name
        assert (
            template.spec.template.spec.containers[0].image_pull_policy
            == deployment_values.image.pullPolicy
        )

        # Assert labels
        assert template.spec.template.metadata.labels["deployment"] == deployment_values.name
        if deployment_values.labels:
            pod_spec_labels = template.spec.template.metadata.labels
            assert set(deployment_values.labels.items()).issubset(pod_spec_labels.items())

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
    "helm_values",
    [
        DagsterHelmValues.construct(
            dagsterUserDeployments=UserDeployments(
                enabled=False,
                enableSubchart=False,
                deployments=[create_simple_user_deployment("simple-deployment-one")],
            )
        ),
        DagsterHelmValues.construct(
            dagsterUserDeployments=UserDeployments(
                enabled=False,
                enableSubchart=True,
                deployments=[create_simple_user_deployment("simple-deployment-one")],
            )
        ),
        DagsterHelmValues.construct(
            dagsterUserDeployments=UserDeployments(
                enabled=True,
                enableSubchart=False,
                deployments=[create_simple_user_deployment("simple-deployment-one")],
            )
        ),
    ],
    ids=[
        "user deployments disabled, subchart disabled",
        "user deployments disabled, subchart enabled",
        "user deployments enabled, subchart disabled",
    ],
)
def test_deployments_do_not_render(helm_values: DagsterHelmValues, template: HelmTemplate, capsys):
    with pytest.raises(subprocess.CalledProcessError):
        template.render(helm_values)

        _, err = capsys.readouterr()
        assert "Error: could not find template" in err


@pytest.mark.parametrize(
    "helm_values",
    [
        DagsterHelmValues.construct(
            dagsterUserDeployments=UserDeployments(
                enabled=True,
                enableSubchart=True,
                deployments=[create_simple_user_deployment("simple-deployment-one")],
            )
        ),
        DagsterHelmValues.construct(
            dagsterUserDeployments=UserDeployments(
                enabled=True,
                enableSubchart=True,
                deployments=[create_complex_user_deployment("complex-deployment-one")],
            )
        ),
        DagsterHelmValues.construct(
            dagsterUserDeployments=UserDeployments(
                enabled=True,
                enableSubchart=True,
                deployments=[
                    create_simple_user_deployment("simple-deployment-one"),
                    create_simple_user_deployment("simple-deployment-two"),
                ],
            )
        ),
        DagsterHelmValues.construct(
            dagsterUserDeployments=UserDeployments(
                enabled=True,
                enableSubchart=True,
                deployments=[
                    create_complex_user_deployment("complex-deployment-one"),
                    create_complex_user_deployment("complex-deployment-two"),
                    create_simple_user_deployment("simple-deployment-three"),
                ],
            )
        ),
    ],
    ids=[
        "single user deployment",
        "multi user deployment",
        "complex, single user deployment",
        "complex, multi user deployment",
    ],
)
def test_deployments_render(helm_values: DagsterHelmValues, template: HelmTemplate):
    user_deployments = template.render(helm_values)

    assert_user_deployment_template(template, user_deployments, helm_values)


def test_chart_does_not_render(full_template: HelmTemplate, capsys):
    helm_values = DagsterHelmValues.construct(
        dagsterUserDeployments=UserDeployments(
            enabled=False,
            enableSubchart=True,
            deployments=[create_simple_user_deployment("simple-deployment-one")],
        )
    )

    with pytest.raises(subprocess.CalledProcessError):
        full_template.render(helm_values)

        _, err = capsys.readouterr()
        assert (
            "dagster-user-deployments subchart cannot be enabled if workspace.yaml is not created."
            in err
        )


@pytest.mark.parametrize(
    "helm_values",
    [
        DagsterHelmValues.construct(
            dagsterUserDeployments=UserDeployments(
                enabled=True,
                enableSubchart=False,
                deployments=[
                    create_simple_user_deployment("simple-deployment-one"),
                ],
            )
        ),
        DagsterHelmValues.construct(
            dagsterUserDeployments=UserDeployments(
                enabled=True,
                enableSubchart=False,
                deployments=[
                    create_complex_user_deployment("complex-deployment-one"),
                    create_complex_user_deployment("complex-deployment-two"),
                    create_simple_user_deployment("simple-deployment-three"),
                ],
            )
        ),
    ],
    ids=[
        "single user deployment enabled, subchart disabled",
        "multiple user deployments enabled, subchart disabled",
    ],
)
def test_chart_does_render(helm_values: DagsterHelmValues, full_template: HelmTemplate):
    templates = full_template.render(helm_values)

    assert templates


@pytest.mark.parametrize(
    "helm_values",
    [
        DagsterHelmValues.construct(
            dagsterUserDeployments=UserDeployments(
                enabled=True,
                enableSubchart=True,
                deployments=[
                    create_simple_user_deployment("simple-deployment-one"),
                ],
            )
        ),
        DagsterHelmValues.construct(
            dagsterUserDeployments=UserDeployments(
                enabled=True,
                enableSubchart=True,
                deployments=[
                    create_complex_user_deployment("complex-deployment-one"),
                    create_complex_user_deployment("complex-deployment-two"),
                    create_simple_user_deployment("simple-deployment-three"),
                ],
            )
        ),
    ],
    ids=[
        "single user deployment enabled",
        "multiple user deployments enabled",
    ],
)
def test_user_deployment_checksum_unchanged(helm_values: DagsterHelmValues, template: HelmTemplate):
    pre_upgrade_templates = template.render(helm_values)
    post_upgrade_templates = template.render(helm_values)

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


def test_user_deployment_checksum_changes(template: HelmTemplate):
    pre_upgrade_helm_values = DagsterHelmValues.construct(
        dagsterUserDeployments=UserDeployments(
            enabled=True,
            enableSubchart=True,
            deployments=[
                create_simple_user_deployment("deployment-one"),
                create_simple_user_deployment("deployment-two"),
            ],
        )
    )
    post_upgrade_helm_values = DagsterHelmValues.construct(
        dagsterUserDeployments=UserDeployments(
            enabled=True,
            enableSubchart=True,
            deployments=[
                create_complex_user_deployment("deployment-one"),
                create_complex_user_deployment("deployment-two"),
            ],
        )
    )

    pre_upgrade_templates = template.render(pre_upgrade_helm_values)
    post_upgrade_templates = template.render(post_upgrade_helm_values)

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


@pytest.mark.parametrize("enabled", [True, False])
def test_startup_probe_enabled(template: HelmTemplate, enabled: bool):
    deployment = create_simple_user_deployment("foo")
    deployment.startupProbe = kubernetes.StartupProbe.construct(enabled=enabled)
    helm_values = DagsterHelmValues.construct(
        dagsterUserDeployments=UserDeployments.construct(deployments=[deployment])
    )

    dagster_user_deployment = template.render(helm_values)
    assert len(dagster_user_deployment) == 1
    dagster_user_deployment = dagster_user_deployment[0]

    assert len(dagster_user_deployment.spec.template.spec.containers) == 1
    container = dagster_user_deployment.spec.template.spec.containers[0]

    assert (container.startup_probe is not None) == enabled


def test_startup_probe_exec(template: HelmTemplate):
    deployment = create_simple_user_deployment("foo")
    deployment.startupProbe = kubernetes.StartupProbe.construct(
        enabled=True, exec=dict(command=["my", "command"])
    )
    helm_values = DagsterHelmValues.construct(
        dagsterUserDeployments=UserDeployments.construct(deployments=[deployment])
    )

    dagster_user_deployment = template.render(helm_values)
    assert len(dagster_user_deployment) == 1
    dagster_user_deployment = dagster_user_deployment[0]

    assert len(dagster_user_deployment.spec.template.spec.containers) == 1
    container = dagster_user_deployment.spec.template.spec.containers[0]

    assert container.startup_probe._exec.command == [  # pylint:disable=protected-access
        "my",
        "command",
    ]


def test_startup_probe_default_exec(template: HelmTemplate):
    deployment = create_simple_user_deployment("foo")
    deployment.startupProbe = kubernetes.StartupProbe.construct(enabled=True)
    helm_values = DagsterHelmValues.construct(
        dagsterUserDeployments=UserDeployments.construct(deployments=[deployment])
    )

    dagster_user_deployment = template.render(helm_values)
    assert len(dagster_user_deployment) == 1
    dagster_user_deployment = dagster_user_deployment[0]

    assert len(dagster_user_deployment.spec.template.spec.containers) == 1
    container = dagster_user_deployment.spec.template.spec.containers[0]

    assert container.startup_probe._exec.command == [  # pylint: disable=protected-access
        "dagster",
        "api",
        "grpc-health-check",
        "-p",
        str(deployment.port),
    ]


@pytest.mark.parametrize("chart_version", ["0.11.0", "0.11.1"])
def test_user_deployment_default_image_tag_is_chart_version(
    template: HelmTemplate, chart_version: str
):
    helm_values = DagsterHelmValues.construct()

    user_deployments = template.render(helm_values, chart_version=chart_version)

    assert len(user_deployments) == 1

    image = user_deployments[0].spec.template.spec.containers[0].image
    _, image_tag = image.split(":")

    assert image_tag == chart_version


def test_user_deployment_image(template: HelmTemplate):
    deployment = create_simple_user_deployment("foo")
    helm_values = DagsterHelmValues.construct(
        dagsterUserDeployments=UserDeployments(
            enabled=True,
            enableSubchart=True,
            deployments=[deployment],
        )
    )

    user_deployments = template.render(helm_values)

    assert len(user_deployments) == 1

    image = user_deployments[0].spec.template.spec.containers[0].image
    image_name, image_tag = image.split(":")

    assert image_name == deployment.image.repository
    assert image_tag == deployment.image.tag


def test_user_deployment_volumes(template: HelmTemplate):

    name = "foo"

    volumes = [
        {"name": "test-volume", "configMap": {"name": "test-volume-configmap"}},
        {"name": "test-pvc", "persistentVolumeClaim": {"claimName": "my_claim", "readOnly": False}},
    ]

    volume_mounts = [
        {
            "name": "test-volume",
            "mountPath": "/opt/dagster/test_mount_path/volume_mounted_file.yaml",
            "subPath": "volume_mounted_file.yaml",
        }
    ]

    deployment = UserDeployment(
        name=name,
        image=kubernetes.Image(repository=f"repo/{name}", tag="tag1", pullPolicy="Always"),
        dagsterApiGrpcArgs=["-m", name],
        port=3030,
        volumes=[kubernetes.Volume.construct(None, **volume) for volume in volumes],
        volumeMounts=[
            kubernetes.VolumeMount.construct(None, **volume_mount) for volume_mount in volume_mounts
        ],
    )

    helm_values = DagsterHelmValues.construct(
        dagsterUserDeployments=UserDeployments(
            enabled=True,
            enableSubchart=True,
            deployments=[deployment],
        )
    )

    user_deployments = template.render(helm_values)

    assert len(user_deployments) == 1

    image = user_deployments[0].spec.template.spec.containers[0].image
    image_name, image_tag = image.split(":")

    deployed_volume_mounts = user_deployments[0].spec.template.spec.containers[0].volume_mounts
    assert deployed_volume_mounts == [
        k8s_model_from_dict(k8s_client.models.V1VolumeMount, volume_mount)
        for volume_mount in volume_mounts
    ]

    deployed_volumes = user_deployments[0].spec.template.spec.volumes
    assert deployed_volumes == [
        k8s_model_from_dict(k8s_client.models.V1Volume, volume) for volume in volumes
    ]

    assert image_name == deployment.image.repository
    assert image_tag == deployment.image.tag


def test_subchart_image_pull_secrets(subchart_template: HelmTemplate):
    image_pull_secrets = [{"name": "super-duper-secret"}]
    deployment_values = DagsterUserDeploymentsHelmValues.construct(
        imagePullSecrets=image_pull_secrets,
    )

    deployment_templates = subchart_template.render(deployment_values)

    assert len(deployment_templates) == 1

    deployment_template = deployment_templates[0]
    pod_spec = deployment_template.spec.template.spec

    assert pod_spec.image_pull_secrets[0].name == image_pull_secrets[0]["name"]


def test_subchart_postgres_password_global_override(subchart_template: HelmTemplate):
    deployment_values = DagsterUserDeploymentsHelmValues.construct(
        postgresqlSecretName="postgresql-secret",
        global_=Global.construct(
            postgresqlSecretName="global-postgresql-secret",
        ),
    )

    deployment_templates = subchart_template.render(deployment_values)

    assert len(deployment_templates) == 1

    deployment_template = deployment_templates[0]
    pod_spec = deployment_template.spec.template.spec
    container = pod_spec.containers[0]

    assert container.env[1].name == "DAGSTER_PG_PASSWORD"
    assert container.env[1].value_from.secret_key_ref.name == "global-postgresql-secret"


def test_subchart_postgres_password(subchart_template: HelmTemplate):
    deployment_values = DagsterUserDeploymentsHelmValues.construct(
        postgresqlSecretName="postgresql-secret",
    )

    deployment_templates = subchart_template.render(deployment_values)

    assert len(deployment_templates) == 1

    deployment_template = deployment_templates[0]
    pod_spec = deployment_template.spec.template.spec
    container = pod_spec.containers[0]

    assert container.env[1].name == "DAGSTER_PG_PASSWORD"
    assert container.env[1].value_from.secret_key_ref.name == "postgresql-secret"


def test_subchart_default_postgres_password(subchart_template: HelmTemplate):
    deployment_values = DagsterUserDeploymentsHelmValues.construct()

    deployment_templates = subchart_template.render(deployment_values)

    assert len(deployment_templates) == 1

    deployment_template = deployment_templates[0]
    pod_spec = deployment_template.spec.template.spec
    container = pod_spec.containers[0]

    assert container.env[1].name == "DAGSTER_PG_PASSWORD"
    assert container.env[1].value_from.secret_key_ref.name == "dagster-postgresql-secret"
