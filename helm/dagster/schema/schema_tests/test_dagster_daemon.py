import pytest
import yaml
from kubernetes.client import models
from schema.charts.dagster.subschema.daemon import (
    Daemon,
    QueuedRunCoordinatorConfig,
    RunCoordinator,
    RunCoordinatorConfig,
    RunCoordinatorType,
    TagConcurrencyLimit,
)
from schema.charts.dagster.values import DagsterHelmValues
from schema.charts.utils import kubernetes
from schema.utils.helm_template import HelmTemplate


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


def test_run_monitoring(instance_template: HelmTemplate,):  # pylint: disable=redefined-outer-name
    helm_values = DagsterHelmValues.construct(
        dagsterDaemon=Daemon.construct(runMonitoring={"enabled": True})
    )

    configmaps = instance_template.render(helm_values)

    assert len(configmaps) == 1

    instance = yaml.full_load(configmaps[0].data["dagster.yaml"])

    assert instance["run_monitoring"]["enabled"] == True
