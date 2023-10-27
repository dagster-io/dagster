import pytest
import yaml
from dagster._core.instance.config import schedules_daemon_config, sensors_daemon_config
from dagster_k8s.models import k8s_model_from_dict, k8s_snake_case_dict
from kubernetes import client as k8s_client
from kubernetes.client import models
from schema.charts.dagster.subschema.daemon import (
    Daemon,
    QueuedRunCoordinatorConfig,
    RunCoordinator,
    RunCoordinatorConfig,
    RunCoordinatorType,
    Schedules,
    Sensors,
    TagConcurrencyLimit,
)
from schema.charts.dagster.values import DagsterHelmValues
from schema.charts.dagster_user_deployments.subschema.user_deployments import UserDeployments
from schema.charts.utils import kubernetes
from schema.utils.helm_template import HelmTemplate

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


@pytest.fixture()
def env_configmap_template() -> HelmTemplate:
    return HelmTemplate(
        helm_dir_path="helm/dagster",
        subchart_paths=["charts/dagster-user-deployments"],
        output="templates/configmap-env-daemon.yaml",
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
):
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
):
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


def test_run_monitoring_defaults(
    instance_template: HelmTemplate,
):
    helm_values = DagsterHelmValues.construct()

    configmaps = instance_template.render(helm_values)

    assert len(configmaps) == 1

    instance = yaml.full_load(configmaps[0].data["dagster.yaml"])

    assert instance["run_monitoring"]["enabled"] is True
    assert instance["run_monitoring"]["max_resume_run_attempts"] == 0


def test_run_monitoring_disabled(
    instance_template: HelmTemplate,
):
    helm_values = DagsterHelmValues.construct(
        dagsterDaemon=Daemon.construct(runMonitoring={"enabled": False})
    )

    configmaps = instance_template.render(helm_values)

    assert len(configmaps) == 1

    instance = yaml.full_load(configmaps[0].data["dagster.yaml"])

    assert "run_monitoring" not in instance


def test_run_monitoring_enabled_default(
    instance_template: HelmTemplate,
):
    helm_values = DagsterHelmValues.construct(
        dagsterDaemon=Daemon.construct(runMonitoring={"enabled": True})
    )

    configmaps = instance_template.render(helm_values)

    assert len(configmaps) == 1

    instance = yaml.full_load(configmaps[0].data["dagster.yaml"])

    assert "run_monitoring" in instance
    assert instance["run_monitoring"]["max_resume_run_attempts"] == 0


def test_run_monitoring_no_max_resume_run_attempts(
    instance_template: HelmTemplate,
):
    helm_values = DagsterHelmValues.construct(
        dagsterDaemon=Daemon.construct(runMonitoring={"enabled": True, "maxResumeRunAttempts": 0})
    )

    configmaps = instance_template.render(helm_values)

    assert len(configmaps) == 1

    instance = yaml.full_load(configmaps[0].data["dagster.yaml"])

    assert instance["run_monitoring"]["enabled"] is True
    assert instance["run_monitoring"]["max_resume_run_attempts"] == 0


def test_run_monitoring_set_max_resume_run_attempts(
    instance_template: HelmTemplate,
):
    helm_values = DagsterHelmValues.construct(
        dagsterDaemon=Daemon.construct(runMonitoring={"enabled": True, "maxResumeRunAttempts": 2})
    )

    configmaps = instance_template.render(helm_values)

    assert len(configmaps) == 1

    instance = yaml.full_load(configmaps[0].data["dagster.yaml"])

    assert instance["run_monitoring"]["enabled"] is True
    assert instance["run_monitoring"]["max_resume_run_attempts"] == 2


def test_sensor_schedule_threading_default(
    instance_template: HelmTemplate,
):
    helm_values = DagsterHelmValues.construct(dagsterDaemon=Daemon.construct())

    configmaps = instance_template.render(helm_values)

    assert len(configmaps) == 1

    instance = yaml.full_load(configmaps[0].data["dagster.yaml"])

    assert instance["sensors"]["use_threads"] is True
    assert instance["sensors"]["num_workers"] == 4

    assert instance["schedules"]["use_threads"] is True
    assert instance["schedules"]["num_workers"] == 4


def test_schedule_threading_disabled(
    instance_template: HelmTemplate,
):
    helm_values = DagsterHelmValues.construct(
        dagsterDaemon=Daemon.construct(schedules={"useThreads": False})
    )

    configmaps = instance_template.render(helm_values)

    assert len(configmaps) == 1

    instance = yaml.full_load(configmaps[0].data["dagster.yaml"])

    assert instance["sensors"]["use_threads"] is True
    assert instance["sensors"]["num_workers"] == 4

    assert "schedules" not in instance


def test_sensor_threading_disabled(
    instance_template: HelmTemplate,
):
    helm_values = DagsterHelmValues.construct(
        dagsterDaemon=Daemon.construct(sensors={"useThreads": False})
    )
    configmaps = instance_template.render(helm_values)

    assert len(configmaps) == 1

    instance = yaml.full_load(configmaps[0].data["dagster.yaml"])

    assert instance["schedules"]["use_threads"] is True
    assert instance["schedules"]["num_workers"] == 4

    assert "sensors" not in instance


def test_run_retries_default(
    instance_template: HelmTemplate,
):
    helm_values = DagsterHelmValues.construct(dagsterDaemon=Daemon.construct())

    configmaps = instance_template.render(helm_values)

    assert len(configmaps) == 1

    instance = yaml.full_load(configmaps[0].data["dagster.yaml"])

    assert instance["run_retries"]["enabled"] is True
    assert "max_retries" not in instance["run_retries"]


def test_run_retries_disabled(
    instance_template: HelmTemplate,
):
    helm_values = DagsterHelmValues.construct(
        dagsterDaemon=Daemon.construct(runRetries={"enabled": False})
    )

    configmaps = instance_template.render(helm_values)

    assert len(configmaps) == 1

    instance = yaml.full_load(configmaps[0].data["dagster.yaml"])

    assert "run_retries" not in instance


def test_run_retries_max_retries(
    instance_template: HelmTemplate,
):
    helm_values = DagsterHelmValues.construct(
        dagsterDaemon=Daemon.construct(runRetries={"enabled": True, "maxRetries": 4})
    )

    configmaps = instance_template.render(helm_values)

    assert len(configmaps) == 1

    instance = yaml.full_load(configmaps[0].data["dagster.yaml"])

    assert instance["run_retries"]["enabled"] is True
    assert instance["run_retries"]["max_retries"] == 4


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


def test_daemon_volumes(template: HelmTemplate):
    volumes = [
        {"name": "test-volume", "configMap": {"name": "test-volume-configmap"}},
        {"name": "test-pvc", "persistentVolumeClaim": {"claimName": "my_claim", "readOnly": False}},
    ]

    volume_mounts = [
        {
            "name": "test-volume",
            "mountPath": "/opt/dagster/test_mount_path/volume_mounted_file.yaml",
            "subPath": "volume_mounted_file.yaml",
        }
    ]

    helm_values = DagsterHelmValues.construct(
        dagsterDaemon=Daemon.construct(volumes=volumes, volumeMounts=volume_mounts)
    )

    [daemon_deployment] = template.render(helm_values)

    deployed_volume_mounts = daemon_deployment.spec.template.spec.containers[0].volume_mounts
    assert deployed_volume_mounts[2:] == [
        k8s_model_from_dict(
            k8s_client.models.V1VolumeMount,
            k8s_snake_case_dict(k8s_client.models.V1VolumeMount, volume_mount),
        )
        for volume_mount in volume_mounts
    ]

    deployed_volumes = daemon_deployment.spec.template.spec.volumes
    assert deployed_volumes[2:] == [
        k8s_model_from_dict(
            k8s_client.models.V1Volume, k8s_snake_case_dict(k8s_client.models.V1Volume, volume)
        )
        for volume in volumes
    ]


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
    assert instance["sensors"]["use_threads"] is True
    assert instance["sensors"]["num_workers"] == 4
    assert "num_submit_workers" not in instance["sensors"]

    helm_values = DagsterHelmValues.construct(
        dagsterDaemon=Daemon.construct(
            sensors=Sensors.construct(
                useThreads=True,
                numWorkers=4,
                numSubmitWorkers=8,
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
    assert instance["sensors"]["num_submit_workers"] == 8


def test_scheduler_threading(instance_template: HelmTemplate):
    helm_values = DagsterHelmValues.construct(
        dagsterDaemon=Daemon.construct(
            schedules=Schedules.construct(
                useThreads=True,
                numWorkers=4,
            )
        )
    )

    configmaps = instance_template.render(helm_values)
    assert len(configmaps) == 1
    instance = yaml.full_load(configmaps[0].data["dagster.yaml"])
    schedules_config = instance["schedules"]
    assert instance["schedules"]["use_threads"] is True
    assert instance["schedules"]["num_workers"] == 4
    assert "num_submit_workers" not in instance["schedules"]

    helm_values = DagsterHelmValues.construct(
        dagsterDaemon=Daemon.construct(
            schedules=Schedules.construct(useThreads=True, numWorkers=4, numSubmitWorkers=8)
        )
    )

    configmaps = instance_template.render(helm_values)
    assert len(configmaps) == 1
    instance = yaml.full_load(configmaps[0].data["dagster.yaml"])
    schedules_config = instance["schedules"]
    assert schedules_config.keys() == schedules_daemon_config().config_type.fields.keys()
    assert instance["schedules"]["use_threads"] is True
    assert instance["schedules"]["num_workers"] == 4
    assert instance["schedules"]["num_submit_workers"] == 8


def test_scheduler_name(template: HelmTemplate):
    helm_values = DagsterHelmValues.construct(
        dagsterDaemon=Daemon.construct(schedulerName="custom")
    )

    [daemon_deployment] = template.render(helm_values)

    assert daemon_deployment.spec.template.spec.scheduler_name == "custom"


def test_env(template: HelmTemplate):
    helm_values = DagsterHelmValues.construct(dagsterDaemon=Daemon.construct())
    [daemon_deployment] = template.render(helm_values)

    assert len(daemon_deployment.spec.template.spec.containers[0].env) == 2

    # env list gets written to deployment
    helm_values = DagsterHelmValues.construct(
        dagsterDaemon=Daemon.construct(
            env=[
                {"name": "TEST_ENV", "value": "test_value"},
                {
                    "name": "TEST_ENV_FROM",
                    "valueFrom": {"fieldRef": {"fieldPath": "metadata.uid", "apiVersion": "v1"}},
                },
            ]
        )
    )
    [daemon_deployment] = template.render(helm_values)

    assert len(daemon_deployment.spec.template.spec.containers[0].env) == 4
    assert daemon_deployment.spec.template.spec.containers[0].env[2].name == "TEST_ENV"
    assert daemon_deployment.spec.template.spec.containers[0].env[2].value == "test_value"
    assert daemon_deployment.spec.template.spec.containers[0].env[3].name == "TEST_ENV_FROM"
    assert (
        daemon_deployment.spec.template.spec.containers[0].env[3].value_from.field_ref.field_path
        == "metadata.uid"
    )

    # env dict doesn't get written to deployment
    helm_values = DagsterHelmValues.construct(
        dagsterDaemon=Daemon.construct(
            env={"TEST_ENV": "test_value"},
        )
    )
    [daemon_deployment] = template.render(helm_values)
    assert len(daemon_deployment.spec.template.spec.containers[0].env) == 2


def test_env_configmap(env_configmap_template):
    # env list doesn't get rendered into configmap
    helm_values = DagsterHelmValues.construct(
        dagsterDaemon=Daemon.construct(
            env=[
                {"name": "TEST_ENV", "value": "test_value"},
                {
                    "name": "TEST_ENV_FROM",
                    "valueFrom": {"fieldRef": {"fieldPath": "metadata.uid", "apiVersion": "v1"}},
                },
            ]
        )
    )
    [cm] = env_configmap_template.render(helm_values)
    assert len(cm.data) == 5
    assert cm.data["DAGSTER_HOME"] == "/opt/dagster/dagster_home"
    assert "TEST_ENV" not in cm.data

    # env dict gets rendered into configmap
    helm_values = DagsterHelmValues.construct(
        dagsterDaemon=Daemon.construct(
            env={"TEST_ENV": "test_value"},
        )
    )
    [cm] = env_configmap_template.render(helm_values)
    assert len(cm.data) == 6
    assert cm.data["DAGSTER_HOME"] == "/opt/dagster/dagster_home"
    assert cm.data["TEST_ENV"] == "test_value"
