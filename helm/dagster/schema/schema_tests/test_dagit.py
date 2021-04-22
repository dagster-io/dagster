import pytest
from kubernetes.client import models
from schema.charts.dagster.subschema.dagit import Dagit
from schema.charts.dagster.values import DagsterHelmValues
from schema.charts.utils import kubernetes

from .helm_template import HelmTemplate


@pytest.fixture(name="template")
def helm_template() -> HelmTemplate:
    return HelmTemplate(
        output="templates/deployment-dagit.yaml",
        model=models.V1Deployment,
    )


@pytest.mark.parametrize("enabled", [True, False])
def test_startup_probe_enabled(template: HelmTemplate, enabled: bool):
    helm_values = DagsterHelmValues.construct(
        dagit=Dagit.construct(startupProbe=kubernetes.StartupProbe(enabled=enabled))
    )

    dagit = template.render(helm_values)
    assert len(dagit) == 1
    dagit = dagit[0]

    assert len(dagit.spec.template.spec.containers) == 1
    container = dagit.spec.template.spec.containers[0]

    assert (container.startup_probe is not None) == enabled
