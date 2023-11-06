import os
import tempfile

import pytest
import yaml
from dagster._config import process_config, resolve_to_config_type
from dagster._core.instance.config import dagster_instance_config, retention_config_schema
from dagster._core.instance.ref import InstanceRef
from dagster._core.run_coordinator import QueuedRunCoordinator
from dagster._core.test_utils import environ
from dagster_aws.s3.compute_log_manager import S3ComputeLogManager
from dagster_azure.blob.compute_log_manager import AzureBlobComputeLogManager
from dagster_celery_k8s import CeleryK8sRunLauncher
from dagster_gcp.gcs.compute_log_manager import GCSComputeLogManager
from dagster_k8s import K8sRunLauncher
from kubernetes.client import models
from schema.charts.dagster.subschema.compute_log_manager import (
    AzureBlobComputeLogManager as AzureBlobComputeLogManagerModel,
    ComputeLogManager,
    ComputeLogManagerConfig,
    ComputeLogManagerType,
    GCSComputeLogManager as GCSComputeLogManagerModel,
    S3ComputeLogManager as S3ComputeLogManagerModel,
)
from schema.charts.dagster.subschema.daemon import (
    ConfigurableClass,
    Daemon,
    QueuedRunCoordinatorConfig,
    RunCoordinator,
    RunCoordinatorConfig,
    RunCoordinatorType,
    TagConcurrencyLimit,
)
from schema.charts.dagster.subschema.postgresql import PostgreSQL, Service
from schema.charts.dagster.subschema.python_logs import PythonLogs
from schema.charts.dagster.subschema.retention import (
    Retention,
    TickRetention,
    TickRetentionByType,
)
from schema.charts.dagster.subschema.run_launcher import (
    CeleryK8sRunLauncherConfig,
    K8sRunLauncherConfig,
    RunK8sConfig,
    RunLauncher,
    RunLauncherConfig,
    RunLauncherType,
)
from schema.charts.dagster.subschema.telemetry import Telemetry
from schema.charts.dagster.values import DagsterHelmValues
from schema.utils.helm_template import HelmTemplate


def to_camel_case(s: str) -> str:
    components = s.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


@pytest.fixture(name="template")
def helm_template() -> HelmTemplate:
    return HelmTemplate(
        helm_dir_path="helm/dagster",
        subchart_paths=["charts/dagster-user-deployments"],
        output="templates/configmap-instance.yaml",
        model=models.V1ConfigMap,
        namespace="test-namespace",
    )


@pytest.mark.parametrize("postgresql_scheme", ["", "postgresql", "postgresql+psycopg2"])
@pytest.mark.parametrize("storage", ["schedule_storage", "run_storage", "event_log_storage"])
def test_storage_postgres_db_config(template: HelmTemplate, postgresql_scheme: str, storage: str):
    postgresql_username = "username"
    postgresql_host = "1.1.1.1"
    postgresql_database = "database"
    postgresql_params = {
        "connect_timeout": 10,
        "application_name": "myapp",
        "options": "-c synchronous_commit=off",
    }
    postgresql_port = 8080
    helm_values = DagsterHelmValues.construct(
        postgresql=PostgreSQL.construct(
            postgresqlUsername=postgresql_username,
            postgresqlHost=postgresql_host,
            postgresqlDatabase=postgresql_database,
            postgresqlParams=postgresql_params,
            postgresqlScheme=postgresql_scheme,
            service=Service(port=postgresql_port),
        )
    )

    configmaps = template.render(helm_values)

    assert len(configmaps) == 1

    instance = yaml.full_load(configmaps[0].data["dagster.yaml"])

    assert instance[storage]

    postgres_db = instance[storage]["config"]["postgres_db"]

    assert postgres_db["username"] == postgresql_username
    assert postgres_db["password"] == {"env": "DAGSTER_PG_PASSWORD"}
    assert postgres_db["hostname"] == postgresql_host
    assert postgres_db["db_name"] == postgresql_database
    assert postgres_db["port"] == postgresql_port
    assert postgres_db["params"] == postgresql_params
    if not postgresql_scheme:
        assert "scheme" not in postgres_db
    else:
        assert postgres_db["scheme"] == postgresql_scheme


def test_k8s_run_launcher_config(template: HelmTemplate):
    job_namespace = "namespace"
    image_pull_policy = "Always"
    load_incluster_config = True
    env_config_maps = [{"name": "env_config_map"}]
    env_secrets = [{"name": "secret"}]
    env_vars = ["ENV_VAR"]
    volume_mounts = [
        {
            "mountPath": "/opt/dagster/dagster_home/dagster.yaml",
            "name": "dagster-instance",
            "subPath": "dagster.yaml",
        },
        {
            "name": "test-volume",
            "mountPath": "/opt/dagster/test_mount_path/volume_mounted_file.yaml",
            "subPath": "volume_mounted_file.yaml",
        },
    ]

    volumes = [
        {"name": "test-volume", "configMap": {"name": "test-volume-configmap"}},
        {"name": "test-pvc", "persistentVolumeClaim": {"claimName": "my_claim", "readOnly": False}},
    ]

    labels = {"my_label_key": "my_label_value"}

    helm_values = DagsterHelmValues.construct(
        runLauncher=RunLauncher.construct(
            type=RunLauncherType.K8S,
            config=RunLauncherConfig.construct(
                k8sRunLauncher=K8sRunLauncherConfig.construct(
                    jobNamespace=job_namespace,
                    imagePullPolicy=image_pull_policy,
                    loadInclusterConfig=load_incluster_config,
                    envConfigMaps=env_config_maps,
                    envSecrets=env_secrets,
                    envVars=env_vars,
                    volumeMounts=volume_mounts,
                    volumes=volumes,
                    labels=labels,
                )
            ),
        )
    )

    configmaps = template.render(helm_values)
    instance = yaml.full_load(configmaps[0].data["dagster.yaml"])
    run_launcher_config = instance["run_launcher"]

    assert run_launcher_config["module"] == "dagster_k8s"
    assert run_launcher_config["class"] == "K8sRunLauncher"
    assert run_launcher_config["config"]["job_namespace"] == job_namespace
    assert run_launcher_config["config"]["load_incluster_config"] == load_incluster_config
    assert run_launcher_config["config"]["image_pull_policy"] == image_pull_policy
    assert run_launcher_config["config"]["env_config_maps"] == [
        configmap["name"] for configmap in env_config_maps
    ]
    assert run_launcher_config["config"]["env_secrets"] == [
        secret["name"] for secret in env_secrets
    ]
    assert run_launcher_config["config"]["env_vars"] == env_vars
    assert run_launcher_config["config"]["volume_mounts"] == volume_mounts
    assert run_launcher_config["config"]["volumes"] == volumes
    assert run_launcher_config["config"]["labels"] == labels

    assert "fail_pod_on_run_failure" not in run_launcher_config["config"]


def test_k8s_run_launcher_fail_pod_on_run_failure(template: HelmTemplate):
    helm_values = DagsterHelmValues.construct(
        runLauncher=RunLauncher.construct(
            type=RunLauncherType.K8S,
            config=RunLauncherConfig.construct(
                k8sRunLauncher=K8sRunLauncherConfig.construct(
                    imagePullPolicy="Always",
                    loadInclusterConfig=True,
                    envConfigMaps=[],
                    envSecrets=[],
                    envVars=[],
                    volumeMounts=[],
                    volumes=[],
                    failPodOnRunFailure=True,
                )
            ),
        )
    )
    configmaps = template.render(helm_values)
    instance = yaml.full_load(configmaps[0].data["dagster.yaml"])
    run_launcher_config = instance["run_launcher"]

    assert run_launcher_config["config"]["fail_pod_on_run_failure"]


def test_k8s_run_launcher_resources(template: HelmTemplate):
    resources = {
        "requests": {"memory": "64Mi", "cpu": "250m"},
        "limits": {"memory": "128Mi", "cpu": "500m"},
    }

    helm_values = DagsterHelmValues.construct(
        runLauncher=RunLauncher.construct(
            type=RunLauncherType.K8S,
            config=RunLauncherConfig.construct(
                k8sRunLauncher=K8sRunLauncherConfig.construct(
                    imagePullPolicy="Always",
                    loadInclusterConfig=True,
                    envConfigMaps=[],
                    envSecrets=[],
                    envVars=[],
                    volumeMounts=[],
                    volumes=[],
                    resources=resources,
                )
            ),
        )
    )
    configmaps = template.render(helm_values)
    instance = yaml.full_load(configmaps[0].data["dagster.yaml"])
    run_launcher_config = instance["run_launcher"]

    assert run_launcher_config["config"]["resources"] == resources


def _check_valid_run_launcher_yaml(dagster_config, instance_class=K8sRunLauncher):
    with environ(
        {
            "DAGSTER_PG_PASSWORD": "hunter12",
            "DAGSTER_K8S_PIPELINE_RUN_ENV_CONFIGMAP": "fake-configmap",
            "DAGSTER_CELERY_BROKER_URL": "https://fake-celery-broker",
            "DAGSTER_CELERY_BACKEND_URL": "https://fake-celery-backend",
        }
    ):
        with tempfile.TemporaryDirectory() as temp_dir:
            with open(os.path.join(temp_dir, "dagster.yaml"), "w", encoding="utf8") as fd:
                yaml.dump(dagster_config, fd, default_flow_style=False)
                run_launcher_data = InstanceRef.from_dir(temp_dir).run_launcher_data
                process_result = process_config(
                    resolve_to_config_type(instance_class.config_type()),
                    run_launcher_data.config_dict,
                )
                assert process_result.success, str(process_result.errors)


def _check_valid_run_coordinator_yaml(dagster_config):
    with environ(
        {
            "DAGSTER_PG_PASSWORD": "hunter12",
        }
    ):
        with tempfile.TemporaryDirectory() as temp_dir:
            with open(os.path.join(temp_dir, "dagster.yaml"), "w", encoding="utf8") as fd:
                yaml.dump(dagster_config, fd, default_flow_style=False)
                run_coordinator_data = InstanceRef.from_dir(temp_dir).run_coordinator_data
                process_result = process_config(
                    resolve_to_config_type(QueuedRunCoordinator.config_type()),
                    run_coordinator_data.config_dict,
                )
                assert process_result.success, str(process_result.errors)


def test_k8s_run_launcher_scheduler_name(template: HelmTemplate):
    helm_values = DagsterHelmValues.construct(
        runLauncher=RunLauncher.construct(
            type=RunLauncherType.K8S,
            config=RunLauncherConfig.construct(
                k8sRunLauncher=K8sRunLauncherConfig.construct(
                    imagePullPolicy="Always",
                    loadInclusterConfig=True,
                    envConfigMaps=[],
                    envSecrets=[],
                    envVars=[],
                    volumeMounts=[],
                    volumes=[],
                    schedulerName="my-scheduler",
                )
            ),
        )
    )
    configmaps = template.render(helm_values)
    instance = yaml.full_load(configmaps[0].data["dagster.yaml"])

    _check_valid_run_launcher_yaml(instance)

    run_launcher_config = instance["run_launcher"]

    assert run_launcher_config["config"]["scheduler_name"] == "my-scheduler"


def test_k8s_run_launcher_security_context(template: HelmTemplate):
    sacred_rites_of_debugging = {"capabilities": {"add": ["SYS_PTRACE"]}}
    helm_values = DagsterHelmValues.construct(
        runLauncher=RunLauncher.construct(
            type=RunLauncherType.K8S,
            config=RunLauncherConfig.construct(
                k8sRunLauncher=K8sRunLauncherConfig.construct(
                    imagePullPolicy="Always",
                    loadInclusterConfig=True,
                    envConfigMaps=[],
                    envSecrets=[],
                    envVars=[],
                    volumeMounts=[],
                    volumes=[],
                    securityContext=sacred_rites_of_debugging,
                )
            ),
        )
    )
    configmaps = template.render(helm_values)
    instance = yaml.full_load(configmaps[0].data["dagster.yaml"])

    _check_valid_run_launcher_yaml(instance)

    run_launcher_config = instance["run_launcher"]

    assert run_launcher_config["config"]["security_context"] == sacred_rites_of_debugging


def test_k8s_run_launcher_raw_k8s_config(template: HelmTemplate):
    container_config = {
        "resources": {
            "requests": {"cpu": "250m", "memory": "64Mi"},
            "limits": {"cpu": "500m", "memory": "2560Mi"},
        }
    }

    pod_template_spec_metadata = {"namespace": "my_pod_namespace"}

    pod_spec_config = {"dns_policy": "value"}

    job_metadata = {"namespace": "my_job_value"}

    job_spec_config = {"backoff_limit": 120}

    helm_values = DagsterHelmValues.construct(
        runLauncher=RunLauncher.construct(
            type=RunLauncherType.K8S,
            config=RunLauncherConfig.construct(
                k8sRunLauncher=K8sRunLauncherConfig.construct(
                    imagePullPolicy="Always",
                    loadInclusterConfig=True,
                    envConfigMaps=[],
                    envSecrets=[],
                    envVars=[],
                    volumeMounts=[],
                    volumes=[],
                    runK8sConfig=RunK8sConfig(
                        containerConfig=container_config,
                        podSpecConfig=pod_spec_config,
                        podTemplateSpecMetadata=pod_template_spec_metadata,
                        jobMetadata=job_metadata,
                        jobSpecConfig=job_spec_config,
                    ),
                )
            ),
        )
    )
    configmaps = template.render(helm_values)
    instance = yaml.full_load(configmaps[0].data["dagster.yaml"])

    _check_valid_run_launcher_yaml(instance)

    run_launcher_config = instance["run_launcher"]

    assert run_launcher_config["config"]["run_k8s_config"] == {
        "container_config": container_config,
        "pod_spec_config": pod_spec_config,
        "pod_template_spec_metadata": pod_template_spec_metadata,
        "job_metadata": job_metadata,
        "job_spec_config": job_spec_config,
    }


def test_celery_k8s_run_launcher_config(template: HelmTemplate):
    image = {"repository": "test_repo", "tag": "test_tag", "pullPolicy": "Always"}

    configSource = {
        "broker_transport_options": {"priority_steps": [9]},
        "worker_concurrency": 1,
    }

    workerQueues = [
        {"name": "dagster", "replicaCount": 2},
        {"name": "extra-queue-1", "replicaCount": 1},
    ]

    volume_mounts = [
        {
            "mountPath": "/opt/dagster/dagster_home/dagster.yaml",
            "name": "dagster-instance",
            "subPath": "dagster.yaml",
        },
        {
            "name": "test-volume",
            "mountPath": "/opt/dagster/test_mount_path/volume_mounted_file.yaml",
            "subPath": "volume_mounted_file.yaml",
        },
    ]

    volumes = [
        {"name": "test-volume", "configMap": {"name": "test-volume-configmap"}},
        {"name": "test-pvc", "persistentVolumeClaim": {"claimName": "my_claim", "readOnly": False}},
    ]

    labels = {"my_label_key": "my_label_value"}

    image_pull_secrets = [{"name": "IMAGE_PULL_SECRET"}]

    helm_values = DagsterHelmValues.construct(
        imagePullSecrets=image_pull_secrets,
        runLauncher=RunLauncher.construct(
            type=RunLauncherType.CELERY,
            config=RunLauncherConfig.construct(
                celeryK8sRunLauncher=CeleryK8sRunLauncherConfig.construct(
                    image=image,
                    configSource=configSource,
                    workerQueues=workerQueues,
                    volumeMounts=volume_mounts,
                    volumes=volumes,
                    labels=labels,
                )
            ),
        ),
    )

    configmaps = template.render(helm_values)
    instance = yaml.full_load(configmaps[0].data["dagster.yaml"])
    run_launcher_config = instance["run_launcher"]

    assert run_launcher_config["module"] == "dagster_celery_k8s"
    assert run_launcher_config["class"] == "CeleryK8sRunLauncher"

    assert run_launcher_config["config"]["config_source"] == configSource

    assert run_launcher_config["config"]["broker"] == {"env": "DAGSTER_CELERY_BROKER_URL"}

    assert run_launcher_config["config"]["backend"] == {"env": "DAGSTER_CELERY_BACKEND_URL"}

    assert run_launcher_config["config"]["volume_mounts"] == volume_mounts
    assert run_launcher_config["config"]["volumes"] == volumes
    assert run_launcher_config["config"]["labels"] == labels

    assert run_launcher_config["config"]["image_pull_secrets"] == image_pull_secrets

    assert run_launcher_config["config"]["image_pull_policy"] == "Always"

    assert run_launcher_config["config"]["service_account_name"] == "release-name-dagster"

    assert "fail_pod_on_run_failure" not in run_launcher_config["config"]

    helm_values_with_image_pull_policy = DagsterHelmValues.construct(
        runLauncher=RunLauncher.construct(
            type=RunLauncherType.CELERY,
            config=RunLauncherConfig.construct(
                celeryK8sRunLauncher=CeleryK8sRunLauncherConfig.construct(
                    image=image,
                    configSource=configSource,
                    workerQueues=workerQueues,
                    volumeMounts=volume_mounts,
                    volumes=volumes,
                    imagePullPolicy="IfNotPresent",
                )
            ),
        ),
    )

    configmaps = template.render(helm_values_with_image_pull_policy)
    instance = yaml.full_load(configmaps[0].data["dagster.yaml"])
    run_launcher_config = instance["run_launcher"]
    assert run_launcher_config["config"]["image_pull_policy"] == "IfNotPresent"

    helm_values_with_fail_pod_on_run_failure = DagsterHelmValues.construct(
        runLauncher=RunLauncher.construct(
            type=RunLauncherType.CELERY,
            config=RunLauncherConfig.construct(
                celeryK8sRunLauncher=CeleryK8sRunLauncherConfig.construct(
                    image=image,
                    configSource=configSource,
                    workerQueues=workerQueues,
                    failPodOnRunFailure=True,
                )
            ),
        ),
    )

    configmaps = template.render(helm_values_with_fail_pod_on_run_failure)
    instance = yaml.full_load(configmaps[0].data["dagster.yaml"])
    run_launcher_config = instance["run_launcher"]
    assert run_launcher_config["config"]["fail_pod_on_run_failure"]


def test_celery_k8s_run_launcher_default_namespace(template: HelmTemplate):
    default_helm_values = DagsterHelmValues.construct(
        runLauncher=RunLauncher.construct(
            type=RunLauncherType.CELERY,
            config=RunLauncherConfig.construct(
                celeryK8sRunLauncher=CeleryK8sRunLauncherConfig.construct()
            ),
        )
    )
    configmaps = template.render(default_helm_values)
    instance = yaml.full_load(configmaps[0].data["dagster.yaml"])
    _check_valid_run_launcher_yaml(instance, instance_class=CeleryK8sRunLauncher)
    run_launcher_config = instance["run_launcher"]["config"]
    assert run_launcher_config["job_namespace"] == template.namespace


def test_celery_k8s_run_launcher_set_namespace(template: HelmTemplate):
    default_helm_values = DagsterHelmValues.construct(
        runLauncher=RunLauncher.construct(
            type=RunLauncherType.CELERY,
            config=RunLauncherConfig.construct(
                celeryK8sRunLauncher=CeleryK8sRunLauncherConfig.construct(
                    jobNamespace="my-namespace"
                )
            ),
        )
    )
    configmaps = template.render(default_helm_values)
    instance = yaml.full_load(configmaps[0].data["dagster.yaml"])
    _check_valid_run_launcher_yaml(instance, instance_class=CeleryK8sRunLauncher)
    run_launcher_config = instance["run_launcher"]["config"]
    assert run_launcher_config["job_namespace"] == "my-namespace"


def test_queued_run_coordinator_config_default(template: HelmTemplate):
    helm_values = DagsterHelmValues.construct(
        dagsterDaemon=Daemon.construct(runCoordinator=RunCoordinator.construct())
    )

    configmaps = template.render(helm_values)
    assert len(configmaps) == 1

    yaml.full_load(configmaps[0].data["dagster.yaml"])
    instance = yaml.full_load(configmaps[0].data["dagster.yaml"])

    _check_valid_run_coordinator_yaml(instance)

    assert instance["run_coordinator"]["module"] == "dagster.core.run_coordinator"
    assert instance["run_coordinator"]["class"] == "QueuedRunCoordinator"

    assert instance["run_coordinator"]["config"]["max_concurrent_runs"] == -1
    assert instance["run_coordinator"]["config"]["dequeue_use_threads"]
    assert instance["run_coordinator"]["config"]["dequeue_num_workers"] == 4


@pytest.mark.parametrize("enabled", [True, False])
@pytest.mark.parametrize("max_concurrent_runs", [0, 50])
def test_queued_run_coordinator_config(
    template: HelmTemplate, enabled: bool, max_concurrent_runs: int
):
    tag_concurrency_limits = [TagConcurrencyLimit(key="key", value="value", limit=10)]
    dequeue_interval_seconds = 50
    dequeue_num_workers = 8
    helm_values = DagsterHelmValues.construct(
        dagsterDaemon=Daemon.construct(
            runCoordinator=RunCoordinator.construct(
                enabled=enabled,
                type=RunCoordinatorType.QUEUED,
                config=RunCoordinatorConfig.construct(
                    queuedRunCoordinator=QueuedRunCoordinatorConfig.construct(
                        maxConcurrentRuns=max_concurrent_runs,
                        tagConcurrencyLimits=tag_concurrency_limits,
                        dequeueIntervalSeconds=dequeue_interval_seconds,
                        dequeueUseThreads=True,
                        dequeueNumWorkers=dequeue_num_workers,
                    )
                ),
            )
        )
    )
    configmaps = template.render(helm_values)
    assert len(configmaps) == 1

    instance = yaml.full_load(configmaps[0].data["dagster.yaml"])

    _check_valid_run_coordinator_yaml(instance)

    assert ("run_coordinator" in instance) == enabled
    if enabled:
        assert instance["run_coordinator"]["module"] == "dagster.core.run_coordinator"
        assert instance["run_coordinator"]["class"] == "QueuedRunCoordinator"
        assert instance["run_coordinator"]["config"]

        run_coordinator_config = instance["run_coordinator"]["config"]

        assert run_coordinator_config["max_concurrent_runs"] == max_concurrent_runs
        assert run_coordinator_config["dequeue_interval_seconds"] == dequeue_interval_seconds

        assert run_coordinator_config["dequeue_use_threads"]
        assert run_coordinator_config["dequeue_num_workers"] == dequeue_num_workers

        assert len(run_coordinator_config["tag_concurrency_limits"]) == len(tag_concurrency_limits)
        assert run_coordinator_config["tag_concurrency_limits"] == [
            tag_concurrency_limit.dict() for tag_concurrency_limit in tag_concurrency_limits
        ]


def test_custom_run_coordinator_config(template: HelmTemplate):
    module = "a_module"
    class_ = "Class"
    config_field_one = "1"
    config_field_two = "two"
    config = {"config_field_one": config_field_one, "config_field_two": config_field_two}
    helm_values = DagsterHelmValues.construct(
        dagsterDaemon=Daemon.construct(
            runCoordinator=RunCoordinator.construct(
                enabled=True,
                type=RunCoordinatorType.CUSTOM,
                config=RunCoordinatorConfig.construct(
                    customRunCoordinator=ConfigurableClass.construct(
                        module=module,
                        class_=class_,
                        config=config,
                    )
                ),
            )
        )
    )
    configmaps = template.render(helm_values)
    assert len(configmaps) == 1

    instance = yaml.full_load(configmaps[0].data["dagster.yaml"])

    assert instance["run_coordinator"]["module"] == module
    assert instance["run_coordinator"]["class"] == class_
    assert instance["run_coordinator"]["config"] == config


def test_noop_compute_log_manager(template: HelmTemplate):
    helm_values = DagsterHelmValues.construct(
        computeLogManager=ComputeLogManager.construct(type=ComputeLogManagerType.NOOP)
    )

    configmaps = template.render(helm_values)
    instance = yaml.full_load(configmaps[0].data["dagster.yaml"])
    compute_logs_config = instance["compute_logs"]

    assert compute_logs_config["module"] == "dagster.core.storage.noop_compute_log_manager"
    assert compute_logs_config["class"] == "NoOpComputeLogManager"


def test_azure_blob_compute_log_manager(template: HelmTemplate):
    storage_account = "account"
    container = "container"
    secret_key = "secret_key"
    default_azure_credential = {"exclude_cli_credential": True}
    local_dir = "/dir"
    prefix = "prefix"
    upload_interval = 30
    helm_values = DagsterHelmValues.construct(
        computeLogManager=ComputeLogManager.construct(
            type=ComputeLogManagerType.AZURE,
            config=ComputeLogManagerConfig.construct(
                azureBlobComputeLogManager=AzureBlobComputeLogManagerModel(
                    storageAccount=storage_account,
                    container=container,
                    secretKey=secret_key,
                    defaultAzureCredential=default_azure_credential,
                    localDir=local_dir,
                    prefix=prefix,
                    uploadInterval=upload_interval,
                )
            ),
        )
    )

    configmaps = template.render(helm_values)
    instance = yaml.full_load(configmaps[0].data["dagster.yaml"])
    compute_logs_config = instance["compute_logs"]

    assert compute_logs_config["module"] == "dagster_azure.blob.compute_log_manager"
    assert compute_logs_config["class"] == "AzureBlobComputeLogManager"
    assert compute_logs_config["config"].keys() == AzureBlobComputeLogManager.config_type().keys()
    assert compute_logs_config["config"] == {
        "storage_account": storage_account,
        "container": container,
        "secret_key": secret_key,
        "default_azure_credential": default_azure_credential,
        "local_dir": local_dir,
        "prefix": prefix,
        "upload_interval": upload_interval,
    }

    # Test all config fields in configurable class


def test_gcs_compute_log_manager(template: HelmTemplate):
    bucket = "bucket"
    local_dir = "/dir"
    prefix = "prefix"
    json_credentials_envvar = "ENV_VAR"
    upload_interval = 30
    helm_values = DagsterHelmValues.construct(
        computeLogManager=ComputeLogManager.construct(
            type=ComputeLogManagerType.GCS,
            config=ComputeLogManagerConfig.construct(
                gcsComputeLogManager=GCSComputeLogManagerModel(
                    bucket=bucket,
                    localDir=local_dir,
                    prefix=prefix,
                    jsonCredentialsEnvvar=json_credentials_envvar,
                    uploadInterval=upload_interval,
                )
            ),
        )
    )

    configmaps = template.render(helm_values)
    instance = yaml.full_load(configmaps[0].data["dagster.yaml"])
    compute_logs_config = instance["compute_logs"]

    assert compute_logs_config["module"] == "dagster_gcp.gcs.compute_log_manager"
    assert compute_logs_config["class"] == "GCSComputeLogManager"
    assert compute_logs_config["config"] == {
        "bucket": bucket,
        "local_dir": local_dir,
        "prefix": prefix,
        "json_credentials_envvar": json_credentials_envvar,
        "upload_interval": upload_interval,
    }

    # Test all config fields in configurable class
    assert compute_logs_config["config"].keys() == GCSComputeLogManager.config_type().keys()


def test_s3_compute_log_manager(template: HelmTemplate):
    bucket = "bucket"
    local_dir = "/dir"
    prefix = "prefix"
    use_ssl = True
    verify = True
    verify_cert_path = "/path"
    endpoint_url = "endpoint.com"
    skip_empty_files = True
    upload_interval = 30
    upload_extra_args = {"ACL": "public-read"}
    show_url_only = True
    region = "us-west-1"

    helm_values = DagsterHelmValues.construct(
        computeLogManager=ComputeLogManager.construct(
            type=ComputeLogManagerType.S3,
            config=ComputeLogManagerConfig.construct(
                s3ComputeLogManager=S3ComputeLogManagerModel(
                    bucket=bucket,
                    localDir=local_dir,
                    prefix=prefix,
                    useSsl=use_ssl,
                    verify=verify,
                    verifyCertPath=verify_cert_path,
                    endpointUrl=endpoint_url,
                    skipEmptyFiles=skip_empty_files,
                    uploadInterval=upload_interval,
                    uploadExtraArgs=upload_extra_args,
                    showUrlOnly=show_url_only,
                    region=region,
                )
            ),
        )
    )

    configmaps = template.render(helm_values)
    instance = yaml.full_load(configmaps[0].data["dagster.yaml"])
    compute_logs_config = instance["compute_logs"]

    assert compute_logs_config["module"] == "dagster_aws.s3.compute_log_manager"
    assert compute_logs_config["class"] == "S3ComputeLogManager"
    assert compute_logs_config["config"] == {
        "bucket": bucket,
        "local_dir": local_dir,
        "prefix": prefix,
        "use_ssl": use_ssl,
        "verify": verify,
        "verify_cert_path": verify_cert_path,
        "endpoint_url": endpoint_url,
        "skip_empty_files": skip_empty_files,
        "upload_interval": upload_interval,
        "upload_extra_args": upload_extra_args,
        "show_url_only": show_url_only,
        "region": region,
    }

    # Test all config fields in configurable class
    assert compute_logs_config["config"].keys() == S3ComputeLogManager.config_type().keys()


def test_s3_compute_log_manager_no_verify(template: HelmTemplate):
    bucket = "bucket"
    local_dir = "/dir"

    # extra test just to check for verify: false
    helm_values = DagsterHelmValues.construct(
        computeLogManager=ComputeLogManager.construct(
            type=ComputeLogManagerType.S3,
            config=ComputeLogManagerConfig.construct(
                s3ComputeLogManager=S3ComputeLogManagerModel(
                    bucket=bucket,
                    localDir=local_dir,
                    prefix=None,
                    useSsl=None,
                    verify=False,
                    verifyCertPath=None,
                    endpointUrl=None,
                    skipEmptyFiles=None,
                    uploadInterval=None,
                    uploadExtraArgs=None,
                    showUrlOnly=None,
                    region=None,
                )
            ),
        )
    )

    configmaps = template.render(helm_values)
    instance = yaml.full_load(configmaps[0].data["dagster.yaml"])
    compute_logs_config = instance["compute_logs"]

    assert compute_logs_config["module"] == "dagster_aws.s3.compute_log_manager"
    assert compute_logs_config["class"] == "S3ComputeLogManager"
    assert compute_logs_config["config"] == {
        "bucket": bucket,
        "local_dir": local_dir,
        "verify": False,
    }


def test_custom_compute_log_manager_config(template: HelmTemplate):
    module = "a_module"
    class_ = "Class"
    config_field_one = "1"
    config_field_two = "two"
    config = {"config_field_one": config_field_one, "config_field_two": config_field_two}
    helm_values = DagsterHelmValues.construct(
        computeLogManager=ComputeLogManager.construct(
            type=ComputeLogManagerType.CUSTOM,
            config=ComputeLogManagerConfig.construct(
                customComputeLogManager=ConfigurableClass.construct(
                    module=module,
                    class_=class_,
                    config=config,
                )
            ),
        )
    )

    configmaps = template.render(helm_values)
    instance = yaml.full_load(configmaps[0].data["dagster.yaml"])
    compute_logs_config = instance["compute_logs"]

    assert compute_logs_config["module"] == module
    assert compute_logs_config["class"] == class_
    assert compute_logs_config["config"] == config


def test_custom_python_logs_config(template: HelmTemplate):
    log_level = "INFO"
    managed_python_loggers = ["foo", "bar", "baz"]
    handler_config = {
        "handlers": {
            "myHandler": {"class": "logging.StreamHandler", "level": "INFO", "stream": "foo"}
        },
        "formatters": {"myFormatter": {"format": "%(message)s"}},
    }
    helm_values = DagsterHelmValues.construct(
        pythonLogs=PythonLogs.construct(
            pythonLogLevel=log_level,
            managedPythonLoggers=managed_python_loggers,
            dagsterHandlerConfig=handler_config,
        )
    )

    configmaps = template.render(helm_values)
    instance = yaml.full_load(configmaps[0].data["dagster.yaml"])
    python_logs_config = instance["python_logs"]

    assert python_logs_config["python_log_level"] == log_level
    assert python_logs_config["managed_python_loggers"] == managed_python_loggers
    assert python_logs_config["dagster_handler_config"] == handler_config


def test_custom_python_logs_missing_config(template: HelmTemplate):
    helm_values = DagsterHelmValues.construct(
        pythonLogs=PythonLogs.construct(pythonLogLevel="INFO")
    )

    configmaps = template.render(helm_values)
    instance = yaml.full_load(configmaps[0].data["dagster.yaml"])
    python_logs_config = instance["python_logs"]

    assert python_logs_config["python_log_level"] == "INFO"
    assert "managed_python_loggers" not in python_logs_config
    assert "dagster_handler_config" not in python_logs_config


@pytest.mark.parametrize("enabled", [True, False])
def test_telemetry(template: HelmTemplate, enabled: bool):
    helm_values = DagsterHelmValues.construct(telemetry=Telemetry.construct(enabled=enabled))

    configmaps = template.render(helm_values)
    instance = yaml.full_load(configmaps[0].data["dagster.yaml"])
    telemetry_config = instance.get("telemetry")

    assert telemetry_config["enabled"] == enabled


@pytest.mark.parametrize(
    argnames=["json_schema_model", "compute_log_manager_class"],
    argvalues=[
        (AzureBlobComputeLogManagerModel, AzureBlobComputeLogManager),
        (GCSComputeLogManagerModel, GCSComputeLogManager),
        (S3ComputeLogManagerModel, S3ComputeLogManager),
    ],
)
def test_compute_log_manager_has_schema(json_schema_model, compute_log_manager_class):
    json_schema_fields = json_schema_model.schema()["properties"].keys()
    compute_log_manager_fields = set(
        map(to_camel_case, compute_log_manager_class.config_type().keys())
    )

    assert json_schema_fields == compute_log_manager_fields


@pytest.mark.parametrize(
    argnames=["json_schema_model", "run_coordinator_class"],
    argvalues=[
        (QueuedRunCoordinatorConfig, QueuedRunCoordinator),
    ],
)
def test_run_coordinator_has_schema(json_schema_model, run_coordinator_class):
    json_schema_fields = json_schema_model.schema()["properties"].keys()
    run_coordinator_fields = set(
        map(
            to_camel_case,
            {
                key
                for key in run_coordinator_class.config_type().keys()
                if key not in {"user_code_failure_retry_delay", "max_user_code_failure_retries"}
            },
        )
    )

    assert json_schema_fields == run_coordinator_fields


def test_retention(template: HelmTemplate):
    helm_values = DagsterHelmValues.construct(
        retention=Retention.construct(
            enabled=True,
            schedule=TickRetention.construct(
                purgeAfterDays=30,
            ),
            sensor=TickRetention.construct(
                purgeAfterDays=TickRetentionByType(
                    skipped=7,
                    success=30,
                    failure=30,
                    started=30,
                ),
            ),
            autoMaterialize=TickRetention.construct(
                purgeAfterDays=TickRetentionByType(
                    skipped=1,
                    success=2,
                    failure=3,
                    started=4,
                ),
            ),
        )
    )

    configmaps = template.render(helm_values)
    assert len(configmaps) == 1
    instance = yaml.full_load(configmaps[0].data["dagster.yaml"])
    retention_config = instance["retention"]
    assert retention_config.keys() == retention_config_schema().config_type.fields.keys()
    assert instance["retention"]["schedule"]["purge_after_days"] == 30
    assert instance["retention"]["sensor"]["purge_after_days"]["skipped"] == 7
    assert instance["retention"]["sensor"]["purge_after_days"]["success"] == 30
    assert instance["retention"]["sensor"]["purge_after_days"]["failure"] == 30
    assert instance["retention"]["auto_materialize"]["purge_after_days"] == {
        "skipped": 1,
        "success": 2,
        "failure": 3,
        "started": 4,
    }


def _check_valid_instance_yaml(dagster_config, instance_class=K8sRunLauncher):
    with tempfile.TemporaryDirectory() as temp_dir:
        with open(os.path.join(temp_dir, "dagster.yaml"), "w", encoding="utf8") as fd:
            yaml.dump(dagster_config, fd, default_flow_style=False)
            # Raises if the config is invalid
            dagster_instance_config(temp_dir)


def test_additional_config(template: HelmTemplate):
    helm_values = DagsterHelmValues.construct(
        additionalInstanceConfig={
            "code_servers": {
                "reload_timeout": 500,
            }
        }
    )

    configmaps = template.render(helm_values)
    assert len(configmaps) == 1
    instance = yaml.full_load(configmaps[0].data["dagster.yaml"])

    _check_valid_instance_yaml(instance)
    code_server_config = instance["code_servers"]
    assert code_server_config["reload_timeout"] == 500


def test_retention_backcompat(template: HelmTemplate):
    helm_values = DagsterHelmValues.construct()
    configmaps = template.render(helm_values)
    instance = yaml.full_load(configmaps[0].data["dagster.yaml"])
    assert not instance.get("retention")
