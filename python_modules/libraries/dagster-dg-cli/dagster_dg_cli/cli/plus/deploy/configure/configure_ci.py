"""Implementation for scaffolding CI/CD workflows (GitHub Actions, GitLab CI, etc)."""

import textwrap
from typing import cast

import click
from dagster_dg_core.config import merge_build_configs
from dagster_dg_core.utils import exit_with_error

from dagster_dg_cli.cli.plus.constants import DgPlusAgentType
from dagster_dg_cli.cli.plus.deploy.configure.utils import (
    BUILD_LOCATION_FRAGMENT,
    BUILD_LOCATION_FRAGMENT_GITLAB,
    HYBRID_GITHUB_ACTION_FILE,
    HYBRID_GITLAB_CI_FILE,
    REGISTRY_INFOS,
    SERVERLESS_GITHUB_ACTION_FILE,
    SERVERLESS_GITLAB_CI_FILE,
    DgPlusDeployConfigureOptions,
    GitProvider,
    get_cli_version_or_main,
    get_git_web_url,
    get_project_contexts,
)
from dagster_dg_cli.utils.plus.build import get_dockerfile_path


def _get_build_fragment_for_locations(
    config: DgPlusDeployConfigureOptions, registry_urls: list[str]
) -> str:
    """Generate the build fragment for GitHub Actions workflow."""
    if config.git_root is None:
        raise ValueError("Git root is required for generating build fragments")

    project_contexts = get_project_contexts(config.dg_context, config.cli_config)

    # TODO: when we cut over to dg deploy, we'll just use a single build call for the workspace
    # rather than iterating over each project
    output = []
    for location_ctx, registry_url in zip(project_contexts, registry_urls):
        output.append(
            textwrap.indent(BUILD_LOCATION_FRAGMENT.read_text(), " " * 6)
            .replace("TEMPLATE_LOCATION_NAME", location_ctx.code_location_name)
            .replace(
                "TEMPLATE_LOCATION_PATH", str(location_ctx.root_path.relative_to(config.git_root))
            )
            .replace("TEMPLATE_IMAGE_REGISTRY", registry_url)
            .replace("TEMPLATE_DAGSTER_CLOUD_ACTION_VERSION", get_cli_version_or_main())
        )
    return "\n" + "\n".join(output)


def _get_registry_fragment(
    registry_urls: list[str], provider: GitProvider
) -> tuple[str, list[str]]:
    """Generate registry login fragment and secrets hints for the specified git provider."""
    additional_secrets_hints = []
    output = []
    for registry_info in REGISTRY_INFOS:
        fragment_info = registry_info.get_fragment_info(provider)
        fragment = fragment_info.fragment.read_text()
        matching_urls = [url for url in registry_urls if registry_info.match(url)]
        if matching_urls:
            if "TEMPLATE_IMAGE_REGISTRY" not in fragment:
                output.append(fragment)
            else:
                for url in matching_urls:
                    output.append(fragment.replace("TEMPLATE_IMAGE_REGISTRY", url))
            additional_secrets_hints.extend(fragment_info.secrets_hints)

    return "\n".join(output), additional_secrets_hints


def validate_registry_urls(config: DgPlusDeployConfigureOptions) -> list[str]:
    """Validate that registry URLs are configured for all projects."""
    project_contexts = get_project_contexts(config.dg_context, config.cli_config)

    registry_urls = [
        merge_build_configs(project.build_config, config.dg_context.build_config).get("registry")
        for project in project_contexts
    ]

    for project, registry_url in zip(project_contexts, registry_urls):
        if registry_url is None:
            raise click.ClickException(
                f"No registry URL found for project {project.code_location_name}. Please specify a registry URL in `build.yaml`."
            )

    return cast("list[str]", registry_urls)


def validate_dockerfiles_exist(config: DgPlusDeployConfigureOptions) -> None:
    """Validate that Dockerfiles exist for all projects."""
    project_contexts = get_project_contexts(config.dg_context, config.cli_config)

    for location_ctx in project_contexts:
        dockerfile_path = get_dockerfile_path(location_ctx, config.dg_context)
        if not dockerfile_path.exists():
            raise click.ClickException(
                f"Dockerfile not found at {dockerfile_path}. Please run `dg scaffold deployment-config` to create one."
            )


def configure_github_actions_impl(config: DgPlusDeployConfigureOptions) -> None:
    """Core implementation for scaffolding GitHub Actions workflow."""
    import typer

    if config.git_root is None:
        exit_with_error("Git root is required for scaffolding GitHub Actions workflow.")

    workflows_dir = config.git_root / ".github" / "workflows"
    workflows_dir.mkdir(parents=True, exist_ok=True)

    if config.agent_type == DgPlusAgentType.SERVERLESS:
        click.echo("Using serverless workflow template.")
    else:
        click.echo("Using hybrid workflow template.")

    additional_secrets_hints = []

    template = (
        SERVERLESS_GITHUB_ACTION_FILE.read_text()
        if config.agent_type == DgPlusAgentType.SERVERLESS
        else HYBRID_GITHUB_ACTION_FILE.read_text()
    )

    template = (
        template.replace(
            "TEMPLATE_ORGANIZATION_NAME",
            config.organization_name or "",
        )
        .replace(
            "TEMPLATE_DEFAULT_DEPLOYMENT_NAME",
            config.deployment_name,
        )
        .replace(
            "TEMPLATE_PROJECT_DIR",
            str(config.dg_context.root_path.relative_to(config.git_root)),
        )
        .replace(
            "TEMPLATE_DAGSTER_CLOUD_ACTION_VERSION",
            get_cli_version_or_main(),
        )
    )

    # Set ENABLE_FAST_DEPLOYS for serverless deployments
    if config.agent_type == DgPlusAgentType.SERVERLESS:
        enable_fast_deploys_value = "true" if config.pex_deploy else "false"
        template = template.replace(
            "TEMPLATE_ENABLE_FAST_DEPLOYS",
            enable_fast_deploys_value,
        )

    registry_urls = None
    if config.agent_type == DgPlusAgentType.HYBRID:
        # Validate in the correct order: registry URLs first, then Dockerfiles
        registry_urls = validate_registry_urls(config)
        validate_dockerfiles_exist(config)

        build_fragment = _get_build_fragment_for_locations(config, registry_urls)
        template = template.replace("      # TEMPLATE_BUILD_LOCATION_FRAGMENT", build_fragment)

        registry_fragment, additional_secrets_hints = _get_registry_fragment(
            registry_urls, GitProvider.GITHUB
        )
        template = template.replace(
            "# TEMPLATE_CONTAINER_REGISTRY_LOGIN_FRAGMENT",
            textwrap.indent(
                registry_fragment,
                " " * 6,
            ),
        )

    workflow_file = workflows_dir / "dagster-plus-deploy.yml"
    workflow_file.write_text(template)

    git_web_url = get_git_web_url(config.git_root) or ""
    if git_web_url:
        git_web_url = f"({git_web_url}/settings/secrets/actions) "
    click.echo(
        typer.style(
            "\nGitHub Actions workflow created successfully. Commit and push your changes in order to deploy to Dagster Plus.\n",
            fg=typer.colors.GREEN,
        )
        + f"\nYou will need to set up the following secrets in your GitHub repository using\nthe GitHub UI {git_web_url}or CLI (https://cli.github.com/):"
        + typer.style(
            f"\ndg plus create ci-api-token --description 'Used in {config.git_root.name} GitHub Actions' | gh secret set DAGSTER_CLOUD_API_TOKEN"
            + "\n"
            + "\n".join(additional_secrets_hints),
            fg=typer.colors.YELLOW,
        )
    )


def _get_build_fragment_for_locations_gitlab(
    config: DgPlusDeployConfigureOptions, registry_urls: list[str]
) -> str:
    """Generate the build fragment for GitLab CI workflow."""
    if config.git_root is None:
        raise ValueError("Git root is required for generating build fragments")

    project_contexts = get_project_contexts(config.dg_context, config.cli_config)

    output = []
    for location_ctx, registry_url in zip(project_contexts, registry_urls):
        fragment = (
            BUILD_LOCATION_FRAGMENT_GITLAB.read_text()
            .replace("TEMPLATE_LOCATION_NAME", location_ctx.code_location_name)
            .replace(
                "TEMPLATE_LOCATION_PATH", str(location_ctx.root_path.relative_to(config.git_root))
            )
            .replace("TEMPLATE_IMAGE_REGISTRY", registry_url)
        )
        output.append(fragment)
    return "\n".join(output)


def configure_gitlab_ci_impl(config: DgPlusDeployConfigureOptions) -> None:
    """Core implementation for scaffolding GitLab CI workflow."""
    import typer

    if config.git_root is None:
        exit_with_error("Git root is required for scaffolding GitLab CI workflow.")

    # GitLab CI config goes at the root, not in a subdirectory
    gitlab_ci_file = config.git_root / ".gitlab-ci.yml"

    if config.agent_type == DgPlusAgentType.SERVERLESS:
        click.echo("Using serverless workflow template.")
    else:
        click.echo("Using hybrid workflow template.")

    additional_secrets_hints = []

    template = (
        SERVERLESS_GITLAB_CI_FILE.read_text()
        if config.agent_type == DgPlusAgentType.SERVERLESS
        else HYBRID_GITLAB_CI_FILE.read_text()
    )

    template = (
        template.replace(
            "TEMPLATE_ORGANIZATION_NAME",
            config.organization_name or "",
        )
        .replace(
            "TEMPLATE_DEFAULT_DEPLOYMENT_NAME",
            config.deployment_name,
        )
        .replace(
            "TEMPLATE_PROJECT_DIR",
            str(config.dg_context.root_path.relative_to(config.git_root)),
        )
    )

    # Set ENABLE_FAST_DEPLOYS for serverless deployments
    if config.agent_type == DgPlusAgentType.SERVERLESS:
        enable_fast_deploys_value = "true" if config.pex_deploy else "false"
        template = template.replace(
            "TEMPLATE_ENABLE_FAST_DEPLOYS",
            enable_fast_deploys_value,
        )

    registry_urls = None
    if config.agent_type == DgPlusAgentType.HYBRID:
        # Validate in the correct order: registry URLs first, then Dockerfiles
        registry_urls = validate_registry_urls(config)
        validate_dockerfiles_exist(config)

        registry_fragment, additional_secrets_hints = _get_registry_fragment(
            registry_urls, GitProvider.GITLAB
        )
        build_fragment = _get_build_fragment_for_locations_gitlab(config, registry_urls)

        template = template.replace(
            "# TEMPLATE_CONTAINER_REGISTRY_LOGIN_FRAGMENT", registry_fragment
        )
        template = template.replace("    # TEMPLATE_BUILD_LOCATION_FRAGMENT", build_fragment)

    gitlab_ci_file.write_text(template)

    git_web_url = get_git_web_url(config.git_root) or ""
    if git_web_url:
        git_web_url = f"({git_web_url}/-/settings/ci_cd) "
    click.echo(
        typer.style(
            "\nGitLab CI workflow created successfully. Commit and push your changes in order to deploy to Dagster Plus.\n",
            fg=typer.colors.GREEN,
        )
        + f"\nYou will need to set up the following CI/CD variables in your GitLab project using\nthe GitLab UI {git_web_url}or CLI (https://docs.gitlab.com/ee/ci/variables/):"
        + typer.style(
            "\nDAGSTER_CLOUD_API_TOKEN - Run: dg plus create ci-api-token --description 'Used in GitLab CI'"
            + "\n"
            + "\n".join(additional_secrets_hints),
            fg=typer.colors.YELLOW,
        )
    )


def configure_ci_impl(config: DgPlusDeployConfigureOptions) -> None:
    """Scaffold CI/CD workflow based on git provider."""
    if config.git_provider == GitProvider.GITHUB:
        configure_github_actions_impl(config)
    elif config.git_provider == GitProvider.GITLAB:
        configure_gitlab_ci_impl(config)
    elif config.git_provider is None:
        # No CI/CD scaffolding requested
        pass
    else:
        raise ValueError(f"Unsupported git provider: {config.git_provider}")
