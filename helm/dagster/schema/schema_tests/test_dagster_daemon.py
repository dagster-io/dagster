import pytest
import yaml
from kubernetes.client import models
from schema.charts.dagster.subschema.daemon import (
    Daemon,
    QueuedRunCoordinatorConfig,
    RunCoordinator,
    RunCoordinatorConfig,
    RunCoordinatorType,
    Sensors,
    TagConcurrencyLimit,
)
from schema.charts.dagster.values import DagsterHelmValues
from schema.charts.dagster_user_deployments.subschema.user_deployments import UserDeployments
from schema.charts.utils import kubernetes
from schema.utils.helm_template import HelmTemplate

from dagster._core.instance.config import sensors_daemon_config

from .utils import create_simple_user_deployment


@pytest.fixture(name="template")
def helm_template() -> HelmTemplate:
    return HelmTemplate(
        helm_dir_path="helm/dagster",
        subchart_paths=["charts/dagster-user-deployments"],
        output="templates/deployment-daemon.yaml",
        model=models.V1Deployment,
    )


@pytest.fixture()
def instance_template() -> HelmTemplate:
    return HelmTemplate(
        helm_dir_path="helm/dagster",
        subchart_paths=["charts/dagster-user-deployments"],
        output="templates/configmap-instance.yaml",
        model=models.V1ConfigMap,
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


def test_daemon_command_with_user_deployments(template: HelmTemplate):
    repository = "repository"
    tag = "tag"
    helm_values = DagsterHelmValues.construct(
        dagsterDaemon=Daemon.construct(
            image=kubernetes.Image.construct(repository=repository, tag=tag)
        ),
        dagsterUserDeployments=UserDeployments.construct(
            enabled=True,
            enableSubchart=True,
            deployments=[create_simple_user_deployment("simple-deployment-one")],
        ),
    )
    daemon_deployments = template.render(helm_values)

    assert len(daemon_deployments) == 1

    command = daemon_deployments[0].spec.template.spec.containers[0].command
    assert command == [
        "/bin/bash",
        "-c",
        "dagster-daemon run -w /dagster-workspace/workspace.yaml",
    ]


def test_daemon_command_without_user_deployments(template: HelmTemplate):
    repository = "repository"
    tag = "tag"
    helm_values = DagsterHelmValues.construct(
        dagsterDaemon=Daemon.construct(
            image=kubernetes.Image.construct(repository=repository, tag=tag)
        ),
        dagsterUserDeployments=UserDeployments.construct(
            enabled=False,
            enableSubchart=False,
            deployments=[],
        ),
    )
    daemon_deployments = template.render(helm_values)

    assert len(daemon_deployments) == 1

    command = daemon_deployments[0].spec.template.spec.containers[0].command
    assert command == [
        "/bin/bash",
        "-c",
        "dagster-daemon run",
    ]


def test_daemon_image(template: HelmTemplate):
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


def test_queued_run_coordinator(
    instance_template: HelmTemplate,
):  # pylint: disable=redefined-outer-name
    helm_values = DagsterHelmValues.construct(
        dagsterDaemon=Daemon.construct(
            runCoordinator=RunCoordinator.construct(
                enabled=True,
                type=RunCoordinatorType.QUEUED,
                config=RunCoordinatorConfig.construct(
                    queuedRunCoordinator=QueuedRunCoordinatorConfig.construct(
                        tagConcurrencyLimits=[
                            TagConcurrencyLimit.construct(key="foo", value="hi", limit=1)
                        ]
                    ),
                ),
            )
        )
    )

    configmaps = instance_template.render(helm_values)

    assert len(configmaps) == 1

    instance = yaml.full_load(configmaps[0].data["dagster.yaml"])

    assert instance["run_coordinator"]["class"] == "QueuedRunCoordinator"
    assert instance["run_coordinator"]["config"]["tag_concurrency_limits"] == [
        {"key": "foo", "value": "hi", "limit": 1}
    ]


def test_queued_run_coordinator_unique_values(
    instance_template: HelmTemplate,
):  # pylint: disable=redefined-outer-name
    helm_values = DagsterHelmValues.construct(
        dagsterDaemon=Daemon.construct(
            runCoordinator=RunCoordinator.construct(
                enabled=True,
                type=RunCoordinatorType.QUEUED,
                config=RunCoordinatorConfig.construct(
                    queuedRunCoordinator=QueuedRunCoordinatorConfig.construct(
                        tagConcurrencyLimits=[
                            TagConcurrencyLimit.construct(
                                key="foo", value={"applyLimitPerUniqueValue": True}, limit=1
                            )
                        ]
                    ),
                ),
            )
        )
    )

    configmaps = instance_template.render(helm_values)

    assert len(configmaps) == 1

    instance = yaml.full_load(configmaps[0].data["dagster.yaml"])

    assert instance["run_coordinator"]["class"] == "QueuedRunCoordinator"
    assert instance["run_coordinator"]["config"]["tag_concurrency_limits"] == [
        {"key": "foo", "value": {"applyLimitPerUniqueValue": True}, "limit": 1}
    ]


def test_run_monitoring(
    instance_template: HelmTemplate,
):  # pylint: disable=redefined-outer-name
    helm_values = DagsterHelmValues.construct(
        dagsterDaemon=Daemon.construct(runMonitoring={"enabled": True})
    )

    configmaps = instance_template.render(helm_values)

    assert len(configmaps) == 1

    instance = yaml.full_load(configmaps[0].data["dagster.yaml"])

    assert instance["run_monitoring"]["enabled"] is True


def test_run_retries(
    instance_template: HelmTemplate,
):  # pylint: disable=redefined-outer-name
    helm_values = DagsterHelmValues.construct(
        dagsterDaemon=Daemon.construct(runRetries={"enabled": True})
    )

    configmaps = instance_template.render(helm_values)

    assert len(configmaps) == 1

    instance = yaml.full_load(configmaps[0].data["dagster.yaml"])

    assert instance["run_retries"]["enabled"] is True


def test_daemon_labels(template: HelmTemplate):
    deployment_labels = {"deployment_label": "label"}
    pod_labels = {"pod_label": "label"}
    helm_values = DagsterHelmValues.construct(
        dagsterDaemon=Daemon.construct(
            deploymentLabels=deployment_labels,
            labels=pod_labels,
        )
    )

    [daemon_deployment] = template.render(helm_values)

    assert set(deployment_labels.items()).issubset(daemon_deployment.metadata.labels.items())
    assert set(pod_labels.items()).issubset(daemon_deployment.spec.template.metadata.labels.items())


def test_sensor_threading(instance_template: HelmTemplate):
    helm_values = DagsterHelmValues.construct(
        dagsterDaemon=Daemon.construct(
            sensors=Sensors.construct(
                useThreads=True,
                numWorkers=4,
            )
        )
    )

    configmaps = instance_template.render(helm_values)
    assert len(configmaps) == 1
    instance = yaml.full_load(configmaps[0].data["dagster.yaml"])
    sensors_config = instance["sensors"]
    assert sensors_config.keys() == sensors_daemon_config().config_type.fields.keys()
    assert instance["sensors"]["use_threads"] is True
    assert instance["sensors"]["num_workers"] == 4


def test_scheduler_name(template: HelmTemplate):
    helm_values = DagsterHelmValues.construct(
        dagsterDaemon=Daemon.construct(schedulerName="custom")
    )

    [daemon_deployment] = template.render(helm_values)

    assert daemon_deployment.spec.template.spec.scheduler_name == "custom"
