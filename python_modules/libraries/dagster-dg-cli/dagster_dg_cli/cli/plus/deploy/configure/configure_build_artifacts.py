"""Implementation for configuring build artifacts (Dockerfiles, build configs, etc)."""

import textwrap

import click

from dagster_dg_cli.cli.plus.deploy.configure.utils import (
    DeploymentScaffoldConfig,
    get_project_contexts,
    get_scaffolded_container_context_yaml,
)
from dagster_dg_cli.utils.plus.build import create_deploy_dockerfile, get_dockerfile_path


def configure_build_artifacts_impl(config: DeploymentScaffoldConfig) -> None:
    """Core implementation for configuring build artifacts."""
    import yaml

    scaffolded_container_context_yaml = (
        get_scaffolded_container_context_yaml(config.agent_platform)
        if config.agent_platform
        else None
    )

    if not config.dg_context.is_project:
        click.echo("Scaffolding build artifacts for workspace...")

        create = True
        if config.dg_context.build_config_path.exists():
            create = config.skip_confirmation_prompt or click.confirm(
                f"Build config already exists at {config.dg_context.build_config_path}. Overwrite it?",
            )
        if create:
            config.dg_context.build_config_path.write_text(yaml.dump({"registry": "..."}))
            click.echo(f"Workspace build config created at {config.dg_context.build_config_path}.")

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
            project_context.build_config_path.write_text(
                textwrap.dedent(
                    """
                    directory: .
                    # Registry is specified in the build.yaml file at the root of the workspace,
                    # but can be overridden here.
                    # registry: '...'
                    """
                )
                if config.dg_context.is_in_workspace
                else textwrap.dedent(
                    """
                    directory: .
                    registry: '...'
                    """
                )
            )
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
            create_deploy_dockerfile(
                dockerfile_path,
                config.python_version,
                config.use_editable_dagster,
            )
            click.echo(f"Dockerfile created at {dockerfile_path}.")
