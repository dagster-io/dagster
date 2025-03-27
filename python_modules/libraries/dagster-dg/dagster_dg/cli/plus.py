import os
import sys
import tempfile
import webbrowser
from contextlib import ExitStack
from pathlib import Path
from typing import Optional

import click
import jinja2
from dagster_shared.plus.config import DagsterPlusCliConfig
from dagster_shared.plus.login_server import start_login_server

from dagster_dg.cli.shared_options import dg_global_options
from dagster_dg.cli.utils import create_temp_dagster_cloud_yaml_file
from dagster_dg.config import normalize_cli_config
from dagster_dg.context import DgContext
from dagster_dg.utils import DgClickCommand, DgClickGroup
from dagster_dg.utils.plus.gql import FULL_DEPLOYMENTS_QUERY
from dagster_dg.utils.plus.gql_client import DagsterCloudGraphQLClient
from dagster_dg.utils.telemetry import cli_telemetry_wrapper


@click.group(name="plus", cls=DgClickGroup, hidden=True)
def plus_group():
    """Commands for interacting with Dagster Plus."""


@plus_group.command(name="login", cls=DgClickCommand)
@cli_telemetry_wrapper
def login_command() -> None:
    """Login to Dagster Plus."""
    server, url = start_login_server()

    try:
        webbrowser.open(url, new=0, autoraise=True)
        click.echo(
            f"Opening browser...\nIf a window does not open automatically, visit {url} to"
            " finish authorization"
        )
    except webbrowser.Error as e:
        click.echo(f"Error launching web browser: {e}\n\nTo finish authorization, visit {url}\n")

    server.serve_forever()
    new_org = server.get_organization()
    new_api_token = server.get_token()

    config = DagsterPlusCliConfig(
        organization=new_org,
        user_token=new_api_token,
        url=DagsterPlusCliConfig.get().url if DagsterPlusCliConfig.exists() else None,
    )
    config.write()
    click.echo(f"Authorized for organization {new_org}\n")

    gql_client = DagsterCloudGraphQLClient.from_config(config)
    result = gql_client.execute(FULL_DEPLOYMENTS_QUERY)
    deployment_names = [d["deploymentName"] for d in result["fullDeployments"]]

    click.echo("Available deployments: " + ", ".join(deployment_names))

    selected_deployment = None
    while selected_deployment not in deployment_names:
        if selected_deployment is not None:
            click.echo(f"{selected_deployment} is not a valid deployment")
        selected_deployment = click.prompt(
            "Select a default deployment", default=deployment_names[0]
        )

    config = DagsterPlusCliConfig(
        organization=config.organization,
        user_token=config.user_token,
        default_deployment=selected_deployment,
        url=config.url,
    )
    config.write()


def _create_temp_deploy_dockerfile(dst_path, python_version):
    dockerfile_template_path = os.path.join(
        os.path.dirname(__file__), "..", "templates", "deploy_uv_Dockerfile.jinja"
    )

    loader = jinja2.FileSystemLoader(searchpath=os.path.dirname(dockerfile_template_path))
    env = jinja2.Environment(loader=loader)

    template = env.get_template(os.path.basename(dockerfile_template_path))

    with open(dst_path, "w", encoding="utf8") as f:
        f.write(template.render(python_version=python_version))
        f.write("\n")


@plus_group.command(name="deploy", cls=DgClickCommand)
@click.option(
    "--organization",
    "organization",
    help="Dagster+ organization to which to deploy. If not set, defaults to the value set by `dg plus login`.",
    envvar="DAGSTER_PLUS_ORGANIZATION",
)
@click.option(
    "--deployment",
    "deployment",
    help="Name of the Dagster+ deployment to which to deploy. If not set, defaults to the value set by `dg plus login`.",
    envvar="DAGSTER_PLUS_DEPLOYMENT",
)
@click.option(
    "--python-version",
    "python_version",
    type=click.Choice(["3.9", "3.10", "3.11", "3.12"]),
    help=(
        "Python version used to deploy the project. If not set, defaults to the calling process's Python minor version."
    ),
)
@dg_global_options
def deploy_command(
    organization: Optional[str],
    deployment: Optional[str],
    python_version: Optional[str],
    **global_options: object,
) -> None:
    """Deploy a project to Dagster Plus."""
    cli_config = normalize_cli_config(global_options, click.get_current_context())

    if not python_version:
        python_version = f"3.{sys.version_info.minor}"

    plus_config = DagsterPlusCliConfig.get()

    organization = organization or plus_config.organization
    if not organization:
        raise click.UsageError(
            "Organization not specified. To specify an organization, use the --organization option "
            "or run `dg plus login`."
        )

    deployment = deployment or plus_config.default_deployment
    if not deployment:
        raise click.UsageError(
            "Deployment not specified. To specify a deployment, use the --deployment option "
            "or run `dg plus login`."
        )

    # TODO This command should work in a workspace context too and apply to multiple projects
    dg_context = DgContext.for_project_environment(Path.cwd(), cli_config)

    # TODO Confirm that dagster-cloud is packaged in the project

    with ExitStack() as stack:
        # TODO Once this is split out into multiple commands, we need a default statedir
        # that can be persisted across commands.
        statedir = stack.enter_context(tempfile.TemporaryDirectory())

        # Construct a dagster_cloud.yaml file based on info in the pyproject.toml
        dagster_cloud_yaml_file = stack.enter_context(
            create_temp_dagster_cloud_yaml_file(dg_context)
        )

        dg_context.external_dagster_cloud_cli_command(
            [
                "ci",
                "init",
                "--statedir",
                str(statedir),
                "--dagster-cloud-yaml-path",
                dagster_cloud_yaml_file,
                "--project-dir",
                str(dg_context.root_path),
                "--deployment",
                deployment,
                "--organization",
                organization,
            ],
        )

        dockerfile_path = dg_context.root_path / "Dockerfile"
        if not os.path.exists(dockerfile_path):
            click.echo(f"No Dockerfile found - scaffolding a default one at {dockerfile_path}.")
            _create_temp_deploy_dockerfile(dockerfile_path, python_version)
        else:
            click.echo(f"Building using Dockerfile at {dockerfile_path}.")

        dg_context.external_dagster_cloud_cli_command(
            [
                "ci",
                "build",
                "--statedir",
                str(statedir),
                "--dockerfile-path",
                str(dg_context.root_path / "Dockerfile"),
            ],
        )

        dg_context.external_dagster_cloud_cli_command(
            [
                "ci",
                "deploy",
                "--statedir",
                str(statedir),
            ],
        )
