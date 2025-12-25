"""Implementation for configuring build artifacts (Dockerfiles, build configs, etc)."""

from typing import Optional

import click

from dagster_dg_cli.cli.plus.constants import DgPlusAgentType
from dagster_dg_cli.cli.plus.deploy.configure.utils import (
    DgPlusDeployConfigureOptions,
    display_registry_secrets_hints,
    get_project_contexts,
    get_scaffolded_container_context_yaml,
    prompt_for_registry_url,
)
from dagster_dg_cli.utils.plus.build import create_deploy_dockerfile, get_dockerfile_path

# Registry comment block with examples
REGISTRY_COMMENTS = """\
# Container registry URL for pushing Docker images.
# Examples:
#   ECR:       123456789012.dkr.ecr.us-east-1.amazonaws.com/my-repo
#   GCR:       gcr.io/my-project/my-image
#   Azure:     myregistry.azurecr.io/my-image
#   DockerHub: docker.io/myuser/my-image
#   GHCR:      ghcr.io/myorg/my-image
"""

PROJECT_BUILD_YAML_IN_WORKSPACE = """\
directory: .
# Registry is specified in the build.yaml file at the root of the workspace,
# but can be overridden here.
# registry: '...'
"""


def configure_build_artifacts_impl(config: DgPlusDeployConfigureOptions) -> None:
    """Core implementation for configuring build artifacts."""
    # For serverless with PEX deploys, skip scaffolding build artifacts
    if config.agent_type == DgPlusAgentType.SERVERLESS and config.pex_deploy:
        return

    scaffolded_container_context_yaml = (
        get_scaffolded_container_context_yaml(config.agent_platform)
        if config.agent_platform
        else None
    )

    # For hybrid deployments, use provided registry URL or prompt for one
    registry_url: Optional[str] = None
    if config.agent_type == DgPlusAgentType.HYBRID:
        if config.registry_url:
            registry_url = config.registry_url
        else:
            registry_url = prompt_for_registry_url(skip_prompt=config.skip_confirmation_prompt)

    # Use the provided registry URL or fall back to placeholder
    registry_value = registry_url if registry_url else "..."

    if not config.dg_context.is_project:
        click.echo("Scaffolding build artifacts for workspace...")

        create = True
        if config.dg_context.build_config_path.exists():
            create = config.skip_confirmation_prompt or click.confirm(
                f"Build config already exists at {config.dg_context.build_config_path}. Overwrite it?",
            )
        if create:
            build_yaml_content = f"{REGISTRY_COMMENTS}registry: '{registry_value}'\n"
            config.dg_context.build_config_path.write_text(build_yaml_content)
            click.echo(f"Workspace build config created at {config.dg_context.build_config_path}.")
            if registry_url:
                click.echo(f"Registry configured: {registry_url}")

        if scaffolded_container_context_yaml:
            create = True
            if config.dg_context.container_context_config_path.exists():
                create = config.skip_confirmation_prompt or click.confirm(
                    f"Container config already exists at {config.dg_context.container_context_config_path}. Overwrite it?",
                )
            if create:
                config.dg_context.container_context_config_path.write_text(
                    scaffolded_container_context_yaml
                )
                click.echo(
                    f"Workspace container config created at {config.dg_context.container_context_config_path}."
                )

    project_contexts = get_project_contexts(config.dg_context, config.cli_config)
    for project_context in project_contexts:
        click.echo(f"Scaffolding build artifacts for {project_context.code_location_name}...")

        create = True
        if project_context.build_config_path.exists():
            create = config.skip_confirmation_prompt or click.confirm(
                f"Build config already exists at {project_context.build_config_path}. Overwrite it?",
            )
        if create:
            if config.dg_context.is_in_workspace:
                # In a workspace, registry is at workspace level
                project_context.build_config_path.write_text(PROJECT_BUILD_YAML_IN_WORKSPACE)
            else:
                # Standalone project needs its own registry
                project_build_yaml = (
                    f"directory: .\n{REGISTRY_COMMENTS}registry: '{registry_value}'\n"
                )
                project_context.build_config_path.write_text(project_build_yaml)
                if registry_url:
                    click.echo(f"Registry configured: {registry_url}")
            click.echo(f"Project build config created at {project_context.build_config_path}.")

        if scaffolded_container_context_yaml:
            if project_context.container_context_config_path.exists():
                create = config.skip_confirmation_prompt or click.confirm(
                    f"Container config already exists at {project_context.container_context_config_path}. Overwrite it?",
                )
            if create:
                project_context.container_context_config_path.write_text(
                    scaffolded_container_context_yaml
                )
                click.echo(
                    f"Project container config created at {project_context.container_context_config_path}."
                )

        dockerfile_path = get_dockerfile_path(project_context, workspace_context=config.dg_context)
        create = True
        if dockerfile_path.exists():
            create = config.skip_confirmation_prompt or click.confirm(
                f"A Dockerfile already exists at {dockerfile_path}. Overwrite it?",
            )
        if create:
            # python_version should always be resolved, but check for safety
            if config.python_version is None:
                raise click.ClickException(
                    "python_version is required for creating Dockerfiles. "
                    "Please specify --python-version."
                )
            create_deploy_dockerfile(
                dockerfile_path,
                config.python_version,
                config.use_editable_dagster,
                project_context.package_name,
            )
            click.echo(f"Dockerfile created at {dockerfile_path}.")

    # Display secrets hints if registry was configured
    if config.agent_type == DgPlusAgentType.HYBRID and registry_url:
        display_registry_secrets_hints(registry_url, config.git_provider)
