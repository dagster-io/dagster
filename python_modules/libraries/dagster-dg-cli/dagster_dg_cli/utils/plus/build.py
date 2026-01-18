import os
from pathlib import Path
from typing import Optional

import click
from dagster_dg_core.config import DgRawBuildConfig, merge_build_configs
from dagster_dg_core.context import DgContext
from dagster_shared import check
from dagster_shared.plus.config import DagsterPlusCliConfig

from dagster_dg_cli.cli.plus.constants import DgPlusAgentPlatform, DgPlusAgentType
from dagster_dg_cli.utils.plus.gql import DEPLOYMENT_INFO_QUERY
from dagster_dg_cli.utils.plus.gql_client import DagsterPlusGraphQLClient


def get_dockerfile_path(
    project_context: DgContext, workspace_context: Optional[DgContext] = None
) -> Path:
    merged_build_config: DgRawBuildConfig = merge_build_configs(
        workspace_context.build_config if workspace_context else None,
        project_context.build_config,
    )

    if merged_build_config and merged_build_config.get("directory"):
        return Path(check.not_none(merged_build_config["directory"])) / "Dockerfile"
    else:
        return project_context.root_path / "Dockerfile"


def get_agent_type_and_platform_from_graphql(
    gql_client,
) -> tuple[DgPlusAgentType, DgPlusAgentPlatform]:
    result = gql_client.execute(DEPLOYMENT_INFO_QUERY)

    agent_type = DgPlusAgentType(result["currentDeployment"]["agentType"])

    agent_platform = DgPlusAgentPlatform.UNKNOWN
    if agent_type == DgPlusAgentType.HYBRID:
        for agent in result["agents"]:
            if agent["status"] == "RUNNING":
                for metadata in agent["metadata"]:
                    if metadata["key"] == "type":
                        agent_class = metadata["value"].lower()
                        if "K8sUserCodeLauncher".lower() in agent_class:
                            agent_platform = DgPlusAgentPlatform.K8S
                            break
                        elif "EcsUserCodeLauncher".lower() in agent_class:
                            agent_platform = DgPlusAgentPlatform.ECS
                            break
                        elif "DockerUserCodeLauncher".lower() in agent_class:
                            agent_platform = DgPlusAgentPlatform.DOCKER
                            break
                        elif "ProcessUserCodeLauncher".lower() in agent_class:
                            agent_platform = DgPlusAgentPlatform.LOCAL
                            break

    return agent_type, agent_platform


def get_agent_type(cli_config: Optional[DagsterPlusCliConfig] = None) -> DgPlusAgentType:
    if cli_config:
        gql_client = DagsterPlusGraphQLClient.from_config(cli_config)
        return get_agent_type_and_platform_from_graphql(gql_client)[0]

    else:
        return DgPlusAgentType(
            click.prompt(
                "Deployment agent type: ",
                type=click.Choice(
                    [agent_type.lower() for agent_type in DgPlusAgentType.__members__.keys()]
                ),
            ).upper()
        )


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
