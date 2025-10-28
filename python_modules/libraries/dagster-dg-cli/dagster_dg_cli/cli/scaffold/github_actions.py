import subprocess
import textwrap
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
    CONTAINER_REGISTRIES,
    TEMPLATES_DIR,
    get_secrets_hints_for_urls,
)
from dagster_dg_cli.cli.scaffold.utils import (
    apply_template_replacements,
    gather_ci_config,
    get_cli_version_or_main,
    validate_hybrid_build_config,
)


def _get_git_web_url(git_root: Path) -> Optional[str]:
    """Get GitHub web URL for the repository."""
    from dagster_cloud_cli.core.pex_builder.code_location import get_local_repo_name

    try:
        local_repo_name = get_local_repo_name(str(git_root))
        return f"https://github.com/{local_repo_name}"
    except subprocess.CalledProcessError:
        return None


# Template file paths
SERVERLESS_GITHUB_ACTION_FILE = TEMPLATES_DIR / "serverless-github-action.yaml"
HYBRID_GITHUB_ACTION_FILE = TEMPLATES_DIR / "hybrid-github-action.yaml"
BUILD_LOCATION_FRAGMENT = TEMPLATES_DIR / "build-location-fragment.yaml"


def _get_build_fragment_for_locations(
    location_ctxs: list[DgContext], git_root: Path, registry_urls: list[str]
) -> str:
    """Generate GitHub Actions build fragment for locations."""
    # TODO: when we cut over to dg deploy, we'll just use a single build call for the workspace
    # rather than iterating over each project
    output = []
    for location_ctx, registry_url in zip(location_ctxs, registry_urls):
        output.append(
            textwrap.indent(BUILD_LOCATION_FRAGMENT.read_text(), " " * 6)
            .replace("TEMPLATE_LOCATION_NAME", location_ctx.code_location_name)
            .replace("TEMPLATE_LOCATION_PATH", str(location_ctx.root_path.relative_to(git_root)))
            .replace("TEMPLATE_IMAGE_REGISTRY", registry_url)
            .replace("TEMPLATE_DAGSTER_CLOUD_ACTION_VERSION", get_cli_version_or_main())
        )
    return "\n" + "\n".join(output)


def _get_registry_fragment(registry_urls: list[str]) -> str:
    """Generate GitHub Actions registry login fragment."""
    output = []
    for registry in CONTAINER_REGISTRIES:
        if registry.github_fragment is None:
            continue
        fragment = registry.github_fragment.read_text()
        matching_urls = [url for url in registry_urls if registry.match(url)]
        if matching_urls:
            if "TEMPLATE_IMAGE_REGISTRY" not in fragment:
                output.append(fragment)
            else:
                for url in matching_urls:
                    output.append(fragment.replace("TEMPLATE_IMAGE_REGISTRY", url))

    return "\n".join(output)


@click.command(
    name="github-actions",
    cls=DgClickCommand,
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.option("--git-root", type=Path, help="Path to the git root of the repository")
@dg_global_options
@cli_telemetry_wrapper
def scaffold_github_actions_command(git_root: Optional[Path], **global_options: object) -> None:
    """Scaffold a GitHub Actions workflow for a Dagster project.

    This command will create a GitHub Actions workflow in the `.github/workflows` directory.
    """
    import typer

    # Gather common configuration
    config = gather_ci_config(git_root, global_options, click.get_current_context())

    workflows_dir = config.git_root / ".github" / "workflows"
    workflows_dir.mkdir(parents=True, exist_ok=True)

    # Load and process template
    template = (
        SERVERLESS_GITHUB_ACTION_FILE.read_text()
        if config.agent_type == DgPlusAgentType.SERVERLESS
        else HYBRID_GITHUB_ACTION_FILE.read_text()
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
        template = template.replace("      # TEMPLATE_BUILD_LOCATION_FRAGMENT", build_fragment)

        registry_fragment = _get_registry_fragment(registry_urls)
        template = template.replace(
            "# TEMPLATE_CONTAINER_REGISTRY_LOGIN_FRAGMENT",
            textwrap.indent(
                registry_fragment,
                " " * 6,
            ),
        )

        additional_secrets_hints = get_secrets_hints_for_urls(registry_urls, "github")

    workflow_file = workflows_dir / "dagster-plus-deploy.yml"
    workflow_file.write_text(template)

    git_web_url = _get_git_web_url(config.git_root) or ""
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
