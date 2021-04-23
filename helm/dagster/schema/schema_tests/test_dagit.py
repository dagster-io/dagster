import pytest
from kubernetes.client import models
from schema.charts.dagster.subschema.dagit import Dagit, Server, Workspace
from schema.charts.dagster.values import DagsterHelmValues
from schema.charts.utils.kubernetes import Image, LivenessProbe, PullPolicy, Service, StartupProbe

from .helm_template import HelmTemplate


@pytest.fixture(name="template")
def helm_template() -> HelmTemplate:
    return HelmTemplate(
        output="templates/deployment-dagit.yaml",
        model=models.V1Deployment
    )


@pytest.mark.parametrize(
    "service_port",
    [
        80,
        3000,
        8080,
    ]
)
def test_dagit_port(template: HelmTemplate, service_port: int):
    helm_values = DagsterHelmValues.construct(
        dagit=Dagit(
            service=Service(
                type="ClusterIP",
                port=service_port,
            ),
            image=Image(
                repository="docker.io/dagster/dagster-celery-k8s",
                tag="latest",
                pullPolicy=PullPolicy.ALWAYS,
            ),
            workspace=Workspace(
                enabled=False,
                servers=[Server(host="k8s-example-user-code-1", port=3030)],
            ),
            livenessProbe=LivenessProbe(),
            startupProbe=StartupProbe(),
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
