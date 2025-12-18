import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import click

if TYPE_CHECKING:
    from dagster_cloud_cli.types import SnapshotBaseDeploymentCondition

import dagster_shared.check as check

# Expensive imports moved to lazy loading inside functions to improve CLI startup performance
from dagster_dg_core.config import DgRawBuildConfig, merge_build_configs
from dagster_dg_core.context import DgContext
from dagster_dg_core.utils.git import get_local_branch_name

from dagster_dg_cli.cli.plus.constants import DgPlusAgentType, DgPlusDeploymentType
from dagster_dg_cli.cli.utils import create_temp_dagster_cloud_yaml_file
from dagster_dg_cli.utils.plus.build import create_deploy_dockerfile, get_dockerfile_path


def _guess_deployment_type(
    project_dir: Path, full_deployment_name: str
) -> tuple[DgPlusDeploymentType, str]:
    branch_name = get_local_branch_name(str(project_dir))
    if not branch_name:
        click.echo(f"Could not determine a git branch, so deploying to {full_deployment_name}.")
        return DgPlusDeploymentType.FULL_DEPLOYMENT, full_deployment_name

    if branch_name in {"main", "master", "HEAD"}:
        click.echo(f"Current branch is {branch_name}, so deploying to {full_deployment_name}.")
        return DgPlusDeploymentType.FULL_DEPLOYMENT, full_deployment_name

    click.echo(
        f"Deploying to the branch deployment for {branch_name}, with {full_deployment_name} as the base deployment."
    )
    return DgPlusDeploymentType.BRANCH_DEPLOYMENT, branch_name


def _guess_and_prompt_deployment_type(
    project_dir: Path, full_deployment_name: str, skip_confirmation_prompt: bool
) -> DgPlusDeploymentType:
    deployment_type, branch_name = _guess_deployment_type(project_dir, full_deployment_name)

    if not skip_confirmation_prompt and not click.confirm("Do you want to continue?"):
        click.echo("Deployment cancelled.")
        raise click.Abort()

    return deployment_type


def _build_hybrid_image(
    dg_context: DgContext,
    dockerfile_path: Path,
    use_editable_dagster: bool,
    statedir: str,
    build_directory: str,
    merged_build_config: DgRawBuildConfig,
    workspace_context: Optional[DgContext],
) -> None:
    registry = merged_build_config.get("registry")

    if not registry:
        workspace_context_str = (
            f" or {workspace_context.build_config_path}" if workspace_context else ""
        )
        raise click.ClickException(
            f"No build registry found. Please specify a registry key at {dg_context.build_config_path}{workspace_context_str}."
        )

    # TODO use commit hash and deployment from the statedir once that is available here
    tag = f"{dg_context.code_location_name}-{uuid.uuid4().hex}"

    build_cmd = [
        "docker",
        "build",
        str(build_directory),
        "-t",
        f"{registry}:{tag}" if registry else tag,
        "-f",
        str(dockerfile_path),
        "--platform",
        "linux/amd64",
    ]

    if use_editable_dagster:
        build_cmd += [
            "--build-context",
            f"oss={os.environ['DAGSTER_GIT_REPO_DIR']}",
            "--build-context",
            f"internal={os.environ['DAGSTER_INTERNAL_GIT_REPO_DIR']}",
        ]
    click.echo(f"Running: {' '.join(build_cmd)}")
    subprocess.run(build_cmd, check=True)

    push_cmd = [
        "docker",
        "push",
        f"{registry}:{tag}" if registry else tag,
    ]

    subprocess.run(push_cmd, check=True)

    # Lazy import for test mocking and performance
    from dagster_cloud_cli.commands.ci import set_build_output_impl

    set_build_output_impl(
        statedir=str(statedir),
        location_name=[dg_context.code_location_name],
        image_tag=tag,
    )


def init_deploy_session(
    organization: str,
    deployment: str,
    dg_context: DgContext,
    statedir: str,
    input_deployment_type: Optional[DgPlusDeploymentType],
    skip_confirmation_prompt: bool,
    git_url: Optional[str],
    commit_hash: Optional[str],
    location_names: tuple[str],
    status_url: Optional[str],
    snapshot_base_condition: Optional["SnapshotBaseDeploymentCondition"],
):
    deployment_type = (
        input_deployment_type
        if input_deployment_type
        else _guess_and_prompt_deployment_type(
            dg_context.root_path, deployment, skip_confirmation_prompt
        )
    )

    if os.path.exists(statedir):
        shutil.rmtree(statedir, ignore_errors=True)

    if not os.path.isdir(statedir):
        os.makedirs(statedir)

    dagster_cloud_yaml_file = create_temp_dagster_cloud_yaml_file(dg_context, statedir)

    # Lazy import for test mocking and performance
    from dagster_cloud_cli.commands.ci import init_impl

    init_impl(
        statedir=str(statedir),
        dagster_cloud_yaml_path=str(dagster_cloud_yaml_file),
        project_dir=str(dg_context.root_path),
        deployment=deployment,
        organization=organization,
        require_branch_deployment=deployment_type == DgPlusDeploymentType.BRANCH_DEPLOYMENT,
        git_url=git_url,
        commit_hash=commit_hash,
        dagster_env=None,
        status_url=status_url,
        snapshot_base_condition=snapshot_base_condition,
        clean_statedir=False,
        location_name=list(location_names),
    )


def build_artifact(
    dg_context: DgContext,
    agent_type: DgPlusAgentType,
    statedir: str,
    use_editable_dagster: bool,
    python_version: Optional[str],
    location_names: tuple[str],
):
    if not python_version:
        python_version = f"3.{sys.version_info.minor}"

    requested_location_names = set(location_names)

    if dg_context.is_project:
        _build_artifact_for_project(
            dg_context,
            agent_type,
            statedir,
            use_editable_dagster,
            python_version,
            workspace_context=None,
        )
    else:
        for spec in dg_context.project_specs:
            project_root = dg_context.root_path / spec.path
            project_context: DgContext = dg_context.with_root_path(project_root)

            if (
                requested_location_names
                and project_context.code_location_name not in requested_location_names
            ):
                continue

            click.echo(f"Building for location {project_context.code_location_name}.")
            _build_artifact_for_project(
                project_context,
                agent_type,
                statedir,
                use_editable_dagster,
                python_version,
                workspace_context=dg_context,
            )


def _build_artifact_for_project(
    dg_context: DgContext,
    agent_type: DgPlusAgentType,
    statedir: str,
    use_editable_dagster: bool,
    python_version: str,
    workspace_context: Optional[DgContext],
):
    merged_build_config: DgRawBuildConfig = merge_build_configs(
        workspace_context.build_config if workspace_context else None,
        dg_context.build_config,
    )

    build_directory = dg_context.build_root_path
    if merged_build_config.get("directory"):
        build_directory = Path(check.not_none(merged_build_config["directory"]))
        assert build_directory.is_absolute(), "Build directory must be an absolute path"

    dockerfile_path = get_dockerfile_path(dg_context, workspace_context)
    if not os.path.exists(dockerfile_path):
        click.echo(f"No Dockerfile found - scaffolding a default one at {dockerfile_path}.")
        create_deploy_dockerfile(
            dockerfile_path, python_version, use_editable_dagster, dg_context.package_name
        )
    else:
        click.echo(f"Building using Dockerfile at {dockerfile_path}.")

    if agent_type == DgPlusAgentType.HYBRID:
        _build_hybrid_image(
            dg_context,
            dockerfile_path,
            use_editable_dagster,
            statedir,
            str(build_directory),
            merged_build_config,
            workspace_context=workspace_context,
        )

    else:
        # Import BuildStrategy and deps locally since they're not needed for tests
        # Lazy import for test mocking and performance
        from dagster_cloud_cli.commands.ci import BuildStrategy, build_impl
        from dagster_cloud_cli.core.pex_builder import deps

        build_impl(
            statedir=str(statedir),
            dockerfile_path=str(dockerfile_path),
            use_editable_dagster=use_editable_dagster,
            location_name=[dg_context.code_location_name],
            build_directory=str(build_directory),
            build_strategy=BuildStrategy.docker,
            docker_image_tag=None,
            docker_base_image=None,
            docker_env=[],
            python_version=python_version,
            pex_build_method=deps.BuildMethod.LOCAL,
            pex_deps_cache_from=None,
            pex_deps_cache_to=None,
            pex_base_image_tag=None,
        )


def finish_deploy_session(dg_context: DgContext, statedir: str, location_names: tuple[str]):
    # Lazy imports for test mocking and performance
    from dagster_cloud_cli.commands.ci import deploy_impl
    from dagster_cloud_cli.config_utils import (
        get_agent_heartbeat_timeout,
        get_location_load_timeout,
    )

    deploy_impl(
        statedir=str(statedir),
        location_name=list(location_names),
        location_load_timeout=get_location_load_timeout(),
        agent_heartbeat_timeout=get_agent_heartbeat_timeout(default_timeout=None),
    )
