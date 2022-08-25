import pytest
from kubernetes.client import models
from schema.charts.dagster.subschema.dagit import Dagit, Workspace
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
    "service_port",
    [
        80,
        3000,
        8080,
    ],
)
def test_dagit_port(deployment_template: HelmTemplate, service_port: int):
    helm_values = DagsterHelmValues.construct(
        dagit=Dagit.construct(
            service=kubernetes.Service(
                type="ClusterIP",
                port=service_port,
            ),
        )
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


def test_readiness_probe(deployment_template: HelmTemplate):
    helm_values = DagsterHelmValues.construct(dagit=Dagit.construct())

    dagit = deployment_template.render(helm_values)
    assert len(dagit) == 1
    dagit = dagit[0]

    assert len(dagit.spec.template.spec.containers) == 1
    container = dagit.spec.template.spec.containers[0]

    assert container.startup_probe is None
    assert container.liveness_probe is None
    assert container.readiness_probe is not None


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
        "release-name-dagit",
        "release-name-dagit-read-only",
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


@pytest.mark.parametrize("name_override", ["dagit", "new-name"])
def test_dagit_name_override(deployment_template, name_override):
    helm_values = DagsterHelmValues.construct(dagit=Dagit.construct(nameOverride=name_override))
    dagit_deployments = deployment_template.render(helm_values)

    assert len(dagit_deployments) == 1

    deployment_name = dagit_deployments[0].metadata.name

    assert deployment_name == f"{deployment_template.release_name}-{name_override}"


def test_dagit_service(service_template):
    helm_values = DagsterHelmValues.construct()
    dagit_template = service_template.render(helm_values)

    assert len(dagit_template) == 1
    assert dagit_template[0].metadata.name == "release-name-dagit"


def test_dagit_service_read_only(service_template):
    helm_values = DagsterHelmValues.construct(dagit=Dagit.construct(enableReadOnly=True))
    dagit_template = service_template.render(helm_values)

    assert len(dagit_template) == 2
    assert [dagit.metadata.name for dagit in dagit_template] == [
        "release-name-dagit",
        "release-name-dagit-read-only",
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


def test_dagit_log_level(deployment_template: HelmTemplate):
    log_level = "trace"
    helm_values = DagsterHelmValues.construct(dagit=Dagit.construct(logLevel=log_level))

    dagit_deployments = deployment_template.render(helm_values)
    command = " ".join(dagit_deployments[0].spec.template.spec.containers[0].command)

    assert f"--log-level {log_level}" in command

    helm_values = DagsterHelmValues.construct(dagit=Dagit.construct())

    dagit_deployments = deployment_template.render(helm_values)
    command = " ".join(dagit_deployments[0].spec.template.spec.containers[0].command)

    assert "--log-level" not in command


def test_dagit_labels(deployment_template: HelmTemplate):
    deployment_labels = {"deployment_label": "label"}
    pod_labels = {"pod_label": "label"}
    helm_values = DagsterHelmValues.construct(
        dagit=Dagit.construct(
            deploymentLabels=deployment_labels,
            labels=pod_labels,
        )
    )

    [dagit_deployment] = deployment_template.render(helm_values)

    assert set(deployment_labels.items()).issubset(dagit_deployment.metadata.labels.items())
    assert set(pod_labels.items()).issubset(dagit_deployment.spec.template.metadata.labels.items())


def test_dagit_workspace_external_configmap(deployment_template: HelmTemplate):
    helm_values = DagsterHelmValues.construct(
        dagit=Dagit.construct(
            workspace=Workspace(
                enabled=True,
                servers=[],
                externalConfigmap="test-external-workspace",
            )
        ),
    )

    [dagit_deployment] = deployment_template.render(helm_values)
    assert (
        dagit_deployment.spec.template.spec.volumes[1].config_map.name == "test-external-workspace"
    )


def test_dagit_scheduler_name_override(deployment_template: HelmTemplate):
    helm_values = DagsterHelmValues.construct(
        dagit=Dagit.construct(
            workspace=Workspace(
                enabled=True,
                servers=[],
                externalConfigmap="test-external-workspace",
            ),
            schedulerName="myscheduler",
        ),
    )

    [dagit_deployment] = deployment_template.render(helm_values)
    assert dagit_deployment.spec.template.spec.scheduler_name == "myscheduler"
