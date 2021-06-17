import pytest
from kubernetes.client import models
from schema.charts.dagster.subschema.run_launcher import (
    CeleryK8sRunLauncherConfig,
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
