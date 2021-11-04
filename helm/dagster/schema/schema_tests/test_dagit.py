import pytest
from kubernetes.client import models
from schema.charts.dagster.subschema.dagit import Dagit
from schema.charts.dagster.values import DagsterHelmValues
from schema.charts.utils import kubernetes
from schema.utils.helm_template import HelmTemplate


@pytest.fixture(name="deployment_template")
def deployment_helm_template() -> HelmTemplate:
    return HelmTemplate(
        helm_dir_path="helm/dagster",
        subchart_paths=["charts/dagster-user-deployments"],
        output="templates/deployment-dagit.yaml",
        model=models.V1Deployment,
    )


@pytest.fixture(name="service_template")
def service_helm_template() -> HelmTemplate:
    return HelmTemplate(
        helm_dir_path="helm/dagster",
        subchart_paths=["charts/dagster-user-deployments"],
        output="templates/service-dagit.yaml",
        model=models.V1Service,
    )


@pytest.mark.parametrize(
    "service_port", [80, 3000, 8080,],
)
def test_dagit_port(deployment_template: HelmTemplate, service_port: int):
    helm_values = DagsterHelmValues.construct(
        dagit=Dagit.construct(service=kubernetes.Service(type="ClusterIP", port=service_port,),)
    )

    dagit_template = deployment_template.render(helm_values)

    # Make sure dagit will start up serving the correct port
    dagit_command = "".join(dagit_template[0].spec.template.spec.containers[0].command)
    port_arg = f"-p {helm_values.dagit.service.port}"
    assert port_arg in dagit_command

    # Make sure k8s will open the correct port
    k8s_port = dagit_template[0].spec.template.spec.containers[0].ports[0].container_port
    assert k8s_port == service_port


@pytest.mark.parametrize("enabled", [True, False])
def test_startup_probe_enabled(deployment_template: HelmTemplate, enabled: bool):
    helm_values = DagsterHelmValues.construct(
        dagit=Dagit.construct(startupProbe=kubernetes.StartupProbe(enabled=enabled))
    )

    dagit = deployment_template.render(helm_values)
    assert len(dagit) == 1
    dagit = dagit[0]

    assert len(dagit.spec.template.spec.containers) == 1
    container = dagit.spec.template.spec.containers[0]

    assert (container.startup_probe is not None) == enabled


def test_dagit_read_only_disabled(deployment_template: HelmTemplate):
    helm_values = DagsterHelmValues.construct()

    dagit_template = deployment_template.render(helm_values)

    assert len(dagit_template) == 1
    assert "--read-only" not in "".join(dagit_template[0].spec.template.spec.containers[0].command)


def test_dagit_read_only_enabled(deployment_template: HelmTemplate):
    helm_values = DagsterHelmValues.construct(dagit=Dagit.construct(enableReadOnly=True))

    dagit_template = deployment_template.render(helm_values)

    assert len(dagit_template) == 2
    assert [
        "--read-only" in "".join(dagit.spec.template.spec.containers[0].command)
        for dagit in dagit_template
    ] == [False, True]
    assert [dagit.metadata.name for dagit in dagit_template] == [
        "RELEASE-NAME-dagit",
        "RELEASE-NAME-dagit-read-only",
    ]

    assert [dagit.spec.template.metadata.labels["component"] for dagit in dagit_template] == [
        "dagit",
        "dagit-read-only",
    ]


@pytest.mark.parametrize("enable_read_only", [True, False])
@pytest.mark.parametrize("chart_version", ["0.11.0", "0.11.1"])
def test_dagit_default_image_tag_is_chart_version(
    deployment_template: HelmTemplate, enable_read_only: bool, chart_version: str
):
    helm_values = DagsterHelmValues.construct(
        dagit=Dagit.construct(enableReadOnly=enable_read_only)
    )

    dagit_deployments = deployment_template.render(helm_values, chart_version=chart_version)

    assert len(dagit_deployments) == 1 + int(enable_read_only)

    for dagit_deployment in dagit_deployments:
        image = dagit_deployment.spec.template.spec.containers[0].image
        _, image_tag = image.split(":")

        assert image_tag == chart_version


def test_dagit_image_tag(deployment_template: HelmTemplate):
    repository = "repository"
    tag = "tag"
    helm_values = DagsterHelmValues.construct(
        dagit=Dagit.construct(image=kubernetes.Image.construct(repository=repository, tag=tag))
    )

    dagit_deployments = deployment_template.render(helm_values)

    assert len(dagit_deployments) == 1

    image = dagit_deployments[0].spec.template.spec.containers[0].image
    image_name, image_tag = image.split(":")

    assert image_name == repository
    assert image_tag == tag


def test_dagit_service(service_template):
    helm_values = DagsterHelmValues.construct()
    dagit_template = service_template.render(helm_values)

    assert len(dagit_template) == 1
    assert dagit_template[0].metadata.name == "RELEASE-NAME-dagit"


def test_dagit_service_read_only(service_template):
    helm_values = DagsterHelmValues.construct(dagit=Dagit.construct(enableReadOnly=True))
    dagit_template = service_template.render(helm_values)

    assert len(dagit_template) == 2
    assert [dagit.metadata.name for dagit in dagit_template] == [
        "RELEASE-NAME-dagit",
        "RELEASE-NAME-dagit-read-only",
    ]
    assert [dagit.spec.selector["component"] for dagit in dagit_template] == [
        "dagit",
        "dagit-read-only",
    ]


def test_dagit_db_statement_timeout(deployment_template: HelmTemplate):
    db_statement_timeout_ms = 9000
    helm_values = DagsterHelmValues.construct(
        dagit=Dagit.construct(dbStatementTimeout=db_statement_timeout_ms)
    )

    dagit_deployments = deployment_template.render(helm_values)
    command = " ".join(dagit_deployments[0].spec.template.spec.containers[0].command)

    assert f"--db-statement-timeout {db_statement_timeout_ms}" in command
