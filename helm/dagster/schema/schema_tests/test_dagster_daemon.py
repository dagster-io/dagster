import pytest
from kubernetes.client import models
from schema.charts.dagster.subschema.daemon import Daemon
from schema.charts.dagster.values import DagsterHelmValues
from schema.charts.utils import kubernetes

from .helm_template import HelmTemplate


@pytest.fixture(name="template")
def helm_template() -> HelmTemplate:
    return HelmTemplate(
        output="templates/deployment-daemon.yaml",
        model=models.V1Deployment,
    )


@pytest.mark.parametrize("enabled", [True, False])
def test_startup_probe_enabled(template: HelmTemplate, enabled: bool):
    helm_values = DagsterHelmValues.construct(
        dagsterDaemon=Daemon.construct(startupProbe=kubernetes.StartupProbe(enabled=enabled))
    )

    daemon = template.render(helm_values)
    assert len(daemon) == 1
    daemon = daemon[0]

    assert len(daemon.spec.template.spec.containers) == 1
    container = daemon.spec.template.spec.containers[0]

    assert (container.startup_probe is not None) == enabled


@pytest.mark.parametrize("chart_version", ["0.11.0", "0.11.1"])
def test_daemon_default_image_tag_is_chart_version(template: HelmTemplate, chart_version: str):
    helm_values = DagsterHelmValues.construct()

    daemon_deployments = template.render(helm_values, chart_version=chart_version)

    assert len(daemon_deployments) == 1

    image = daemon_deployments[0].spec.template.spec.containers[0].image
    _, image_tag = image.split(":")

    assert image_tag == chart_version


def test_dagit_image(template: HelmTemplate):
    repository = "repository"
    tag = "tag"
    helm_values = DagsterHelmValues.construct(
        dagsterDaemon=Daemon.construct(
            image=kubernetes.Image.construct(repository=repository, tag=tag)
        )
    )

    daemon_deployments = template.render(helm_values)

    assert len(daemon_deployments) == 1

    image = daemon_deployments[0].spec.template.spec.containers[0].image
    image_name, image_tag = image.split(":")

    assert image_name == repository
    assert image_tag == tag
