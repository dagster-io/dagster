import subprocess
from pathlib import Path
from typing import Optional

import click
from dagster_dg_core.config import normalize_cli_config
from dagster_dg_core.context import DgContext
from dagster_dg_core.shared_options import dg_global_options
from dagster_dg_core.utils import DgClickCommand
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper

from dagster_dg_cli.cli.plus.constants import DgPlusAgentType
from dagster_dg_cli.cli.scaffold.registry_config import (
    TEMPLATES_DIR,
    get_registry_for_url,
    get_secrets_hints_for_urls,
)
from dagster_dg_cli.cli.scaffold.utils import (
    apply_template_replacements,
    gather_ci_config,
    validate_hybrid_build_config,
)


def _get_git_web_url(git_root: Path) -> Optional[str]:
    """Get GitLab web URL for the repository."""
    try:
        # Try to get the GitLab remote URL
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=git_root,
            capture_output=True,
            text=True,
            check=True,
        )
        remote_url = result.stdout.strip()

        # Convert SSH URL to HTTPS if needed
        if remote_url.startswith("git@gitlab.com:"):
            remote_url = remote_url.replace("git@gitlab.com:", "https://gitlab.com/")
        if remote_url.endswith(".git"):
            remote_url = remote_url[:-4]

        return remote_url
    except subprocess.CalledProcessError:
        return None


# Template file paths
SERVERLESS_GITLAB_CI_FILE = TEMPLATES_DIR / "serverless-gitlab-ci.yml"
HYBRID_GITLAB_CI_FILE = TEMPLATES_DIR / "hybrid-gitlab-ci.yml"
BUILD_LOCATION_FRAGMENT = TEMPLATES_DIR / "build-location-fragment-gitlab.yml"


def _get_build_fragment_for_locations(
    location_ctxs: list[DgContext], git_root: Path, registry_urls: list[str]
) -> str:
    """Generate GitLab CI build fragment for locations."""
    output = []
    for location_ctx, registry_url in zip(location_ctxs, registry_urls):
        # Get the registry login fragment for this registry
        registry_fragment = ""
        registry = get_registry_for_url(registry_url)
        if registry and registry.gitlab_fragment:
            registry_fragment = registry.gitlab_fragment.read_text()
            if "TEMPLATE_IMAGE_REGISTRY" in registry_fragment:
                registry_fragment = registry_fragment.replace(
                    "TEMPLATE_IMAGE_REGISTRY", registry_url
                )

        # Build the job definition
        job_content = (
            BUILD_LOCATION_FRAGMENT.read_text()
            .replace("TEMPLATE_LOCATION_NAME", location_ctx.code_location_name)
            .replace("TEMPLATE_LOCATION_PATH", str(location_ctx.root_path.relative_to(git_root)))
            .replace("TEMPLATE_IMAGE_REGISTRY", registry_url)
            .replace("    # TEMPLATE_REGISTRY_LOGIN_FRAGMENT", registry_fragment)
        )
        output.append(job_content)
    return "\n".join(output)


@click.command(
    name="gitlab-ci",
    cls=DgClickCommand,
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.option("--git-root", type=Path, help="Path to the git root of the repository")
@dg_global_options
@cli_telemetry_wrapper
def scaffold_gitlab_ci_command(git_root: Optional[Path], **global_options: object) -> None:
    """Scaffold GitLab CI configuration for a Dagster project.

    This command will create a .gitlab-ci.yml file in the repository root.
    """
    import typer

    # Gather common configuration
    config = gather_ci_config(git_root, global_options, click.get_current_context())

    # Load and process template
    template = (
        SERVERLESS_GITLAB_CI_FILE.read_text()
        if config.agent_type == DgPlusAgentType.SERVERLESS
        else HYBRID_GITLAB_CI_FILE.read_text()
    )

    template = apply_template_replacements(template, config)

    # Handle hybrid-specific logic
    additional_secrets_hints = []
    if config.agent_type == DgPlusAgentType.HYBRID:
        cli_config = normalize_cli_config(global_options, click.get_current_context())
        project_contexts, registry_urls = validate_hybrid_build_config(config, cli_config)

        build_fragment = _get_build_fragment_for_locations(
            project_contexts, config.git_root, registry_urls
        )
        template = template.replace("# TEMPLATE_BUILD_LOCATION_FRAGMENT", build_fragment)

        additional_secrets_hints = get_secrets_hints_for_urls(registry_urls, "gitlab")

    gitlab_ci_file = config.git_root / ".gitlab-ci.yml"
    gitlab_ci_file.write_text(template)

    git_web_url = _get_git_web_url(config.git_root) or ""
    if git_web_url:
        git_web_url = f"({git_web_url}/-/settings/ci_cd) "

    click.echo(
        typer.style(
            "\nGitLab CI configuration created successfully. Commit and push your changes to deploy to Dagster Plus.\n",
            fg=typer.colors.GREEN,
        )
        + f"\nYou will need to set up the following CI/CD variables in your GitLab project\n(Settings > CI/CD > Variables) {git_web_url}:"
        + typer.style(
            f"\n\nDAGSTER_CLOUD_API_TOKEN - Create using:\n  dg plus create ci-api-token --description 'Used in {config.git_root.name} GitLab CI'"
            + ("\n\n" + "\n".join(additional_secrets_hints) if additional_secrets_hints else ""),
            fg=typer.colors.YELLOW,
        )
    )
