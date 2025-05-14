import os
from pathlib import Path
from typing import Optional

import click
from dagster_cloud_cli.types import SnapshotBaseDeploymentCondition
from dagster_shared.plus.config import DagsterPlusCliConfig
from dagster_shared.seven.temp_dir import get_system_temp_directory

from dagster_dg.cli.plus.constants import DgPlusAgentType, DgPlusDeploymentType
from dagster_dg.cli.plus.deploy_session import (
    build_artifact,
    finish_deploy_session,
    init_deploy_session,
)
from dagster_dg.cli.shared_options import (
    dg_editable_dagster_options,
    dg_global_options,
    dg_path_options,
    make_option_group,
)
from dagster_dg.config import DgRawCliConfig, normalize_cli_config
from dagster_dg.context import DgContext
from dagster_dg.utils import DgClickCommand, DgClickGroup, not_none
from dagster_dg.utils.plus.build import get_agent_type
from dagster_dg.utils.telemetry import cli_telemetry_wrapper

DEFAULT_STATEDIR_PATH = os.path.join(get_system_temp_directory(), "dg-build-state")


def _get_statedir():
    return os.getenv("DAGSTER_BUILD_STATEDIR", DEFAULT_STATEDIR_PATH)


def _get_organization(input_organization: Optional[str], plus_config: DagsterPlusCliConfig) -> str:
    organization = input_organization or plus_config.organization
    if not organization:
        raise click.UsageError(
            "Organization not specified. To specify an organization, use the --organization option "
            "or run `dg plus login`."
        )
    return organization


def _get_deployment(input_deployment: Optional[str], plus_config: DagsterPlusCliConfig) -> str:
    deployment = input_deployment or plus_config.default_deployment
    if not deployment:
        raise click.UsageError(
            "Deployment not specified. To specify a deployment, use the --deployment option "
            "or run `dg plus login`."
        )
    return deployment


org_and_deploy_option_group = make_option_group(
    {
        not_none(option.name): option
        for option in [
            click.Option(
                ["--organization"],
                "organization",
                help="Dagster+ organization to which to deploy. If not set, defaults to the value set by `dg plus login`.",
                envvar="DAGSTER_CLOUD_ORGANIZATION",
            ),
            click.Option(
                ["--deployment"],
                "deployment",
                help="Name of the Dagster+ deployment to which to deploy (or use as the base deployment if deploying to a branch deployment). If not set, defaults to the value set by `dg plus login`.",
                envvar="DAGSTER_CLOUD_DEPLOYMENT",
            ),
        ]
    }
)


@click.group(name="deploy", cls=DgClickGroup, invoke_without_command=True)
@org_and_deploy_option_group
@click.option(
    "--python-version",
    "python_version",
    type=click.Choice(["3.9", "3.10", "3.11", "3.12"]),
    help=(
        "Python version used to deploy the project. If not set, defaults to the calling process's Python minor version."
    ),
)
@click.option(
    "--deployment-type",
    "deployment_type_str",
    type=click.Choice([deployment_type.value for deployment_type in DgPlusDeploymentType]),
    help="Whether to deploy to a full deployment or a branch deployment. If unset, will attempt to infer from the current git branch.",
)
@click.option(
    "--agent-type",
    "agent_type_str",
    type=click.Choice([agent_type.value.lower() for agent_type in DgPlusAgentType]),
    help="Whether this a Hybrid or serverless code location.",
    required=False,
)
@click.option(
    "-y",
    "--yes",
    "skip_confirmation_prompt",
    is_flag=True,
    help="Skip confirmation prompts.",
)
@click.option("--git-url", "git_url")
@click.option("--commit-hash", "commit_hash")
@click.option(
    "--location-name",
    "location_names",
    help="Name of the code location to set the build output for. Defaults to the current project's code location, or every project's code location when run in a workspace.",
    required=False,
    multiple=True,
)
@click.option("--status-url", "status_url")
@click.option(
    "--snapshot-base-condition",
    "snapshot_base_condition_str",
    type=click.Choice(
        [
            snapshot_base_condition.value
            for snapshot_base_condition in SnapshotBaseDeploymentCondition
        ]
    ),
)
@dg_editable_dagster_options
@dg_path_options
@dg_global_options
@cli_telemetry_wrapper
def deploy_group(
    organization: Optional[str],
    deployment: Optional[str],
    python_version: Optional[str],
    agent_type_str: str,
    deployment_type_str: Optional[str],
    git_url: Optional[str],
    commit_hash: Optional[str],
    use_editable_dagster: Optional[str],
    skip_confirmation_prompt: bool,
    location_names: tuple[str],
    path: Path,
    status_url: Optional[str],
    snapshot_base_condition_str: Optional[str],
    **global_options: object,
) -> None:
    """Deploy a project or workspace to Dagster Plus. Handles all state management for the deploy
    session, building and pushing a new code artifact for each project.

    To run a full end-to-end deploy, run `dg plus deploy`. This will start a new session, build
    and push the image for the project or workspace, and inform Dagster+ to deploy the newly built
    code.

    Each of the individual stages of the deploy is also available as its own subcommand for additional
    customization.
    """
    if click.get_current_context().invoked_subcommand:
        return

    snapshot_base_condition = (
        SnapshotBaseDeploymentCondition(snapshot_base_condition_str)
        if snapshot_base_condition_str
        else None
    )

    cli_config = normalize_cli_config(global_options, click.get_current_context())
    plus_config = (
        DagsterPlusCliConfig.get() if DagsterPlusCliConfig.exists() else DagsterPlusCliConfig()
    )
    organization = _get_organization(organization, plus_config)
    deployment = _get_deployment(deployment, plus_config)

    dg_context = DgContext.for_workspace_or_project_environment(path, cli_config)
    _validate_location_names(dg_context, location_names, cli_config)

    # TODO Confirm that dagster-cloud is packaged in the project

    statedir = _get_statedir()

    if agent_type_str:
        agent_type = DgPlusAgentType(agent_type_str.upper())
    else:
        agent_type = get_agent_type(plus_config)

    init_deploy_session(
        organization,
        deployment,
        dg_context,
        statedir,
        DgPlusDeploymentType(deployment_type_str) if deployment_type_str else None,
        skip_confirmation_prompt,
        git_url,
        commit_hash,
        location_names,
        status_url,
        snapshot_base_condition,
    )

    build_artifact(
        dg_context,
        agent_type,
        statedir,
        bool(use_editable_dagster),
        python_version,
        location_names,
    )

    finish_deploy_session(dg_context, statedir, location_names)


def _validate_location_names(
    dg_context: DgContext, location_names: tuple[str], cli_config: DgRawCliConfig
):
    if not location_names:
        return

    if dg_context.is_project:
        existing_location_names = {dg_context.code_location_name}
    else:
        existing_location_names = {
            dg_context.for_project_environment(project_spec.path, cli_config).code_location_name
            for project_spec in dg_context.project_specs
        }
    nonexistent_location_names = set(location_names) - existing_location_names
    if nonexistent_location_names:
        raise click.UsageError(
            f"The following requested locations do not exist: {', '.join(nonexistent_location_names)}"
        )


@deploy_group.command(name="start", cls=DgClickCommand)
@org_and_deploy_option_group
@click.option(
    "--deployment-type",
    "deployment_type_str",
    type=click.Choice([deployment_type.value for deployment_type in DgPlusDeploymentType]),
    help="Whether to deploy to a full deployment or a branch deployment. If unset, will attempt to infer from the current git branch.",
)
@click.option(
    "-y",
    "--yes",
    "skip_confirmation_prompt",
    is_flag=True,
    help="Skip confirmation prompts.",
)
@click.option("--git-url", "git_url")
@click.option("--commit-hash", "commit_hash")
@click.option(
    "--location-name",
    "location_names",
    help="Name of the code location to set the build output for. Defaults to the current project's code location, or every project's code location when run in a workspace.",
    required=False,
    multiple=True,
)
@dg_path_options
@click.option("--status-url", "status_url")
@click.option(
    "--snapshot-base-condition",
    "snapshot_base_condition_str",
    type=click.Choice(
        [
            snapshot_base_condition.value
            for snapshot_base_condition in SnapshotBaseDeploymentCondition
        ]
    ),
)
@dg_global_options
@cli_telemetry_wrapper
def start_deploy_session_command(
    organization: Optional[str],
    deployment: Optional[str],
    deployment_type_str: Optional[str],
    skip_confirmation_prompt: bool,
    git_url: Optional[str],
    commit_hash: Optional[str],
    location_names: tuple[str],
    path: Path,
    status_url: Optional[str],
    snapshot_base_condition_str: Optional[str],
    **global_options: object,
) -> None:
    """Start a new deploy session. Determines which code locations will be deployed and what
    deployment is being targeted (creating a new branch deployment if needed), and initializes a
    folder on the filesystem where state about the deploy session will be stored.
    """
    cli_config = normalize_cli_config(global_options, click.get_current_context())
    plus_config = (
        DagsterPlusCliConfig.get() if DagsterPlusCliConfig.exists() else DagsterPlusCliConfig()
    )
    organization = _get_organization(organization, plus_config)
    deployment = _get_deployment(deployment, plus_config)

    dg_context = DgContext.for_workspace_or_project_environment(path, cli_config)
    _validate_location_names(dg_context, location_names, cli_config)
    statedir = _get_statedir()

    snapshot_base_condition = (
        SnapshotBaseDeploymentCondition(snapshot_base_condition_str)
        if snapshot_base_condition_str
        else None
    )

    init_deploy_session(
        organization,
        deployment,
        dg_context,
        statedir,
        DgPlusDeploymentType(deployment_type_str) if deployment_type_str else None,
        skip_confirmation_prompt,
        git_url,
        commit_hash,
        location_names,
        status_url,
        snapshot_base_condition,
    )


@deploy_group.command(name="build-and-push", cls=DgClickCommand)
@click.option(
    "--agent-type",
    "agent_type_str",
    type=click.Choice([agent_type.value.lower() for agent_type in DgPlusAgentType]),
    help="Whether this a Hybrid or serverless code location.",
)
@click.option(
    "--python-version",
    "python_version",
    type=click.Choice(["3.9", "3.10", "3.11", "3.12"]),
    help=(
        "Python version used to deploy the project. If not set, defaults to the calling process's Python minor version."
    ),
)
@click.option(
    "--location-name",
    "location_names",
    help="Name of the code location to set the build output for. Defaults to the current project's code location, or every project's code location when run in a workspace.",
    required=False,
    multiple=True,
)
@dg_editable_dagster_options
@dg_path_options
@dg_global_options
@cli_telemetry_wrapper
def build_and_push_command(
    agent_type_str: str,
    python_version: Optional[str],
    use_editable_dagster: Optional[str],
    location_names: tuple[str],
    path: Path,
    **global_options: object,
) -> None:
    """Builds a Docker image to be deployed, and pushes it to the registry
    that was configured when the deploy session was started.
    """
    cli_config = normalize_cli_config(global_options, click.get_current_context())

    dg_context = DgContext.for_workspace_or_project_environment(path, cli_config)

    _validate_location_names(dg_context, location_names, cli_config)

    if agent_type_str:
        agent_type = DgPlusAgentType(agent_type_str.upper())
    else:
        plus_config = DagsterPlusCliConfig.get()
        agent_type = get_agent_type(plus_config)

    statedir = _get_statedir()

    build_artifact(
        dg_context,
        agent_type,
        statedir,
        bool(use_editable_dagster),
        python_version,
        location_names,
    )


@deploy_group.command(name="set-build-output", cls=DgClickCommand)
@click.option(
    "--image-tag",
    "image_tag",
    help="Tag for the built docker image.",
    required=True,
)
@click.option(
    "--location-name",
    "location_names",
    help="Name of the code location to set the build output for. Defaults to the current project's code location, or every project's code location when run in a workspace.",
    required=False,
    multiple=True,
)
@dg_global_options
@dg_path_options
@cli_telemetry_wrapper
def set_build_output_command(
    image_tag: str, location_names: tuple[str], path: Path, **global_options: object
) -> None:
    """If building a Docker image was built outside of the `dg` CLI, configures the deploy session
    to indicate the correct tag to use when the session is finished.
    """
    from dagster_cloud_cli.commands.ci import set_build_output

    cli_config = normalize_cli_config(global_options, click.get_current_context())

    dg_context = DgContext.for_workspace_or_project_environment(path, cli_config)
    statedir = _get_statedir()
    _validate_location_names(dg_context, location_names, cli_config)

    set_build_output(
        statedir=str(statedir),
        location_name=list(location_names),
        image_tag=image_tag,
    )


@deploy_group.command(name="finish", cls=DgClickCommand)
@click.option(
    "--location-name",
    "location_names",
    help="Name of the code location to set the build output for. Defaults to the current project's code location, or every project's code location when run in a workspace.",
    required=False,
    multiple=True,
)
@dg_global_options
@dg_path_options
@cli_telemetry_wrapper
def finish_deploy_session_command(
    location_names: tuple[str], path: Path, **global_options: object
) -> None:
    """Once all needed images have been built and pushed, completes the deploy session, signaling
    to the Dagster+ API that the deployment can be updated to the newly built and pushed code.
    """
    cli_config = normalize_cli_config(global_options, click.get_current_context())

    dg_context = DgContext.for_workspace_or_project_environment(path, cli_config)
    _validate_location_names(dg_context, location_names, cli_config)
    statedir = _get_statedir()

    finish_deploy_session(dg_context, statedir, location_names)
