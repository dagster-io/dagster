import os
from pathlib import Path
from typing import Optional

import click
import jinja2
from dagster_shared import check
from dagster_shared.plus.config import DagsterPlusCliConfig

from dagster_dg.cli.plus.constants import DgPlusAgentType
from dagster_dg.config import DgRawBuildConfig, merge_build_configs
from dagster_dg.context import DgContext
from dagster_dg.utils.plus.gql import DEPLOYMENT_INFO_QUERY
from dagster_dg.utils.plus.gql_client import DagsterPlusGraphQLClient


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


def get_agent_type(cli_config: Optional[DagsterPlusCliConfig] = None) -> DgPlusAgentType:
    if cli_config:
        gql_client = DagsterPlusGraphQLClient.from_config(cli_config)
        result = gql_client.execute(DEPLOYMENT_INFO_QUERY)
        return DgPlusAgentType(result["currentDeployment"]["agentType"])
    else:
        return DgPlusAgentType(
            click.prompt(
                "Deployment agent type: ",
                type=click.Choice(
                    [agent_type.lower() for agent_type in DgPlusAgentType.__members__.keys()]
                ),
            ).upper()
        )


def create_deploy_dockerfile(dst_path: Path, python_version: str, use_editable_dagster: bool):
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
        f.write(template.render(python_version=python_version))
        f.write("\n")
