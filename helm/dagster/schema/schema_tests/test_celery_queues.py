import pytest
import yaml
from kubernetes.client import models
from schema.charts.dagster.subschema.run_launcher import (
    CeleryK8sRunLauncherConfig,
    CeleryWorkerQueue,
    RunLauncher,
    RunLauncherConfig,
    RunLauncherType,
)
from schema.charts.dagster.values import DagsterHelmValues
from schema.charts.utils import kubernetes
from schema.utils.helm_template import HelmTemplate


@pytest.fixture(name="deployment_template")
def deployment_helm_template() -> HelmTemplate:
    return HelmTemplate(
        helm_dir_path="helm/dagster",
        subchart_paths=["charts/dagster-user-deployments"],
        output="templates/deployment-celery-queues.yaml",
        model=models.V1Deployment,
    )


@pytest.fixture(name="celery_queue_configmap_template")
def celery_queue_configmap_helm_template() -> HelmTemplate:
    return HelmTemplate(
        helm_dir_path="helm/dagster",
        subchart_paths=["charts/dagster-user-deployments"],
        output="templates/configmap-celery.yaml",
        model=models.V1ConfigMap,
    )


@pytest.mark.parametrize("chart_version", ["0.11.0", "0.11.1"])
def test_celery_queue_default_image_tag_is_chart_version(
    deployment_template: HelmTemplate, chart_version: str
):
    helm_values = DagsterHelmValues.construct(
        runLauncher=RunLauncher.construct(type=RunLauncherType.CELERY)
    )

    celery_queue_deployments = deployment_template.render(helm_values, chart_version=chart_version)

    assert len(celery_queue_deployments) == 1

    image = celery_queue_deployments[0].spec.template.spec.containers[0].image
    _, image_tag = image.split(":")

    assert image_tag == chart_version


def test_celery_queue_image(deployment_template: HelmTemplate):
    repository = "repository"
    tag = "tag"
    helm_values = DagsterHelmValues.construct(
        runLauncher=RunLauncher(
            type=RunLauncherType.CELERY,
            config=RunLauncherConfig(
                celeryK8sRunLauncher=CeleryK8sRunLauncherConfig.construct(
                    image=kubernetes.Image.construct(repository=repository, tag=tag)
                )
            ),
        )
    )

    dagit_deployments = deployment_template.render(helm_values)

    assert len(dagit_deployments) == 1

    image = dagit_deployments[0].spec.template.spec.containers[0].image
    image_name, image_tag = image.split(":")

    assert image_name == repository
    assert image_tag == tag


def test_celery_queue_inherit_config_source(
    deployment_template: HelmTemplate, celery_queue_configmap_template: HelmTemplate
):

    configSource = {
        "broker_transport_options": {"priority_steps": [9]},
        "worker_concurrency": 1,
    }

    workerQueues = [
        {
            "name": "dagster",
            "replicaCount": 2,
            "additionalCeleryArgs": ["-E", "--concurrency", "16"],
        },
        {"name": "extra-queue-1", "replicaCount": 1, "configSource": {"worker_concurrency": 4}},
    ]

    helm_values = DagsterHelmValues.construct(
        runLauncher=RunLauncher.construct(
            type=RunLauncherType.CELERY,
            config=RunLauncherConfig.construct(
                celeryK8sRunLauncher=CeleryK8sRunLauncherConfig.construct(
                    configSource=configSource,
                    workerQueues=[CeleryWorkerQueue(**workerQueue) for workerQueue in workerQueues],
                )
            ),
        )
    )

    celery_queue_deployments = deployment_template.render(helm_values)

    celery_queue_configmaps = celery_queue_configmap_template.render(helm_values)

    assert len(celery_queue_deployments) == 2

    assert len(celery_queue_configmaps) == 2

    dagster_container_spec = celery_queue_deployments[0].spec.template.spec.containers[0]
    assert dagster_container_spec.command == ["dagster-celery"]
    assert dagster_container_spec.args == [
        "worker",
        "start",
        "-A",
        "dagster_celery_k8s.app",
        "-y",
        "/opt/dagster/dagster_home/celery-config.yaml",
        "-q",
        "dagster",
        "--",
        "-E",
        "--concurrency",
        "16",
    ]

    liveness_command = [
        "/bin/sh",
        "-c",
        'dagster-celery status -A dagster_celery_k8s.app -y /opt/dagster/dagster_home/celery-config.yaml | grep "${HOSTNAME}:.*OK"',
    ]

    assert (
        dagster_container_spec.liveness_probe._exec.command  # pylint: disable=protected-access
        == liveness_command
    )

    extra_queue_container_spec = celery_queue_deployments[1].spec.template.spec.containers[0]
    assert extra_queue_container_spec.command == ["dagster-celery"]
    assert extra_queue_container_spec.args == [
        "worker",
        "start",
        "-A",
        "dagster_celery_k8s.app",
        "-y",
        "/opt/dagster/dagster_home/celery-config.yaml",
        "-q",
        "extra-queue-1",
    ]

    assert (
        extra_queue_container_spec.liveness_probe._exec.command  # pylint: disable=protected-access
        == liveness_command
    )

    dagster_celery = yaml.full_load(celery_queue_configmaps[0].data["celery.yaml"])
    extra_queue_celery = yaml.full_load(celery_queue_configmaps[1].data["celery.yaml"])

    assert dagster_celery["execution"]["celery"]["broker"]["env"] == "DAGSTER_K8S_CELERY_BROKER"
    assert dagster_celery["execution"]["celery"]["backend"]["env"] == "DAGSTER_K8S_CELERY_BACKEND"

    assert dagster_celery["execution"]["celery"]["config_source"] == configSource

    assert extra_queue_celery["execution"]["celery"]["config_source"] == {
        "broker_transport_options": {"priority_steps": [9]},
        "worker_concurrency": 4,
    }

    assert extra_queue_celery["execution"]["celery"]["broker"]["env"] == "DAGSTER_K8S_CELERY_BROKER"
    assert (
        extra_queue_celery["execution"]["celery"]["backend"]["env"] == "DAGSTER_K8S_CELERY_BACKEND"
    )


def test_celery_queue_empty_run_launcher_config_source(
    deployment_template: HelmTemplate, celery_queue_configmap_template: HelmTemplate
):
    workerQueues = [
        {"name": "dagster", "replicaCount": 2, "configSource": {"worker_concurrency": 3}},
        {"name": "extra-queue-1", "replicaCount": 1, "configSource": {"worker_concurrency": 4}},
    ]

    helm_values = DagsterHelmValues.construct(
        runLauncher=RunLauncher.construct(
            type=RunLauncherType.CELERY,
            config=RunLauncherConfig.construct(
                celeryK8sRunLauncher=CeleryK8sRunLauncherConfig.construct(
                    workerQueues=[CeleryWorkerQueue(**workerQueue) for workerQueue in workerQueues],
                )
            ),
        )
    )

    celery_queue_deployments = deployment_template.render(helm_values)

    celery_queue_configmaps = celery_queue_configmap_template.render(helm_values)

    assert len(celery_queue_deployments) == 2

    assert len(celery_queue_configmaps) == 2

    dagster_celery = yaml.full_load(celery_queue_configmaps[0].data["celery.yaml"])
    extra_queue_celery = yaml.full_load(celery_queue_configmaps[1].data["celery.yaml"])

    assert dagster_celery["execution"]["celery"]["config_source"] == workerQueues[0]["configSource"]

    assert (
        extra_queue_celery["execution"]["celery"]["config_source"]
        == workerQueues[1]["configSource"]
    )
