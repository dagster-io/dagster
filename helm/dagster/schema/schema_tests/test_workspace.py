import subprocess
from typing import List

import pytest
import yaml
from kubernetes.client import models
from schema.charts.dagster.subschema.webserver import Server, Webserver, Workspace
from schema.charts.dagster.values import DagsterHelmValues
from schema.charts.dagster_user_deployments.subschema.user_deployments import UserDeployments
from schema.utils.helm_template import HelmTemplate

from .utils import create_simple_user_deployment


@pytest.fixture(name="template")
def helm_template() -> HelmTemplate:
    return HelmTemplate(
        helm_dir_path="helm/dagster",
        subchart_paths=["charts/dagster-user-deployments"],
        output="templates/configmap-workspace.yaml",
        model=models.V1ConfigMap,
    )


def test_workspace_renders_fail(template: HelmTemplate, capfd):
    helm_values = DagsterHelmValues.construct(
        dagsterUserDeployments=UserDeployments.construct(
            enabled=False,
            enableSubchart=True,
            deployments=[],
        )
    )

    with pytest.raises(subprocess.CalledProcessError):
        template.render(helm_values)

    _, err = capfd.readouterr()
    assert (
        "dagster-user-deployments subchart cannot be enabled if workspace.yaml is not created"
        in err
    )


def test_workspace_does_not_render(template: HelmTemplate, capfd):
    helm_values = DagsterHelmValues.construct(
        dagsterUserDeployments=UserDeployments.construct(
            enabled=False,
            enableSubchart=False,
            deployments=[create_simple_user_deployment("deployment-one")],
        )
    )

    with pytest.raises(subprocess.CalledProcessError):
        template.render(helm_values)

    _, err = capfd.readouterr()
    assert "Error: could not find template" in err


def test_workspace_renders_from_helm_user_deployments(template: HelmTemplate):
    deployments = [
        create_simple_user_deployment("deployment-one"),
        create_simple_user_deployment("deployment-two"),
    ]
    helm_values = DagsterHelmValues.construct(
        dagsterUserDeployments=UserDeployments.construct(
            enabled=True,
            enableSubchart=True,
            deployments=deployments,
        )
    )

    workspace_templates = template.render(helm_values)

    assert len(workspace_templates) == 1

    workspace_template = workspace_templates[0]

    workspace = yaml.full_load(workspace_template.data["workspace.yaml"])
    grpc_servers = workspace["load_from"]

    assert len(grpc_servers) == len(deployments)

    for grpc_server, deployment in zip(grpc_servers, deployments):
        assert grpc_server["grpc_server"]["host"] == deployment.name
        assert grpc_server["grpc_server"]["port"] == deployment.port
        assert grpc_server["grpc_server"]["location_name"] == deployment.name


def test_workspace_renders_from_helm_webserver(template: HelmTemplate):
    servers = [
        Server(host="another-deployment-one", port=4000, name="deployment one"),
        Server(host="another-deployment-two", port=4001, name="deployment two"),
        Server(host="another-deployment-three", port=4002, name="deployment three"),
    ]
    helm_values = DagsterHelmValues.construct(
        dagsterWebserver=Webserver.construct(workspace=Workspace(enabled=True, servers=servers)),
        dagsterUserDeployments=UserDeployments.construct(
            enabled=True,
            enableSubchart=True,
            deployments=[
                create_simple_user_deployment("deployment-one"),
                create_simple_user_deployment("deployment-two"),
            ],
        ),
    )

    workspace_templates = template.render(helm_values)

    assert len(workspace_templates) == 1

    workspace_template = workspace_templates[0]

    workspace = yaml.full_load(workspace_template.data["workspace.yaml"])
    grpc_servers = workspace["load_from"]

    assert len(grpc_servers) == len(servers)

    for grpc_server, server in zip(grpc_servers, servers):
        assert grpc_server["grpc_server"]["host"] == server.host
        assert grpc_server["grpc_server"]["port"] == server.port
        assert grpc_server["grpc_server"]["location_name"] == server.name


def test_workspace_server_location_name_renders_from_helm_webserver(template: HelmTemplate):
    servers = [
        Server(host="another-deployment-one", port=4000),
        Server(host="another-deployment-two", port=4001, name="deployment two"),
    ]
    helm_values = DagsterHelmValues.construct(
        dagsterWebserver=Webserver.construct(workspace=Workspace(enabled=True, servers=servers)),
        dagsterUserDeployments=UserDeployments.construct(
            enabled=True,
            enableSubchart=True,
            deployments=[
                create_simple_user_deployment("deployment-one"),
                create_simple_user_deployment("deployment-two"),
            ],
        ),
    )

    workspace_templates = template.render(helm_values)

    assert len(workspace_templates) == 1

    workspace_template = workspace_templates[0]

    workspace = yaml.full_load(workspace_template.data["workspace.yaml"])
    grpc_servers = workspace["load_from"]

    assert len(grpc_servers) == len(servers)

    for grpc_server, server in zip(grpc_servers, servers):
        assert grpc_server["grpc_server"]["host"] == server.host
        assert grpc_server["grpc_server"]["port"] == server.port

    assert grpc_servers[0]["grpc_server"]["location_name"] == servers[0].host
    assert grpc_servers[1]["grpc_server"]["location_name"] == servers[1].name


def test_workspace_renders_empty(template: HelmTemplate):
    servers: List[Server] = []
    helm_values = DagsterHelmValues.construct(
        dagsterWebserver=Webserver.construct(workspace=Workspace(enabled=True, servers=servers)),
        dagsterUserDeployments=UserDeployments.construct(
            enabled=True,
            enableSubchart=True,
            deployments=[],
        ),
    )

    workspace_templates = template.render(helm_values)

    assert len(workspace_templates) == 1

    workspace_template = workspace_templates[0]

    workspace = yaml.full_load(workspace_template.data["workspace.yaml"])
    grpc_servers = workspace["load_from"]

    assert len(grpc_servers) == len(servers)


def test_workspace_external_configmap_fail(template: HelmTemplate, capfd):
    helm_values = DagsterHelmValues.construct(
        dagsterWebserver=Webserver.construct(
            workspace=Workspace(
                enabled=True,
                servers=[
                    Server(host="another-deployment-one", port=4000),
                ],
                externalConfigmap="test",
            )
        ),
        dagsterUserDeployments=UserDeployments.construct(
            enabled=True,
            enableSubchart=True,
            deployments=[create_simple_user_deployment("deployment-one")],
        ),
    )

    with pytest.raises(subprocess.CalledProcessError):
        template.render(helm_values)

    _, err = capfd.readouterr()
    assert "workspace.servers and workspace.externalConfigmap cannot both be set." in err


def test_workspace_external_configmap_not_present(template: HelmTemplate, capfd):
    helm_values = DagsterHelmValues.construct(
        dagsterWebserver=Webserver.construct(
            workspace=Workspace(
                enabled=True,
                servers=[],
                externalConfigmap="test",
            )
        ),
        dagsterUserDeployments=UserDeployments.construct(
            enabled=True,
            enableSubchart=False,
            deployments=[],
        ),
    )

    with pytest.raises(subprocess.CalledProcessError):
        template.render(helm_values)

    _, err = capfd.readouterr()
    # workspace.yaml isn't rendered if using an externalConfigmap
    assert "Error: could not find template" in err
