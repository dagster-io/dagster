import os
from pathlib import Path
from typing import TYPE_CHECKING

import click
from dagster_cloud_cli import config_utils
from dagster_dg_core.config import DgRawBuildConfig, merge_build_configs
from dagster_dg_core.context import DgContext
from dagster_rest_resources.gql_client import DagsterPlusGraphQLClient
from dagster_shared import check
from dagster_shared.plus.config import DagsterPlusCliConfig

if TYPE_CHECKING:
    from dagster_rest_resources.gql_client import IGraphQLClient

from dagster_dg_cli.cli.plus.constants import DgPlusAgentPlatform, DgPlusAgentType
from dagster_dg_cli.utils.plus.gql import DEPLOYMENT_INFO_QUERY


def get_dockerfile_path(
    project_context: DgContext, workspace_context: DgContext | None = None
) -> Path:
    merged_build_config: DgRawBuildConfig = merge_build_configs(
        workspace_context.build_config if workspace_context else None,
        project_context.build_config,
    )

    if merged_build_config and merged_build_config.get("directory"):
        return Path(check.not_none(merged_build_config["directory"])) / "Dockerfile"
    else:
        return project_context.root_path / "Dockerfile"


def _agent_platform_from_agents(agents: list) -> DgPlusAgentPlatform:
    # Resolve deterministically by priority (K8S first), not by agent order: a mixed v1+v2 org
    # mid-migration runs both a K8s and an ECS agent, and K8S is the signal that drives the
    # Serverless v2 PEX->Docker redirect, so it must win regardless of the order agents appear in.
    running_types: list[str] = []
    for agent in agents:
        if agent["status"] != "RUNNING":
            continue
        for metadata in agent["metadata"]:
            if metadata["key"] != "type":
                continue
            running_types.append(metadata["value"].lower())
            break

    if any("K8sUserCodeLauncher".lower() in t for t in running_types):
        return DgPlusAgentPlatform.K8S
    if any("EcsUserCodeLauncher".lower() in t for t in running_types):
        return DgPlusAgentPlatform.ECS
    if any("DockerUserCodeLauncher".lower() in t for t in running_types):
        return DgPlusAgentPlatform.DOCKER
    if any("ProcessUserCodeLauncher".lower() in t for t in running_types):
        return DgPlusAgentPlatform.LOCAL
    return DgPlusAgentPlatform.UNKNOWN


def get_agent_type_and_platform_from_graphql(
    gql_client: "IGraphQLClient",
) -> tuple[DgPlusAgentType, DgPlusAgentPlatform]:
    result = gql_client.execute_arbitrary(DEPLOYMENT_INFO_QUERY)

    agent_type = DgPlusAgentType(result["currentDeployment"]["agentType"])

    # Serverless is inspected as well as Hybrid: a Serverless v2 org runs the
    # ServerlessK8sUserCodeLauncher, so K8S distinguishes v2 from classic (ECS-backed) Serverless.
    agent_platform = (
        _agent_platform_from_agents(result.get("agents", []))
        if agent_type in (DgPlusAgentType.HYBRID, DgPlusAgentType.SERVERLESS)
        else DgPlusAgentPlatform.UNKNOWN
    )

    return agent_type, agent_platform


def _gql_client_from_env_or_config(
    cli_config: DagsterPlusCliConfig | None,
) -> "IGraphQLClient | None":
    """Build a Plus GraphQL client from the dg config if present, else from the
    ``DAGSTER_CLOUD_*`` env vars used by CI and the deploy commands. Returns None if
    credentials can't be resolved.
    """
    organization = (
        cli_config.organization if cli_config else None
    ) or config_utils.get_organization()
    api_token = (cli_config.user_token if cli_config else None) or config_utils.get_user_token()
    url = config_utils.get_url() or (
        cli_config.organization_url if cli_config and cli_config.organization else None
    )
    deployment = (
        cli_config.default_deployment if cli_config else None
    ) or config_utils.get_deployment()
    if not (organization and api_token and url):
        return None
    return DagsterPlusGraphQLClient(
        url=url, api_token=api_token, organization=organization, deployment=deployment
    )


def get_serverless_agent_platform(cli_config: DagsterPlusCliConfig | None) -> DgPlusAgentPlatform:
    """Resolve the agent platform for a Serverless deployment, sourcing auth from the dg config
    or the ``DAGSTER_CLOUD_*`` env vars (CI/dogfood auth). Only the org-level ``agents`` list is
    read, so this does not depend on a resolvable ``currentDeployment``.
    """
    client = _gql_client_from_env_or_config(cli_config)
    if client is None:
        return DgPlusAgentPlatform.UNKNOWN
    result = client.execute_arbitrary(DEPLOYMENT_INFO_QUERY)
    return _agent_platform_from_agents(result.get("agents", []))


def get_agent_type_and_platform(
    cli_config: DagsterPlusCliConfig | None = None,
) -> tuple[DgPlusAgentType, DgPlusAgentPlatform]:
    gql_client = _gql_client_from_env_or_config(cli_config)
    if gql_client is not None:
        return get_agent_type_and_platform_from_graphql(gql_client)

    prompted = DgPlusAgentType(
        click.prompt(
            "Deployment agent type: ",
            type=click.Choice(
                [agent_type.lower() for agent_type in DgPlusAgentType.__members__.keys()]
            ),
        ).upper()
    )
    return prompted, DgPlusAgentPlatform.UNKNOWN


def get_agent_type(cli_config: DagsterPlusCliConfig | None = None) -> DgPlusAgentType:
    return get_agent_type_and_platform(cli_config)[0]


def create_deploy_dockerfile(
    dst_path: Path, python_version: str, use_editable_dagster: bool, package_name: str
):
    # defer for import performance
    import jinja2

    dockerfile_template_path = (
        Path(__file__).parent.parent.parent
        / "templates"
        / (
            "deploy_uv_editable_Dockerfile.jinja"
            if use_editable_dagster
            else "deploy_uv_Dockerfile.jinja"
        )
    )

    loader = jinja2.FileSystemLoader(searchpath=os.path.dirname(dockerfile_template_path))
    env = jinja2.Environment(loader=loader)

    template = env.get_template(os.path.basename(dockerfile_template_path))

    with open(dst_path, "w", encoding="utf8") as f:
        f.write(template.render(python_version=python_version, package_arg=package_name))
        f.write("\n")
