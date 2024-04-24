import json
import subprocess
from typing import List, Union

import pytest
from dagster_k8s.models import k8s_model_from_dict, k8s_snake_case_dict
from kubernetes import client as k8s_client
from kubernetes.client import models
from schema.charts.dagster.subschema.global_ import Global
from schema.charts.dagster.values import DagsterHelmValues
from schema.charts.dagster_user_deployments.subschema.user_deployments import (
    ReadinessProbeWithEnabled,
    UserDeployment,
    UserDeploymentIncludeConfigInLaunchedRuns,
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


@pytest.fixture()
def user_deployment_configmap_template() -> HelmTemplate:
    return HelmTemplate(
        helm_dir_path="helm/dagster",
        subchart_paths=["charts/dagster-user-deployments"],
        output="charts/dagster-user-deployments/templates/configmap-env-user.yaml",
        model=models.V1ConfigMap,
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
        assert not template.spec.template.spec.containers[0].command
        assert template.spec.template.spec.containers[0].args[:5] == [
            "dagster",
            "api",
            "grpc",
            "-h",
            "0.0.0.0",
        ]

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


def test_deployments_enabled_subchart_disabled(template: HelmTemplate, capfd):
    with pytest.raises(subprocess.CalledProcessError):
        template.render(
            DagsterHelmValues.construct(
                dagsterUserDeployments=UserDeployments.construct(
                    enabled=True,
                    enableSubchart=False,
                    deployments=[create_simple_user_deployment("simple-deployment-one")],
                )
            ),
        )

    _, err = capfd.readouterr()
    assert "Error: could not find template" in err


def test_deployments_disabled_subchart_enabled(template: HelmTemplate, capfd):
    with pytest.raises(subprocess.CalledProcessError):
        template.render(
            DagsterHelmValues.construct(
                dagsterUserDeployments=UserDeployments.construct(
                    enabled=False,
                    enableSubchart=True,
                    deployments=[create_simple_user_deployment("simple-deployment-one")],
                )
            ),
        )

    _, err = capfd.readouterr()
    assert (
        "dagster-user-deployments subchart cannot be enabled if workspace.yaml is not created"
        in err
    )


def test_deployments_disabled_subchart_disabled(template: HelmTemplate, capfd):
    with pytest.raises(subprocess.CalledProcessError):
        template.render(
            DagsterHelmValues.construct(
                dagsterUserDeployments=UserDeployments.construct(
                    enabled=False,
                    enableSubchart=False,
                    deployments=[create_simple_user_deployment("simple-deployment-one")],
                )
            )
        )

    _, err = capfd.readouterr()
    assert "Error: could not find template" in err


@pytest.mark.parametrize(
    "helm_values",
    [
        DagsterHelmValues.construct(
            dagsterUserDeployments=UserDeployments.construct(
                enabled=True,
                enableSubchart=True,
                deployments=[create_simple_user_deployment("simple-deployment-one")],
            )
        ),
        DagsterHelmValues.construct(
            dagsterUserDeployments=UserDeployments.construct(
                enabled=True,
                enableSubchart=True,
                deployments=[create_complex_user_deployment("complex-deployment-one")],
            )
        ),
        DagsterHelmValues.construct(
            dagsterUserDeployments=UserDeployments.construct(
                enabled=True,
                enableSubchart=True,
                deployments=[
                    create_simple_user_deployment("simple-deployment-one"),
                    create_simple_user_deployment("simple-deployment-two"),
                ],
            )
        ),
        DagsterHelmValues.construct(
            dagsterUserDeployments=UserDeployments.construct(
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


def test_chart_does_not_render(full_template: HelmTemplate, capfd):
    helm_values = DagsterHelmValues.construct(
        dagsterUserDeployments=UserDeployments.construct(
            enabled=False,
            enableSubchart=True,
            deployments=[create_simple_user_deployment("simple-deployment-one")],
        )
    )

    with pytest.raises(subprocess.CalledProcessError):
        full_template.render(helm_values)

    _, err = capfd.readouterr()
    assert (
        "dagster-user-deployments subchart cannot be enabled if workspace.yaml is not created."
        in err
    )


@pytest.mark.parametrize(
    "helm_values",
    [
        DagsterHelmValues.construct(
            dagsterUserDeployments=UserDeployments.construct(
                enabled=True,
                enableSubchart=False,
                deployments=[
                    create_simple_user_deployment("simple-deployment-one"),
                ],
            )
        ),
        DagsterHelmValues.construct(
            dagsterUserDeployments=UserDeployments.construct(
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
            dagsterUserDeployments=UserDeployments.construct(
                enabled=True,
                enableSubchart=True,
                deployments=[
                    create_simple_user_deployment("simple-deployment-one"),
                ],
            )
        ),
        DagsterHelmValues.construct(
            dagsterUserDeployments=UserDeployments.construct(
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
        dagsterUserDeployments=UserDeployments.construct(
            enabled=True,
            enableSubchart=True,
            deployments=[
                create_simple_user_deployment("deployment-one"),
                create_simple_user_deployment("deployment-two"),
            ],
        )
    )
    post_upgrade_helm_values = DagsterHelmValues.construct(
        dagsterUserDeployments=UserDeployments.construct(
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


def test_readiness_probe_enabled_by_default(template: HelmTemplate):
    deployment = create_simple_user_deployment("foo")
    helm_values = DagsterHelmValues.construct(
        dagsterUserDeployments=UserDeployments.construct(deployments=[deployment])
    )

    dagster_user_deployment = template.render(helm_values)
    assert len(dagster_user_deployment) == 1
    dagster_user_deployment = dagster_user_deployment[0]

    assert len(dagster_user_deployment.spec.template.spec.containers) == 1
    container = dagster_user_deployment.spec.template.spec.containers[0]

    assert container.startup_probe is None
    assert container.startup_probe is None
    assert container.readiness_probe is not None
    assert container.readiness_probe._exec.command == [  # noqa: SLF001
        "dagster",
        "api",
        "grpc-health-check",
        "-p",
        "3030",
    ]
    assert container.readiness_probe.timeout_seconds == 10


def test_readiness_probe_can_be_disabled(template: HelmTemplate):
    deployment = create_simple_user_deployment("foo")
    deployment.readinessProbe = ReadinessProbeWithEnabled.construct(enabled=False)
    helm_values = DagsterHelmValues.construct(
        dagsterUserDeployments=UserDeployments.construct(deployments=[deployment])
    )

    dagster_user_deployment = template.render(helm_values)
    assert len(dagster_user_deployment) == 1
    dagster_user_deployment = dagster_user_deployment[0]

    assert len(dagster_user_deployment.spec.template.spec.containers) == 1
    container = dagster_user_deployment.spec.template.spec.containers[0]

    assert container.startup_probe is None
    assert container.startup_probe is None
    assert container.readiness_probe is None


def test_readiness_probe_can_be_customized(template: HelmTemplate):
    deployment = create_simple_user_deployment("foo")
    deployment.readinessProbe = ReadinessProbeWithEnabled.construct(timeoutSeconds=42)
    helm_values = DagsterHelmValues.construct(
        dagsterUserDeployments=UserDeployments.construct(deployments=[deployment])
    )

    dagster_user_deployment = template.render(helm_values)
    assert len(dagster_user_deployment) == 1
    dagster_user_deployment = dagster_user_deployment[0]

    assert len(dagster_user_deployment.spec.template.spec.containers) == 1
    container = dagster_user_deployment.spec.template.spec.containers[0]

    assert container.startup_probe is None
    assert container.startup_probe is None
    assert container.readiness_probe is not None
    assert container.readiness_probe._exec.command == [  # noqa: SLF001
        "dagster",
        "api",
        "grpc-health-check",
        "-p",
        "3030",
    ]
    assert container.readiness_probe.timeout_seconds == 42


def test_readiness_probes_subchart(subchart_template: HelmTemplate):
    deployment = create_simple_user_deployment(
        "foo",
    )
    deployment.readinessProbe = kubernetes.ReadinessProbe.construct(timeout_seconds=3)
    helm_values = DagsterHelmValues.construct(
        dagsterUserDeployments=UserDeployments.construct(deployments=[deployment])
    )

    dagster_user_deployment = subchart_template.render(helm_values)
    assert len(dagster_user_deployment) == 1
    dagster_user_deployment = dagster_user_deployment[0]

    assert len(dagster_user_deployment.spec.template.spec.containers) == 1
    container = dagster_user_deployment.spec.template.spec.containers[0]

    assert container.startup_probe is None
    assert container.startup_probe is None
    assert container.readiness_probe is not None


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

    assert container.startup_probe._exec.command == [  # noqa: SLF001
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

    assert container.startup_probe._exec.command == [  # noqa: SLF001
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


@pytest.mark.parametrize("tag", [5176135, "abc1234", "20220531.1", "1234"])
def test_user_deployment_tag_can_be_numeric(template: HelmTemplate, tag: Union[str, int]):
    deployment = create_simple_user_deployment("foo")
    deployment.image.tag = tag

    helm_values = DagsterHelmValues.construct(
        dagsterUserDeployments=UserDeployments.construct(
            enabled=True,
            enableSubchart=True,
            deployments=[deployment],
        )
    )

    user_deployments = template.render(helm_values)

    assert len(user_deployments) == 1

    image = user_deployments[0].spec.template.spec.containers[0].image
    _, image_tag = image.split(":")

    assert image_tag == str(tag)


def _assert_no_container_context(user_deployment):
    # No container context set by default
    env_names = [env.name for env in user_deployment.spec.template.spec.containers[0].env]
    assert "DAGSTER_CLI_API_GRPC_CONTAINER_CONTEXT" not in env_names


def _assert_has_container_context(user_deployment):
    env_names = [env.name for env in user_deployment.spec.template.spec.containers[0].env]
    assert "DAGSTER_CLI_API_GRPC_CONTAINER_CONTEXT" in env_names


def test_user_deployment_image(template: HelmTemplate):
    deployment = create_simple_user_deployment("foo")
    helm_values = DagsterHelmValues.construct(
        dagsterUserDeployments=UserDeployments.construct(
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

    _assert_has_container_context(user_deployments[0])


def test_user_deployment_include_config_in_launched_runs(template: HelmTemplate):
    deployments = [
        create_simple_user_deployment("foo", include_config_in_launched_runs=True),
        create_simple_user_deployment("bar", include_config_in_launched_runs=None),
        create_simple_user_deployment("baz", include_config_in_launched_runs=False),
    ]

    helm_values = DagsterHelmValues.construct(
        dagsterUserDeployments=UserDeployments.construct(
            enabled=True, enableSubchart=True, deployments=deployments
        )
    )

    user_deployments = template.render(helm_values)

    assert len(user_deployments) == 3

    # Setting to true results in container context being set
    container_context = user_deployments[0].spec.template.spec.containers[0].env[2]
    assert container_context.name == "DAGSTER_CLI_API_GRPC_CONTAINER_CONTEXT"
    assert json.loads(container_context.value) == {
        "k8s": {
            "image_pull_policy": "Always",
            "env_config_maps": ["release-name-dagster-user-deployments-foo-user-env"],
            "namespace": "default",
            "service_account_name": "release-name-dagster-user-deployments-user-deployments",
            "run_k8s_config": {
                "pod_spec_config": {
                    "automount_service_account_token": True,
                }
            },
        }
    }

    # Setting to None also results in container context being set
    assert (
        user_deployments[1].spec.template.spec.containers[0].env[2].name
        == "DAGSTER_CLI_API_GRPC_CONTAINER_CONTEXT"
    )

    # setting to false means no container context
    _assert_no_container_context(user_deployments[2])


@pytest.mark.parametrize("include_config_in_launched_runs", [False, True])
def test_user_deployment_volumes(template: HelmTemplate, include_config_in_launched_runs: bool):
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

    deployment = UserDeployment.construct(
        name=name,
        image=kubernetes.Image(repository=f"repo/{name}", tag="tag1", pullPolicy="Always"),
        dagsterApiGrpcArgs=["-m", name],
        port=3030,
        volumes=[kubernetes.Volume.construct(None, **volume) for volume in volumes],
        volumeMounts=[
            kubernetes.VolumeMount.construct(None, **volume_mount) for volume_mount in volume_mounts
        ],
        includeConfigInLaunchedRuns=UserDeploymentIncludeConfigInLaunchedRuns(
            enabled=include_config_in_launched_runs
        ),
    )

    helm_values = DagsterHelmValues.construct(
        dagsterUserDeployments=UserDeployments.construct(
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
        k8s_model_from_dict(
            k8s_client.models.V1VolumeMount,
            k8s_snake_case_dict(k8s_client.models.V1VolumeMount, volume_mount),
        )
        for volume_mount in volume_mounts
    ]

    deployed_volumes = user_deployments[0].spec.template.spec.volumes
    assert deployed_volumes == [
        k8s_model_from_dict(
            k8s_client.models.V1Volume, k8s_snake_case_dict(k8s_client.models.V1Volume, volume)
        )
        for volume in volumes
    ]

    assert image_name == deployment.image.repository
    assert image_tag == deployment.image.tag

    if include_config_in_launched_runs:
        container_context = user_deployments[0].spec.template.spec.containers[0].env[2]
        assert container_context.name == "DAGSTER_CLI_API_GRPC_CONTAINER_CONTEXT"
        assert json.loads(container_context.value) == {
            "k8s": {
                "env_config_maps": [
                    "release-name-dagster-user-deployments-foo-user-env",
                ],
                "image_pull_policy": "Always",
                "volume_mounts": volume_mounts,
                "volumes": volumes,
                "namespace": "default",
                "service_account_name": "release-name-dagster-user-deployments-user-deployments",
                "run_k8s_config": {
                    "pod_spec_config": {
                        "automount_service_account_token": True,
                    }
                },
            }
        }
    else:
        _assert_no_container_context(user_deployments[0])


@pytest.mark.parametrize("include_config_in_launched_runs", [False, True])
def test_user_deployment_secrets_and_configmaps(
    template: HelmTemplate, include_config_in_launched_runs: bool
):
    name = "foo"

    secrets = [{"name": "my-secret"}, {"name": "my-other-secret"}]

    configmaps = [{"name": "my-configmap"}, {"name": "my-other-configmap"}]

    deployment = UserDeployment.construct(
        name=name,
        image=kubernetes.Image(repository=f"repo/{name}", tag="tag1", pullPolicy="Always"),
        dagsterApiGrpcArgs=["-m", name],
        port=3030,
        envConfigMaps=[
            kubernetes.ConfigMapEnvSource.construct(None, **configmap) for configmap in configmaps
        ],
        envSecrets=[kubernetes.SecretEnvSource.construct(None, **secret) for secret in secrets],
        includeConfigInLaunchedRuns=UserDeploymentIncludeConfigInLaunchedRuns(
            enabled=include_config_in_launched_runs
        ),
    )

    helm_values = DagsterHelmValues.construct(
        dagsterUserDeployments=UserDeployments.construct(
            enabled=True,
            enableSubchart=True,
            deployments=[deployment],
        )
    )

    user_deployments = template.render(helm_values)

    assert len(user_deployments) == 1

    if include_config_in_launched_runs:
        container_context = user_deployments[0].spec.template.spec.containers[0].env[2]
        assert container_context.name == "DAGSTER_CLI_API_GRPC_CONTAINER_CONTEXT"
        assert json.loads(container_context.value) == {
            "k8s": {
                "image_pull_policy": "Always",
                "env_secrets": ["my-secret", "my-other-secret"],
                "env_config_maps": [
                    "release-name-dagster-user-deployments-foo-user-env",
                    "my-configmap",
                    "my-other-configmap",
                ],
                "namespace": "default",
                "service_account_name": "release-name-dagster-user-deployments-user-deployments",
                "run_k8s_config": {
                    "pod_spec_config": {
                        "automount_service_account_token": True,
                    }
                },
            }
        }
    else:
        _assert_no_container_context(user_deployments[0])


@pytest.mark.parametrize("include_config_in_launched_runs", [False, True])
def test_user_deployment_labels(template: HelmTemplate, include_config_in_launched_runs: bool):
    name = "foo"

    labels = {"my-label-key": "my-label-val", "my-other-label-key": "my-other-label-val"}

    deployment = UserDeployment.construct(
        name=name,
        image=kubernetes.Image(repository=f"repo/{name}", tag="tag1", pullPolicy="Always"),
        dagsterApiGrpcArgs=["-m", name],
        port=3030,
        labels=labels,
        includeConfigInLaunchedRuns=UserDeploymentIncludeConfigInLaunchedRuns(
            enabled=include_config_in_launched_runs
        ),
    )

    helm_values = DagsterHelmValues.construct(
        dagsterUserDeployments=UserDeployments.construct(
            enabled=True,
            enableSubchart=True,
            deployments=[deployment],
        )
    )

    user_deployments = template.render(helm_values)

    assert len(user_deployments) == 1

    if include_config_in_launched_runs:
        container_context = user_deployments[0].spec.template.spec.containers[0].env[2]
        assert container_context.name == "DAGSTER_CLI_API_GRPC_CONTAINER_CONTEXT"
        assert json.loads(container_context.value) == {
            "k8s": {
                "image_pull_policy": "Always",
                "env_config_maps": [
                    "release-name-dagster-user-deployments-foo-user-env",
                ],
                "labels": labels,
                "namespace": "default",
                "service_account_name": "release-name-dagster-user-deployments-user-deployments",
                "run_k8s_config": {
                    "pod_spec_config": {
                        "automount_service_account_token": True,
                    }
                },
            }
        }
    else:
        _assert_no_container_context(user_deployments[0])


@pytest.mark.parametrize("include_config_in_launched_runs", [False, True])
def test_annotations(template: HelmTemplate, include_config_in_launched_runs: bool):
    name = "foo"

    annotations = {"my-annotation-key": "my-annotation-val"}

    deployment = UserDeployment.construct(
        name=name,
        image=kubernetes.Image(repository=f"repo/{name}", tag="tag1", pullPolicy="Always"),
        dagsterApiGrpcArgs=["-m", name],
        port=3030,
        annotations=annotations,
        includeConfigInLaunchedRuns=UserDeploymentIncludeConfigInLaunchedRuns(
            enabled=include_config_in_launched_runs
        ),
    )

    helm_values = DagsterHelmValues.construct(
        dagsterUserDeployments=UserDeployments.construct(
            enabled=True,
            enableSubchart=True,
            deployments=[deployment],
        )
    )

    user_deployments = template.render(helm_values)

    assert len(user_deployments) == 1

    if include_config_in_launched_runs:
        container_context = user_deployments[0].spec.template.spec.containers[0].env[2]
        assert container_context.name == "DAGSTER_CLI_API_GRPC_CONTAINER_CONTEXT"
        assert json.loads(container_context.value) == {
            "k8s": {
                "image_pull_policy": "Always",
                "env_config_maps": [
                    "release-name-dagster-user-deployments-foo-user-env",
                ],
                "namespace": "default",
                "service_account_name": "release-name-dagster-user-deployments-user-deployments",
                "run_k8s_config": {
                    "pod_spec_config": {
                        "automount_service_account_token": True,
                    },
                    "pod_template_spec_metadata": {
                        "annotations": annotations,
                    },
                },
            }
        }
    else:
        _assert_no_container_context(user_deployments[0])


@pytest.mark.parametrize("include_config_in_launched_runs", [False, True])
def test_user_deployment_resources(template: HelmTemplate, include_config_in_launched_runs: bool):
    name = "foo"

    resources = {
        "requests": {"memory": "64Mi", "cpu": "250m"},
        "limits": {"memory": "128Mi", "cpu": "500m"},
    }

    deployment = UserDeployment.construct(
        name=name,
        image={"repository": f"repo/{name}", "tag": "tag1", "pullPolicy": "Always"},
        dagsterApiGrpcArgs=["-m", name],
        port=3030,
        resources=resources,
        includeConfigInLaunchedRuns={"enabled": include_config_in_launched_runs},
    )

    helm_values = DagsterHelmValues.construct(
        dagsterUserDeployments=UserDeployments.construct(
            enabled=True,
            enableSubchart=True,
            deployments=[deployment],
        )
    )

    user_deployments = template.render(helm_values)

    assert len(user_deployments) == 1

    if include_config_in_launched_runs:
        container_context = user_deployments[0].spec.template.spec.containers[0].env[2]
        assert container_context.name == "DAGSTER_CLI_API_GRPC_CONTAINER_CONTEXT"
        assert json.loads(container_context.value) == {
            "k8s": {
                "image_pull_policy": "Always",
                "env_config_maps": [
                    "release-name-dagster-user-deployments-foo-user-env",
                ],
                "resources": resources,
                "namespace": "default",
                "service_account_name": "release-name-dagster-user-deployments-user-deployments",
                "run_k8s_config": {
                    "pod_spec_config": {
                        "automount_service_account_token": True,
                    }
                },
            }
        }
    else:
        _assert_no_container_context(user_deployments[0])


@pytest.mark.parametrize("include_config_in_launched_runs", [False, True])
def test_user_deployment_sidecar(template: HelmTemplate, include_config_in_launched_runs: bool):
    name = "foo"

    init_containers = [
        {"name": "my-init-container", "image": "my-init-image"},
    ]

    sidecars = [
        {"name": "my-sidecar", "image": "my-sidecar-image"},
    ]

    deployment = UserDeployment.construct(
        name=name,
        image=kubernetes.Image(repository=f"repo/{name}", tag="tag1", pullPolicy="Always"),
        dagsterApiGrpcArgs=["-m", name],
        port=3030,
        initContainers=[
            kubernetes.Container.construct(None, **container) for container in init_containers
        ],
        sidecarContainers=[kubernetes.Container.construct(None, **sidecar) for sidecar in sidecars],
        includeConfigInLaunchedRuns=UserDeploymentIncludeConfigInLaunchedRuns(
            enabled=include_config_in_launched_runs
        ),
    )

    helm_values = DagsterHelmValues.construct(
        dagsterUserDeployments=UserDeployments.construct(
            enabled=True,
            enableSubchart=True,
            deployments=[deployment],
        )
    )

    user_deployments = template.render(helm_values)

    assert len(user_deployments) == 1

    image = user_deployments[0].spec.template.spec.containers[0].image
    image_name, image_tag = image.split(":")

    deployed_sidecars = user_deployments[0].spec.template.spec.containers[1:]
    assert deployed_sidecars == [
        k8s_model_from_dict(
            k8s_client.models.V1Container,
            k8s_snake_case_dict(k8s_client.models.V1Container, sidecar),
        )
        for sidecar in sidecars
    ]

    deployed_init_containers = user_deployments[0].spec.template.spec.init_containers
    assert deployed_init_containers == [
        k8s_model_from_dict(
            k8s_client.models.V1Container,
            k8s_snake_case_dict(k8s_client.models.V1Container, container),
        )
        for container in init_containers
    ]

    if include_config_in_launched_runs:
        container_context = user_deployments[0].spec.template.spec.containers[0].env[2]
        assert container_context.name == "DAGSTER_CLI_API_GRPC_CONTAINER_CONTEXT"
        assert json.loads(container_context.value) == {
            "k8s": {
                "env_config_maps": [
                    "release-name-dagster-user-deployments-foo-user-env",
                ],
                "image_pull_policy": "Always",
                "namespace": "default",
                "service_account_name": "release-name-dagster-user-deployments-user-deployments",
                "run_k8s_config": {
                    "pod_spec_config": {
                        "init_containers": init_containers,
                        "containers": sidecars,
                        "automount_service_account_token": True,
                    },
                },
            }
        }
    else:
        _assert_no_container_context(user_deployments[0])


@pytest.mark.parametrize("include_config_in_launched_runs", [False, True])
def test_subchart_image_pull_secrets(
    subchart_template: HelmTemplate, include_config_in_launched_runs: bool
):
    image_pull_secrets = [{"name": "super-duper-secret"}]
    deployment_values = DagsterUserDeploymentsHelmValues.construct(
        imagePullSecrets=image_pull_secrets,
        deployments=[
            create_simple_user_deployment(
                "foo", include_config_in_launched_runs=include_config_in_launched_runs
            )
        ],
    )

    deployment_templates = subchart_template.render(deployment_values)

    assert len(deployment_templates) == 1

    deployment_template = deployment_templates[0]
    pod_spec = deployment_template.spec.template.spec

    assert pod_spec.image_pull_secrets[0].name == image_pull_secrets[0]["name"]

    if include_config_in_launched_runs:
        container_context = deployment_template.spec.template.spec.containers[0].env[2]
        assert container_context.name == "DAGSTER_CLI_API_GRPC_CONTAINER_CONTEXT"
        assert json.loads(container_context.value) == {
            "k8s": {
                "env_config_maps": [
                    "release-name-dagster-user-deployments-foo-user-env",
                ],
                "image_pull_policy": "Always",
                "image_pull_secrets": image_pull_secrets,
                "namespace": "default",
                "service_account_name": "release-name-dagster-user-deployments-user-deployments",
                "run_k8s_config": {
                    "pod_spec_config": {
                        "automount_service_account_token": True,
                    }
                },
            }
        }
    else:
        _assert_no_container_context(deployment_template)


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


@pytest.mark.parametrize("tag", [5176135, "abc1234"])
def test_subchart_tag_can_be_numeric(subchart_template: HelmTemplate, tag: Union[str, int]):
    deployment_values = DagsterUserDeploymentsHelmValues.construct(
        deployments=[
            UserDeployment.construct(
                name="foo",
                image=kubernetes.Image.construct(
                    repository="foo",
                    tag=tag,
                    pullPolicy="Always",
                ),
                dagsterApiGrpcArgs=[],
                port=0,
            )
        ]
    )

    deployment_templates = subchart_template.render(deployment_values)

    assert len(deployment_templates) == 1

    image = deployment_templates[0].spec.template.spec.containers[0].image
    _, image_tag = image.split(":")

    assert image_tag == str(tag)


def test_scheduler_name(template: HelmTemplate):
    deployment = UserDeployment.construct(
        name="foo",
        image=kubernetes.Image(repository="repo/foo", tag="tag1", pullPolicy="Always"),
        dagsterApiGrpcArgs=["-m", "foo"],
        port=3030,
        includeConfigInLaunchedRuns=None,
        schedulerName="myscheduler",
    )
    helm_values = DagsterHelmValues.construct(
        dagsterUserDeployments=UserDeployments.construct(deployments=[deployment])
    )

    dagster_user_deployment = template.render(helm_values)
    assert len(dagster_user_deployment) == 1
    dagster_user_deployment = dagster_user_deployment[0]

    assert dagster_user_deployment.spec.template.spec.scheduler_name == "myscheduler"


def test_automount_svc_acct_token(template: HelmTemplate):
    helm_values = UserDeployment.construct()

    [daemon_deployment] = template.render(helm_values)

    assert daemon_deployment.spec.template.spec.automount_service_account_token


def test_env(template: HelmTemplate, user_deployment_configmap_template):
    # new env: list. Gets written to container
    deployment = UserDeployment.construct(
        name="foo",
        image=kubernetes.Image(repository="repo/foo", tag="tag1", pullPolicy="Always"),
        dagsterApiGrpcArgs=["-m", "foo"],
        port=3030,
        includeConfigInLaunchedRuns=None,
        env=[{"name": "test_env", "value": "test_value"}],
    )
    helm_values = DagsterHelmValues.construct(
        dagsterUserDeployments=UserDeployments.construct(deployments=[deployment])
    )

    [cm] = user_deployment_configmap_template.render(helm_values)
    assert not cm.data

    [dagster_user_deployment] = template.render(helm_values)
    assert len(dagster_user_deployment.spec.template.spec.containers[0].env) == 4
    assert dagster_user_deployment.spec.template.spec.containers[0].env[3].name == "test_env"
    assert dagster_user_deployment.spec.template.spec.containers[0].env[3].value == "test_value"


def test_code_server_cli(template: HelmTemplate, user_deployment_configmap_template):
    deployment = UserDeployment.construct(
        name="foo",
        image=kubernetes.Image(repository="repo/foo", tag="tag1", pullPolicy="Always"),
        codeServerArgs=["-m", "foo"],
        port=3030,
        includeConfigInLaunchedRuns=UserDeploymentIncludeConfigInLaunchedRuns(enabled=True),
    )
    helm_values = DagsterHelmValues.construct(
        dagsterUserDeployments=UserDeployments.construct(deployments=[deployment])
    )

    [dagster_user_deployment] = template.render(helm_values)
    assert len(dagster_user_deployment.spec.template.spec.containers[0].env) == 3

    assert dagster_user_deployment.spec.template.spec.containers[0].args == [
        "dagster",
        "code-server",
        "start",
        "-h",
        "0.0.0.0",
        "-p",
        "3030",
        "-m",
        "foo",
    ]

    container_context = dagster_user_deployment.spec.template.spec.containers[0].env[2]
    assert container_context.name == "DAGSTER_CONTAINER_CONTEXT"
    assert json.loads(container_context.value) == {
        "k8s": {
            "image_pull_policy": "Always",
            "env_config_maps": ["release-name-dagster-user-deployments-foo-user-env"],
            "namespace": "default",
            "service_account_name": "release-name-dagster-user-deployments-user-deployments",
            "run_k8s_config": {
                "pod_spec_config": {
                    "automount_service_account_token": True,
                },
            },
        }
    }


def test_env_container_context(template: HelmTemplate, user_deployment_configmap_template):
    # new env: list. Gets written to container
    deployment = UserDeployment.construct(
        name="foo",
        image=kubernetes.Image(repository="repo/foo", tag="tag1", pullPolicy="Always"),
        dagsterApiGrpcArgs=["-m", "foo"],
        port=3030,
        includeConfigInLaunchedRuns=UserDeploymentIncludeConfigInLaunchedRuns(enabled=True),
        env=[{"name": "test_env", "value": "test_value"}],
    )
    helm_values = DagsterHelmValues.construct(
        dagsterUserDeployments=UserDeployments.construct(deployments=[deployment])
    )

    [cm] = user_deployment_configmap_template.render(helm_values)
    assert not cm.data

    [dagster_user_deployment] = template.render(helm_values)
    assert len(dagster_user_deployment.spec.template.spec.containers[0].env) == 4
    assert dagster_user_deployment.spec.template.spec.containers[0].env[3].name == "test_env"
    assert dagster_user_deployment.spec.template.spec.containers[0].env[3].value == "test_value"

    container_context = dagster_user_deployment.spec.template.spec.containers[0].env[2]
    assert container_context.name == "DAGSTER_CLI_API_GRPC_CONTAINER_CONTEXT"
    assert json.loads(container_context.value) == {
        "k8s": {
            "image_pull_policy": "Always",
            "env_config_maps": ["release-name-dagster-user-deployments-foo-user-env"],
            "namespace": "default",
            "service_account_name": "release-name-dagster-user-deployments-user-deployments",
            "env": [{"name": "test_env", "value": "test_value"}],
            "run_k8s_config": {
                "pod_spec_config": {
                    "automount_service_account_token": True,
                }
            },
        }
    }


def test_old_env(template: HelmTemplate, user_deployment_configmap_template):
    # old style env: dict. Gets written to configmap
    deployment = UserDeployment.construct(
        name="foo",
        image=kubernetes.Image(repository="repo/foo", tag="tag1", pullPolicy="Always"),
        dagsterApiGrpcArgs=["-m", "foo"],
        port=3030,
        includeConfigInLaunchedRuns=None,
        env={"test_env": "test_value"},
    )
    helm_values = DagsterHelmValues.construct(
        dagsterUserDeployments=UserDeployments.construct(deployments=[deployment])
    )

    [dagster_user_deployment] = template.render(helm_values)
    assert len(dagster_user_deployment.spec.template.spec.containers[0].env) == 3

    [cm] = user_deployment_configmap_template.render(helm_values)
    assert cm.data["test_env"] == "test_value"
