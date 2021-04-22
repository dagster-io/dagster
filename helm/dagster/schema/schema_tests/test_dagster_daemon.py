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
