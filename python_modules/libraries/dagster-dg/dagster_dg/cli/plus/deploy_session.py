import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Optional

import click
import jinja2

from dagster_dg.cli.plus.constants import DgPlusAgentType, DgPlusDeploymentType
from dagster_dg.cli.utils import create_temp_dagster_cloud_yaml_file
from dagster_dg.context import DgContext
from dagster_dg.utils.git import get_local_branch_name


def _guess_deployment_type(
    project_dir: Path, full_deployment_name: str
) -> tuple[DgPlusDeploymentType, str]:
    branch_name = get_local_branch_name(str(project_dir))
    if not branch_name:
        click.echo(f"Could not determine a git branch, so deploying to {full_deployment_name}.")
        return DgPlusDeploymentType.FULL_DEPLOYMENT, full_deployment_name

    if branch_name in {"main", "master"}:
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


def _create_temp_deploy_dockerfile(dst_path, python_version, use_editable_dagster: bool):
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


def _build_hybrid_image(
    dg_context: DgContext,
    dockerfile_path: Path,
    use_editable_dagster: bool,
    statedir: str,
) -> None:
    if not dg_context.build_config:
        raise click.ClickException(
            f"No build config found. Please specify a registry at {dg_context.build_config_path}."
        )

    registry = dg_context.build_config["registry"]
    source_directory = dg_context.build_config.get("directory", ".")

    # TODO use commit hash and deployment from the statedir once that is available here
    tag = f"{dg_context.code_location_name}-{uuid.uuid4().hex}"

    build_cmd = [
        "docker",
        "build",
        source_directory,
        "-t",
        f"{registry}:{tag}" if registry else tag,
        "-f",
        dockerfile_path,
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

    subprocess.run(build_cmd, check=True)

    push_cmd = [
        "docker",
        "push",
        f"{registry}:{tag}" if registry else tag,
    ]

    subprocess.run(push_cmd, check=True)

    dg_context.external_dagster_cloud_cli_command(
        [
            "ci",
            "set-build-output",
            "--statedir",
            str(statedir),
            "--location-name",
            dg_context.code_location_name,
            "--image-tag",
            tag,
        ]
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
            "--no-clean-statedir",  # we just cleaned it up above
        ]
        + (
            ["--require-branch-deployment"]
            if deployment_type == DgPlusDeploymentType.BRANCH_DEPLOYMENT
            else []
        )
        + (["--git-url", git_url] if git_url else [])
        + (["--commit-hash", commit_hash] if commit_hash else []),
    )


def build_artifact(
    dg_context: DgContext,
    agent_type: DgPlusAgentType,
    statedir: str,
    use_editable_dagster: bool,
    python_version: Optional[str],
):
    if not python_version:
        python_version = f"3.{sys.version_info.minor}"

    dockerfile_path = dg_context.root_path / "Dockerfile"
    if not os.path.exists(dockerfile_path):
        click.echo(f"No Dockerfile found - scaffolding a default one at {dockerfile_path}.")
        _create_temp_deploy_dockerfile(dockerfile_path, python_version, use_editable_dagster)
    else:
        click.echo(f"Building using Dockerfile at {dockerfile_path}.")

    if agent_type == DgPlusAgentType.HYBRID:
        _build_hybrid_image(dg_context, dockerfile_path, use_editable_dagster, statedir)

    else:
        dg_context.external_dagster_cloud_cli_command(
            [
                "ci",
                "build",
                "--statedir",
                str(statedir),
                "--dockerfile-path",
                str(dg_context.root_path / "Dockerfile"),
            ]
            + (["--use-editable-dagster"] if use_editable_dagster else []),
        )


def finish_deploy_session(dg_context: DgContext, statedir: str):
    dg_context.external_dagster_cloud_cli_command(
        [
            "ci",
            "deploy",
            "--statedir",
            str(statedir),
        ],
    )
