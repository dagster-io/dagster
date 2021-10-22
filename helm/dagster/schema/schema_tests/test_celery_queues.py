import pytest
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
        {"name": "extra-queue-1", "replicaCount": 1},
        {"name": "dagster", "replicaCount": 2},
    ]

    helm_values = DagsterHelmValues.construct(
        runLauncher=RunLauncher.construct(
            type=RunLauncherType.CELERY,
            config=RunLauncherConfig.construct(
                celeryK8sRunLauncher=CeleryK8sRunLauncherConfig.construct(
                    configSource=configSource,
                    workerQueues=[
                        CeleryWorkerQueue.construct(**workerQueue) for workerQueue in workerQueues
                    ],
                )
            ),
        )
    )

    print("HI")

    print(str(helm_values))

    celery_queue_deployments = deployment_template.render(helm_values)

    print("DEPLOYMENTS:\n\n\n\n\n")
    print(str(celery_queue_deployments))

    assert len(celery_queue_deployments) == 2

    celery_queue_configmaps = celery_queue_configmap_template.render(helm_values)

    print("CONFIG MAPS: \n\n\n\n\n\n\n")
    print(str(celery_queue_configmaps))
