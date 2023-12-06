import pytest
import yaml
from dagster_k8s.models import k8s_model_from_dict, k8s_snake_case_dict
from kubernetes import client as k8s_client
from kubernetes.client import models
from schema.charts.dagster.subschema.webserver import Server, Webserver, Workspace
from schema.charts.dagster.values import DagsterHelmValues
from schema.charts.utils import kubernetes
from schema.utils.helm_template import HelmTemplate


@pytest.fixture(name="deployment_template")
def deployment_helm_template() -> HelmTemplate:
    return HelmTemplate(
        helm_dir_path="helm/dagster",
        subchart_paths=["charts/dagster-user-deployments"],
        output="templates/deployment-webserver.yaml",
        model=models.V1Deployment,
    )


@pytest.fixture(name="service_template")
def service_helm_template() -> HelmTemplate:
    return HelmTemplate(
        helm_dir_path="helm/dagster",
        subchart_paths=["charts/dagster-user-deployments"],
        output="templates/service-webserver.yaml",
        model=models.V1Service,
    )


@pytest.fixture(name="configmap_template")
def configmap_helm_template() -> HelmTemplate:
    return HelmTemplate(
        helm_dir_path="helm/dagster",
        subchart_paths=["charts/dagster-user-deployments"],
        output="templates/configmap-env-webserver.yaml",
        model=models.V1ConfigMap,
    )


@pytest.fixture(name="workspace_configmap_template")
def workspace_configmap_helm_template() -> HelmTemplate:
    return HelmTemplate(
        helm_dir_path="helm/dagster",
        subchart_paths=["charts/dagster-user-deployments"],
        output="templates/configmap-workspace.yaml",
        model=models.V1ConfigMap,
    )


# Parametrizing "webserver_field" here tests backcompat. `dagit` was the old field name.
# This parametrization can be removed in 2.0.
@pytest.mark.parametrize("webserver_field", ["dagsterWebserver", "dagit"])
@pytest.mark.parametrize(
    "service_port",
    [
        80,
        3000,
        8080,
    ],
)
def test_webserver_port(deployment_template: HelmTemplate, webserver_field: str, service_port: int):
    helm_values = DagsterHelmValues.construct(
        **{  # type: ignore[call-arg]
            webserver_field: Webserver.construct(
                service=kubernetes.Service(
                    type="ClusterIP",
                    port=service_port,
                ),
            )
        }
    )

    webserver_template = deployment_template.render(helm_values)

    # Make sure dagster-webserver will start up serving the correct port
    dagster_webserver_command = "".join(
        webserver_template[0].spec.template.spec.containers[0].command
    )
    port_arg = f"-p {service_port}"
    assert port_arg in dagster_webserver_command

    # Make sure k8s will open the correct port
    k8s_port = webserver_template[0].spec.template.spec.containers[0].ports[0].container_port
    assert k8s_port == service_port


# Parametrizing "webserver_field" here tests backcompat. `dagit` was the old field name.
# This parametrization can be removed in 2.0.
@pytest.mark.parametrize("webserver_field", ["dagsterWebserver", "dagit"])
@pytest.mark.parametrize("enabled", [True, False])
def test_startup_probe_enabled(
    deployment_template: HelmTemplate, webserver_field: str, enabled: bool
):
    helm_values = DagsterHelmValues.construct(
        **{
            webserver_field: Webserver.construct(
                startupProbe=kubernetes.StartupProbe(enabled=enabled)
            )
        }
    )

    webserver = deployment_template.render(helm_values)
    assert len(webserver) == 1
    webserver = webserver[0]

    assert len(webserver.spec.template.spec.containers) == 1
    container = webserver.spec.template.spec.containers[0]

    assert (container.startup_probe is not None) == enabled


# Parametrizing "webserver_field" here tests backcompat. `dagit` was the old field name.
# This parametrization can be removed in 2.0.
@pytest.mark.parametrize("webserver_field", ["dagsterWebserver", "dagit"])
def test_readiness_probe(deployment_template: HelmTemplate, webserver_field: str):
    helm_values = DagsterHelmValues.construct(**{webserver_field: Webserver.construct()})

    webserver = deployment_template.render(helm_values)
    assert len(webserver) == 1
    webserver = webserver[0]

    assert len(webserver.spec.template.spec.containers) == 1
    container = webserver.spec.template.spec.containers[0]

    assert container.startup_probe is None
    assert container.liveness_probe is None
    assert container.readiness_probe is not None


def test_webserver_read_only_disabled(deployment_template: HelmTemplate):
    helm_values = DagsterHelmValues.construct()

    webserver = deployment_template.render(helm_values)

    assert len(webserver) == 1
    assert "--read-only" not in "".join(webserver[0].spec.template.spec.containers[0].command)


# Parametrizing "webserver_field" here tests backcompat. `dagit` was the old field name.
# This parametrization can be removed in 2.0.
@pytest.mark.parametrize("webserver_field", ["dagsterWebserver", "dagit"])
def test_webserver_read_only_enabled(deployment_template: HelmTemplate, webserver_field: str):
    helm_values = DagsterHelmValues.construct(
        **{webserver_field: Webserver.construct(enableReadOnly=True)}
    )

    deployments = deployment_template.render(helm_values)

    assert len(deployments) == 2
    assert [
        "--read-only" in "".join(deployment.spec.template.spec.containers[0].command)
        for deployment in deployments
    ] == [False, True]
    assert [deployment.metadata.name for deployment in deployments] == [
        "release-name-dagster-webserver",
        "release-name-dagster-webserver-read-only",
    ]

    assert [
        deployment.spec.template.metadata.labels["component"] for deployment in deployments
    ] == [
        "dagster-webserver",
        "dagster-webserver-read-only",
    ]


# Parametrizing "webserver_field" here tests backcompat. `dagit` was the old field name.
# This parametrization can be removed in 2.0.
@pytest.mark.parametrize("webserver_field", ["dagsterWebserver", "dagit"])
@pytest.mark.parametrize("enable_read_only", [True, False])
@pytest.mark.parametrize("chart_version", ["0.11.0", "0.11.1"])
def test_webserver_default_image_tag_is_chart_version(
    deployment_template: HelmTemplate,
    webserver_field: str,
    enable_read_only: bool,
    chart_version: str,
):
    helm_values = DagsterHelmValues.construct(
        **{webserver_field: Webserver.construct(enableReadOnly=enable_read_only)}
    )

    webserver_deployments = deployment_template.render(helm_values, chart_version=chart_version)

    assert len(webserver_deployments) == 1 + int(enable_read_only)

    for webserver_deployment in webserver_deployments:
        image = webserver_deployment.spec.template.spec.containers[0].image
        _, image_tag = image.split(":")

        assert image_tag == chart_version


# Parametrizing "webserver_field" here tests backcompat. `dagit` was the old field name.
# This parametrization can be removed in 2.0.
@pytest.mark.parametrize("webserver_field", ["dagsterWebserver", "dagit"])
def test_webserver_image_tag(deployment_template: HelmTemplate, webserver_field: str):
    repository = "repository"
    tag = "tag"
    helm_values = DagsterHelmValues.construct(
        **{
            webserver_field: Webserver.construct(
                image=kubernetes.Image.construct(repository=repository, tag=tag)
            )
        }
    )

    webserver_deployments = deployment_template.render(helm_values)

    assert len(webserver_deployments) == 1

    image = webserver_deployments[0].spec.template.spec.containers[0].image
    image_name, image_tag = image.split(":")

    assert image_name == repository
    assert image_tag == tag


# Parametrizing "webserver_field" here tests backcompat. `dagit` was the old field name.
# This parametrization can be removed in 2.0.
@pytest.mark.parametrize("webserver_field", ["dagsterWebserver", "dagit"])
@pytest.mark.parametrize("name_override", ["webserver", "new-name"])
def test_webserver_name_override(deployment_template, webserver_field, name_override):
    helm_values = DagsterHelmValues.construct(
        **{webserver_field: Webserver.construct(nameOverride=name_override)}
    )
    webserver_deployments = deployment_template.render(helm_values)

    assert len(webserver_deployments) == 1

    deployment_name = webserver_deployments[0].metadata.name

    assert deployment_name == f"{deployment_template.release_name}-{name_override}"


# Parametrizing "webserver_field" here tests backcompat. `dagit` was the old field name.
# This parametrization can be removed in 2.0.
@pytest.mark.parametrize("webserver_field", ["dagsterWebserver", "dagit"])
@pytest.mark.parametrize("path_prefix", ["webserver", "some-path"])
def test_webserver_path_prefix(deployment_template, webserver_field, path_prefix):
    helm_values = DagsterHelmValues.construct(
        **{webserver_field: Webserver.construct(pathPrefix=path_prefix)}
    )
    webserver_deployments = deployment_template.render(helm_values)

    assert len(webserver_deployments) == 1

    command = " ".join(webserver_deployments[0].spec.template.spec.containers[0].command)

    assert f"--path-prefix {path_prefix}" in command


def test_webserver_service(service_template):
    helm_values = DagsterHelmValues.construct()
    webserver_template = service_template.render(helm_values)

    assert len(webserver_template) == 1
    assert webserver_template[0].metadata.name == "release-name-dagster-webserver"


def test_webserver_service_read_only(service_template):
    helm_values = DagsterHelmValues.construct(
        dagsterWebserver=Webserver.construct(enableReadOnly=True)
    )
    webserver_template = service_template.render(helm_values)

    assert len(webserver_template) == 2
    assert [obj.metadata.name for obj in webserver_template] == [
        "release-name-dagster-webserver",
        "release-name-dagster-webserver-read-only",
    ]
    assert [obj.spec.selector["component"] for obj in webserver_template] == [
        "dagster-webserver",
        "dagster-webserver-read-only",
    ]


def test_webserver_db_statement_timeout(deployment_template: HelmTemplate):
    db_statement_timeout_ms = 9000
    helm_values = DagsterHelmValues.construct(
        dagsterWebserver=Webserver.construct(dbStatementTimeout=db_statement_timeout_ms)
    )

    webserver_deployments = deployment_template.render(helm_values)
    command = " ".join(webserver_deployments[0].spec.template.spec.containers[0].command)

    assert f"--db-statement-timeout {db_statement_timeout_ms}" in command


def test_webserver_db_pool_recycle(deployment_template: HelmTemplate):
    pool_recycle_s = 7200
    helm_values = DagsterHelmValues.construct(
        dagsterWebserver=Webserver.construct(dbPoolRecycle=pool_recycle_s)
    )

    webserver_deployments = deployment_template.render(helm_values)
    command = " ".join(webserver_deployments[0].spec.template.spec.containers[0].command)

    assert f"--db-pool-recycle {pool_recycle_s}" in command


def test_webserver_log_level(deployment_template: HelmTemplate):
    log_level = "trace"
    helm_values = DagsterHelmValues.construct(
        dagsterWebserver=Webserver.construct(logLevel=log_level)
    )

    deployments = deployment_template.render(helm_values)
    command = " ".join(deployments[0].spec.template.spec.containers[0].command)

    assert f"--log-level {log_level}" in command

    helm_values = DagsterHelmValues.construct(dagsterWebserver=Webserver.construct())

    deployments = deployment_template.render(helm_values)
    command = " ".join(deployments[0].spec.template.spec.containers[0].command)

    assert "--log-level" not in command


def test_webserver_labels(deployment_template: HelmTemplate):
    deployment_labels = {"deployment_label": "label"}
    pod_labels = {"pod_label": "label"}
    helm_values = DagsterHelmValues.construct(
        dagsterWebserver=Webserver.construct(
            deploymentLabels=deployment_labels,
            labels=pod_labels,
        )
    )

    [deployment] = deployment_template.render(helm_values)

    assert set(deployment_labels.items()).issubset(deployment.metadata.labels.items())
    assert set(pod_labels.items()).issubset(deployment.spec.template.metadata.labels.items())


def test_webserver_volumes(deployment_template: HelmTemplate):
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
        dagsterWebserver=Webserver.construct(volumes=volumes, volumeMounts=volume_mounts)
    )

    [deployment] = deployment_template.render(helm_values)

    deployed_volume_mounts = deployment.spec.template.spec.containers[0].volume_mounts
    assert deployed_volume_mounts[2:] == [
        k8s_model_from_dict(
            k8s_client.models.V1VolumeMount,
            k8s_snake_case_dict(k8s_client.models.V1VolumeMount, volume_mount),
        )
        for volume_mount in volume_mounts
    ]

    deployed_volumes = deployment.spec.template.spec.volumes
    assert deployed_volumes[2:] == [
        k8s_model_from_dict(
            k8s_client.models.V1Volume, k8s_snake_case_dict(k8s_client.models.V1Volume, volume)
        )
        for volume in volumes
    ]


def test_webserver_workspace_external_configmap(deployment_template: HelmTemplate):
    helm_values = DagsterHelmValues.construct(
        dagsterWebserver=Webserver.construct(
            workspace=Workspace(
                enabled=True,
                servers=[],
                externalConfigmap="test-external-workspace",
            )
        ),
    )

    [webserver_deployment] = deployment_template.render(helm_values)
    assert (
        webserver_deployment.spec.template.spec.volumes[1].config_map.name
        == "test-external-workspace"
    )


def test_webserver_workspace_servers(workspace_configmap_template: HelmTemplate):
    helm_values = DagsterHelmValues.construct(
        dagsterWebserver=Webserver.construct(
            workspace=Workspace(
                enabled=True,
                servers=[
                    Server(
                        host="example.com",
                        port=443,
                        name="Example",
                    )
                ],
                externalConfigmap=None,
            )
        ),
    )

    expected = {
        "load_from": [
            {"grpc_server": {"host": "example.com", "port": 443, "location_name": "Example"}}
        ]
    }

    [webserver_workspace_configmap] = workspace_configmap_template.render(helm_values)
    actual = yaml.safe_load(webserver_workspace_configmap.data["workspace.yaml"])

    assert actual == expected


def test_webserver_workspace_servers_ssl(workspace_configmap_template: HelmTemplate):
    helm_values = DagsterHelmValues.construct(
        dagsterWebserver=Webserver.construct(
            workspace=Workspace(
                enabled=True,
                servers=[
                    Server(
                        host="example.com",
                        port=443,
                        name="Example",
                        ssl=True,
                    )
                ],
                externalConfigmap=None,
            )
        ),
    )

    expected = {
        "load_from": [
            {
                "grpc_server": {
                    "host": "example.com",
                    "port": 443,
                    "location_name": "Example",
                    "ssl": True,
                }
            }
        ]
    }

    [webserver_workspace_configmap] = workspace_configmap_template.render(helm_values)
    actual = yaml.safe_load(webserver_workspace_configmap.data["workspace.yaml"])

    assert actual == expected


def test_webserver_scheduler_name_override(deployment_template: HelmTemplate):
    helm_values = DagsterHelmValues.construct(
        dagsterWebserver=Webserver.construct(
            workspace=Workspace(
                enabled=True,
                servers=[],
                externalConfigmap="test-external-workspace",
            ),
            schedulerName="myscheduler",
        ),
    )

    [webserver_deployment] = deployment_template.render(helm_values)
    assert webserver_deployment.spec.template.spec.scheduler_name == "myscheduler"


def test_webserver_security_context(deployment_template: HelmTemplate):
    security_context = {
        "allowPrivilegeEscalation": False,
        "runAsNonRoot": True,
        "runAsUser": 1000,
        "privileged": False,
        "capabilities": {
            "drop": ["ALL"],
        },
        "seccompProfile": {
            "type": "RuntimeDefault",
        },
    }
    helm_values = DagsterHelmValues.construct(
        dagsterWebserver=Webserver.construct(securityContext=security_context)
    )

    [webserver_deployment] = deployment_template.render(helm_values)

    assert len(webserver_deployment.spec.template.spec.init_containers) == 2

    assert all(
        container.security_context
        == k8s_model_from_dict(
            k8s_client.models.V1SecurityContext,
            k8s_snake_case_dict(k8s_client.models.V1SecurityContext, security_context),
        )
        for container in webserver_deployment.spec.template.spec.init_containers
    )


def test_env(deployment_template: HelmTemplate):
    helm_values = DagsterHelmValues.construct(dagsterWebserver=Webserver.construct())
    [daemon_deployment] = deployment_template.render(helm_values)

    assert len(daemon_deployment.spec.template.spec.containers[0].env) == 1

    helm_values = DagsterHelmValues.construct(
        dagsterWebserver=Webserver.construct(
            env=[
                {"name": "TEST_ENV", "value": "test_value"},
            ]
        )
    )
    [daemon_deployment] = deployment_template.render(helm_values)

    assert len(daemon_deployment.spec.template.spec.containers[0].env) == 2
    assert daemon_deployment.spec.template.spec.containers[0].env[1].name == "TEST_ENV"
    assert daemon_deployment.spec.template.spec.containers[0].env[1].value == "test_value"

    # env dict doesn't get written to deployment
    helm_values = DagsterHelmValues.construct(
        dagsterWebserver=Webserver.construct(
            env={"TEST_ENV": "test_value"},
        )
    )
    [daemon_deployment] = deployment_template.render(helm_values)
    assert len(daemon_deployment.spec.template.spec.containers[0].env) == 1


def test_env_configmap(configmap_template):
    # env list doesn't get rendered into configmap
    helm_values = DagsterHelmValues.construct(
        dagsterWebserver=Webserver.construct(
            env=[
                {"name": "TEST_ENV", "value": "test_value"},
                {
                    "name": "TEST_ENV_FROM",
                    "valueFrom": {"fieldRef": {"fieldPath": "metadata.uid", "apiVersion": "v1"}},
                },
            ]
        )
    )
    [cm] = configmap_template.render(helm_values)
    assert len(cm.data) == 5
    assert cm.data["DAGSTER_HOME"] == "/opt/dagster/dagster_home"
    assert "TEST_ENV" not in cm.data

    # env dict gets rendered into configmap
    helm_values = DagsterHelmValues.construct(
        dagsterWebserver=Webserver.construct(
            env={"TEST_ENV": "test_value"},
        )
    )
    [cm] = configmap_template.render(helm_values)
    assert len(cm.data) == 6
    assert cm.data["DAGSTER_HOME"] == "/opt/dagster/dagster_home"
    assert cm.data["TEST_ENV"] == "test_value"
