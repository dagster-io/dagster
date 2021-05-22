import pytest
from kubernetes.client import models
from schema.charts.dagster.subschema.dagit import Dagit
from schema.charts.dagster.values import DagsterHelmValues
from schema.charts.utils import kubernetes

from .helm_template import HelmTemplate


@pytest.fixture(name="template")
def helm_template() -> HelmTemplate:
    return HelmTemplate(output="templates/deployment-dagit.yaml", model=models.V1Deployment)


@pytest.mark.parametrize(
    "service_port",
    [
        80,
        3000,
        8080,
    ],
)
def test_dagit_port(template: HelmTemplate, service_port: int):
    helm_values = DagsterHelmValues.construct(
        dagit=Dagit.construct(
            service=kubernetes.Service(
                type="ClusterIP",
                port=service_port,
            ),
        )
    )

    dagit_template = template.render(helm_values)

    # Make sure dagit will start up serving the correct port
    dagit_command = "".join(dagit_template[0].spec.template.spec.containers[0].command)
    port_arg = f"-p {helm_values.dagit.service.port}"
    assert port_arg in dagit_command

    # Make sure k8s will open the correct port
    k8s_port = dagit_template[0].spec.template.spec.containers[0].ports[0].container_port
    assert k8s_port == service_port


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


def test_dagit_read_only_disabled(template: HelmTemplate):
    helm_values = DagsterHelmValues.construct(dagit=Dagit.construct())

    dagit_template = template.render(helm_values)

    assert len(dagit_template) == 1
    assert "--read-only" not in "".join(dagit_template[0].spec.template.spec.containers[0].command)


def test_dagit_read_only_enabled(template: HelmTemplate):
    helm_values = DagsterHelmValues.construct(dagit=Dagit.construct(enableReadOnly=True))

    dagit_template = template.render(helm_values)

    assert len(dagit_template) == 2
    assert [
        "--read-only" in "".join(dagit.spec.template.spec.containers[0].command)
        for dagit in dagit_template
    ] == [False, True]
