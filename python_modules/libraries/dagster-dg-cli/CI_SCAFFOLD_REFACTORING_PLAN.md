# CI Scaffolding Refactoring Plan

## Executive Summary

The `github_actions.py` and `gitlab_ci.py` files have ~53% code duplication (150+ lines). This refactoring consolidates common logic into shared modules while preserving platform-specific behavior.

## Duplication Analysis

### Exact Duplicates (Can be extracted immediately)

1. **Utility Functions** (~20 lines total)
   - `get_cli_version_or_main()` - Version string generation
   - `search_for_git_root()` - Recursive git root search
   - `_get_project_contexts()` - Get project contexts from workspace

2. **Data Structures** (~5 lines)
   - `ContainerRegistryInfo` NamedTuple definition

3. **Command Setup Logic** (~50 lines)
   ```python
   # Git root detection
   git_root = git_root or search_for_git_root(Path.cwd())
   if git_root is None: exit_with_error(...)

   # Context loading
   cli_config = normalize_cli_config(...)
   dg_context = DgContext.for_workspace_or_project_environment(...)
   plus_config = DagsterPlusCliConfig.get() if ...

   # Organization/deployment prompting
   if plus_config and plus_config.organization: ...
   else: organization_name = click.prompt(...)

   if plus_config and plus_config.default_deployment: ...
   else: deployment_name = click.prompt(...)

   # Agent type detection
   agent_type = get_agent_type(plus_config)
   ```

4. **Hybrid Validation Logic** (~35 lines)
   ```python
   if agent_type == DgPlusAgentType.HYBRID:
       project_contexts = _get_project_contexts(...)

       # Extract and validate registry URLs
       registry_urls = [merge_build_configs(...).get("registry") ...]
       for project, registry_url in zip(...):
           if registry_url is None: raise click.ClickException(...)

       # Validate Dockerfiles exist
       for location_ctx in project_contexts:
           dockerfile_path = get_dockerfile_path(...)
           if not dockerfile_path.exists(): raise click.ClickException(...)
   ```

5. **Template Replacement Logic** (~10 lines)
   ```python
   template = template.replace("TEMPLATE_ORGANIZATION_NAME", organization_name)
       .replace("TEMPLATE_DEFAULT_DEPLOYMENT_NAME", deployment_name)
       .replace("TEMPLATE_PROJECT_DIR", str(...))
       .replace("TEMPLATE_DAGSTER_CLOUD_ACTION_VERSION", get_cli_version_or_main())
   ```

### Similar but Different (Need abstraction)

1. **`_get_git_web_url()`**
   - GitHub: Uses `dagster_cloud_cli.core.pex_builder.code_location.get_local_repo_name`
   - GitLab: Manual parsing of `git remote get-url origin`
   - **Recommendation**: Create unified function that detects Git provider

2. **Registry Configuration**
   - Same registries: ECR, DockerHub, GCR, Azure CR
   - Different paths: `registry_fragments/` vs `gitlab_registry_fragments/`
   - Different secrets hint formats:
     - GitHub: `'gh secret set KEY --body "value"'`
     - GitLab: `"KEY - Description"`
   - **Recommendation**: Shared registry definitions with platform-specific formatters

3. **`_get_build_fragment_for_locations()`**
   - GitHub: Global approach with `textwrap.indent()`
   - GitLab: Per-job approach with embedded registry fragments
   - **Recommendation**: Platform-specific implementations, but share registry matching logic

4. **`_get_registry_fragment()`**
   - GitHub: Returns fragment text + secrets hints
   - GitLab: Returns empty string + secrets hints (fragments embedded in jobs)
   - **Recommendation**: Share registry detection logic, different formatters

## Proposed Architecture

```
scaffold/
├── ci_utils.py                 # NEW: Shared utilities
├── registry_config.py          # NEW: Shared registry configuration
├── github_actions.py           # REFACTORED: Platform-specific
└── gitlab_ci.py               # REFACTORED: Platform-specific
```

### 1. `ci_utils.py` - Shared Utilities

```python
"""Shared utilities for CI scaffolding commands."""

from pathlib import Path
from typing import Optional
from dagster_dg_core.config import DgRawCliConfig
from dagster_dg_core.context import DgContext


def get_cli_version_or_main() -> str:
    """Get CLI version string for CI workflows."""
    from dagster_dg_cli.version import __version__ as cli_version
    return "main" if cli_version.endswith("+dev") else f"v{cli_version}"


def search_for_git_root(path: Path) -> Optional[Path]:
    """Recursively search for git repository root."""
    if path.joinpath(".git").exists():
        return path
    elif path.parent == path:
        return None
    else:
        return search_for_git_root(path.parent)


def get_project_contexts(dg_context: DgContext, cli_config: DgRawCliConfig) -> list[DgContext]:
    """Get list of project contexts from workspace or single project."""
    if dg_context.is_in_workspace:
        return [
            dg_context.for_project_environment(project.path, cli_config)
            for project in dg_context.project_specs
        ]
    else:
        return [dg_context]


class CIScaffoldConfig:
    """Configuration gathered for CI scaffolding."""

    def __init__(
        self,
        git_root: Path,
        dg_context: DgContext,
        organization_name: str,
        deployment_name: str,
        agent_type: DgPlusAgentType,
    ):
        self.git_root = git_root
        self.dg_context = dg_context
        self.organization_name = organization_name
        self.deployment_name = deployment_name
        self.agent_type = agent_type


def gather_ci_config(
    git_root: Optional[Path],
    global_options: object,
    click_context,
) -> CIScaffoldConfig:
    """Gather common configuration for CI scaffolding.

    This function handles:
    - Git root detection and validation
    - Config loading (Plus config, CLI config)
    - Organization/deployment prompting
    - Agent type detection
    """
    import click
    from dagster_dg_core.config import normalize_cli_config
    from dagster_dg_core.context import DgContext
    from dagster_dg_core.utils import exit_with_error
    from dagster_shared.plus.config import DagsterPlusCliConfig
    from dagster_dg_cli.cli.plus.constants import DgPlusAgentType
    from dagster_dg_cli.utils.plus.build import get_agent_type

    # Git root detection
    git_root = git_root or search_for_git_root(Path.cwd())
    if git_root is None:
        exit_with_error(
            "No git repository found. CI scaffolding must be run from a git repository, or "
            "specify the path to the git root with `--git-root`."
        )

    # Context loading
    cli_config = normalize_cli_config(global_options, click_context)
    dg_context = DgContext.for_workspace_or_project_environment(Path.cwd(), cli_config)
    plus_config = DagsterPlusCliConfig.get() if DagsterPlusCliConfig.exists() else None

    # Organization name
    if plus_config and plus_config.organization:
        organization_name = plus_config.organization
        click.echo(f"Using organization name {organization_name} from Dagster Plus config.")
    else:
        organization_name = click.prompt("Dagster Plus organization name") or ""

    # Deployment name
    if plus_config and plus_config.default_deployment:
        deployment_name = plus_config.default_deployment
        click.echo(f"Using default deployment name {deployment_name} from Dagster Plus config.")
    else:
        deployment_name = click.prompt("Default deployment name", default="prod")

    # Agent type
    agent_type = get_agent_type(plus_config)
    if agent_type == DgPlusAgentType.SERVERLESS:
        click.echo("Using serverless workflow template.")
    else:
        click.echo("Using hybrid workflow template.")

    return CIScaffoldConfig(
        git_root=git_root,
        dg_context=dg_context,
        organization_name=organization_name,
        deployment_name=deployment_name,
        agent_type=agent_type,
    )


def apply_template_replacements(
    template: str,
    config: CIScaffoldConfig,
) -> str:
    """Apply common template replacements."""
    return (
        template
        .replace("TEMPLATE_ORGANIZATION_NAME", config.organization_name)
        .replace("TEMPLATE_DEFAULT_DEPLOYMENT_NAME", config.deployment_name)
        .replace("TEMPLATE_PROJECT_DIR", str(config.dg_context.root_path.relative_to(config.git_root)))
        .replace("TEMPLATE_DAGSTER_CLOUD_ACTION_VERSION", get_cli_version_or_main())
    )


def validate_hybrid_build_config(
    config: CIScaffoldConfig,
    cli_config: DgRawCliConfig,
) -> tuple[list[DgContext], list[str]]:
    """Validate hybrid deployment build configuration.

    Returns:
        Tuple of (project_contexts, registry_urls)

    Raises:
        click.ClickException: If validation fails
    """
    import click
    from typing import cast
    from dagster_dg_cli.utils.plus.build import get_dockerfile_path, merge_build_configs

    project_contexts = get_project_contexts(config.dg_context, cli_config)

    # Extract and validate registry URLs
    registry_urls = [
        merge_build_configs(project.build_config, config.dg_context.build_config).get("registry")
        for project in project_contexts
    ]
    for project, registry_url in zip(project_contexts, registry_urls):
        if registry_url is None:
            raise click.ClickException(
                f"No registry URL found for project {project.code_location_name}. "
                f"Please specify a registry URL in `build.yaml`."
            )
    registry_urls = cast("list[str]", registry_urls)

    # Validate Dockerfiles exist
    for location_ctx in project_contexts:
        dockerfile_path = get_dockerfile_path(location_ctx, config.dg_context)
        if not dockerfile_path.exists():
            raise click.ClickException(
                f"Dockerfile not found at {dockerfile_path}. "
                f"Please run `dg scaffold build-artifacts` in {location_ctx.root_path} to create one."
            )

    return project_contexts, registry_urls
```

### 2. `registry_config.py` - Shared Registry Configuration

```python
"""Shared container registry configuration for CI scaffolding."""

from pathlib import Path
from typing import Callable, NamedTuple


TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"


class ContainerRegistryInfo(NamedTuple):
    """Information about a container registry."""
    name: str
    match: Callable[[str], bool]
    github_fragment: Path
    gitlab_fragment: Path
    github_secrets: list[str]
    gitlab_secrets: list[str]


# Unified registry configuration
CONTAINER_REGISTRIES = [
    ContainerRegistryInfo(
        name="ECR",
        match=lambda url: "ecr" in url,
        github_fragment=TEMPLATES_DIR / "registry_fragments" / "ecr-login-fragment.yaml",
        gitlab_fragment=TEMPLATES_DIR / "gitlab_registry_fragments" / "ecr-login-fragment.yml",
        github_secrets=[
            'gh secret set AWS_ACCESS_KEY_ID --body "(your AWS access key ID)"',
            'gh secret set AWS_SECRET_ACCESS_KEY --body "(your AWS secret access key)"',
            'gh secret set AWS_REGION --body "(your AWS region)"',
        ],
        gitlab_secrets=[
            "AWS_ACCESS_KEY_ID - Your AWS access key ID",
            "AWS_SECRET_ACCESS_KEY - Your AWS secret access key",
            "AWS_REGION - Your AWS region (e.g., us-east-1)",
        ],
    ),
    ContainerRegistryInfo(
        name="DockerHub",
        match=lambda url: "docker.io" in url,
        github_fragment=TEMPLATES_DIR / "registry_fragments" / "dockerhub-login-fragment.yaml",
        gitlab_fragment=TEMPLATES_DIR / "gitlab_registry_fragments" / "dockerhub-login-fragment.yml",
        github_secrets=[
            'gh secret set DOCKERHUB_USERNAME --body "(your DockerHub username)"',
            'gh secret set DOCKERHUB_TOKEN --body "(your DockerHub token)"',
        ],
        gitlab_secrets=[
            "DOCKERHUB_USERNAME - Your DockerHub username",
            "DOCKERHUB_TOKEN - Your DockerHub access token",
        ],
    ),
    ContainerRegistryInfo(
        name="GitHub Container Registry",
        match=lambda url: "ghcr.io" in url,
        github_fragment=TEMPLATES_DIR / "registry_fragments" / "github-container-registry-login-fragment.yaml",
        gitlab_fragment=None,  # Not used in GitLab
        github_secrets=[],
        gitlab_secrets=[],
    ),
    ContainerRegistryInfo(
        name="GitLab Container Registry",
        match=lambda url: "registry.gitlab.com" in url or "gitlab.com" in url,
        github_fragment=None,  # Not used in GitHub
        gitlab_fragment=TEMPLATES_DIR / "gitlab_registry_fragments" / "gitlab-container-registry-login-fragment.yml",
        github_secrets=[],
        gitlab_secrets=[],
    ),
    ContainerRegistryInfo(
        name="Azure Container Registry",
        match=lambda url: "azurecr.io" in url,
        github_fragment=TEMPLATES_DIR / "registry_fragments" / "azure-container-registry-login-fragment.yaml",
        gitlab_fragment=TEMPLATES_DIR / "gitlab_registry_fragments" / "azure-container-registry-login-fragment.yml",
        github_secrets=[
            'gh secret set AZURE_CLIENT_ID --body "(your Azure client ID)"',
            'gh secret set AZURE_CLIENT_SECRET --body "(your Azure client secret)"',
        ],
        gitlab_secrets=[
            "AZURE_CLIENT_ID - Your Azure client ID",
            "AZURE_CLIENT_SECRET - Your Azure client secret",
            "AZURE_TENANT_ID - Your Azure tenant ID",
        ],
    ),
    ContainerRegistryInfo(
        name="Google Container Registry",
        match=lambda url: "gcr.io" in url,
        github_fragment=TEMPLATES_DIR / "registry_fragments" / "gcr-login-fragment.yaml",
        gitlab_fragment=TEMPLATES_DIR / "gitlab_registry_fragments" / "gcr-login-fragment.yml",
        github_secrets=[
            'gh secret set GCR_JSON_KEY --body "(your GCR JSON key)"',
        ],
        gitlab_secrets=[
            "GCR_JSON_KEY - Your GCR service account JSON key",
        ],
    ),
]


def get_registry_for_url(url: str) -> ContainerRegistryInfo | None:
    """Get registry info for a given URL."""
    for registry in CONTAINER_REGISTRIES:
        if registry.match(url):
            return registry
    return None


def get_secrets_hints_for_urls(registry_urls: list[str], platform: str) -> list[str]:
    """Get secrets hints for a list of registry URLs.

    Args:
        registry_urls: List of container registry URLs
        platform: Either "github" or "gitlab"

    Returns:
        List of secrets hints for the platform
    """
    secrets_hints = []
    seen_registries = set()

    for url in registry_urls:
        registry = get_registry_for_url(url)
        if registry and registry.name not in seen_registries:
            seen_registries.add(registry.name)
            hints = registry.github_secrets if platform == "github" else registry.gitlab_secrets
            secrets_hints.extend(hints)

    return secrets_hints
```

### 3. Refactored `github_actions.py`

```python
"""Scaffold GitHub Actions workflow for Dagster deployment."""

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
from dagster_dg_cli.cli.scaffold.ci_utils import (
    gather_ci_config,
    apply_template_replacements,
    validate_hybrid_build_config,
    get_cli_version_or_main,
)
from dagster_dg_cli.cli.scaffold.registry_config import (
    CONTAINER_REGISTRIES,
    get_registry_for_url,
    get_secrets_hints_for_urls,
    TEMPLATES_DIR,
)


def _get_git_web_url_github(git_root: Path) -> Optional[str]:
    """Get GitHub web URL for the repository."""
    from dagster_cloud_cli.core.pex_builder.code_location import get_local_repo_name

    try:
        local_repo_name = get_local_repo_name(str(git_root))
        return f"https://github.com/{local_repo_name}"
    except subprocess.CalledProcessError:
        return None


def _get_build_fragment_for_locations_github(
    location_ctxs: list[DgContext], git_root: Path, registry_urls: list[str]
) -> str:
    """Generate GitHub Actions build fragment for locations."""
    BUILD_LOCATION_FRAGMENT = TEMPLATES_DIR / "build-location-fragment.yaml"

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


def _get_registry_fragment_github(registry_urls: list[str]) -> str:
    """Generate GitHub Actions registry login fragment."""
    output = []
    for url in registry_urls:
        registry = get_registry_for_url(url)
        if registry and registry.github_fragment:
            fragment = registry.github_fragment.read_text()
            if "TEMPLATE_IMAGE_REGISTRY" not in fragment:
                if fragment not in output:  # Avoid duplicates
                    output.append(fragment)
            else:
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
    """Scaffold a GitHub Actions workflow for a Dagster project."""
    import typer

    # Gather common configuration
    config = gather_ci_config(git_root, global_options, click.get_current_context())

    # Create workflows directory
    workflows_dir = config.git_root / ".github" / "workflows"
    workflows_dir.mkdir(parents=True, exist_ok=True)

    # Load template
    if config.agent_type == DgPlusAgentType.SERVERLESS:
        template_file = TEMPLATES_DIR / "serverless-github-action.yaml"
    else:
        template_file = TEMPLATES_DIR / "hybrid-github-action.yaml"

    template = apply_template_replacements(template_file.read_text(), config)

    # Handle hybrid-specific logic
    additional_secrets_hints = []
    if config.agent_type == DgPlusAgentType.HYBRID:
        cli_config = normalize_cli_config(global_options, click.get_current_context())
        project_contexts, registry_urls = validate_hybrid_build_config(config, cli_config)

        # Generate build fragment
        build_fragment = _get_build_fragment_for_locations_github(
            project_contexts, config.git_root, registry_urls
        )
        template = template.replace("      # TEMPLATE_BUILD_LOCATION_FRAGMENT", build_fragment)

        # Generate registry login fragment
        registry_fragment = _get_registry_fragment_github(registry_urls)
        template = template.replace(
            "# TEMPLATE_CONTAINER_REGISTRY_LOGIN_FRAGMENT",
            textwrap.indent(registry_fragment, " " * 6),
        )

        # Get secrets hints
        additional_secrets_hints = get_secrets_hints_for_urls(registry_urls, "github")

    # Write workflow file
    workflow_file = workflows_dir / "dagster-plus-deploy.yml"
    workflow_file.write_text(template)

    # Display success message
    git_web_url = _get_git_web_url_github(config.git_root) or ""
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
            + ("\n" + "\n".join(additional_secrets_hints) if additional_secrets_hints else ""),
            fg=typer.colors.YELLOW,
        )
    )
```

### 4. Refactored `gitlab_ci.py`

Similar refactoring to GitHub Actions, using shared utilities and registry configuration.

## Benefits

1. **Reduced Duplication**: ~150 lines eliminated
2. **Easier Maintenance**: Single source of truth for common logic
3. **Consistency**: Shared behavior across platforms
4. **Extensibility**: Easy to add new CI platforms (e.g., CircleCI, Jenkins)
5. **Testability**: Common logic can be tested once

## Migration Strategy

1. Create `ci_utils.py` with shared utilities
2. Create `registry_config.py` with unified registry config
3. Refactor `github_actions.py` to use shared code
4. Refactor `gitlab_ci.py` to use shared code
5. Run full test suite to verify no regressions
6. Update any affected tests

## Risks and Mitigation

**Risk**: Breaking existing functionality during refactoring
**Mitigation**:
- Comprehensive test coverage already exists (22 tests)
- Refactor incrementally, testing after each step
- Keep platform-specific logic clearly separated

**Risk**: Making code more complex for minor duplication
**Mitigation**:
- Only extract truly duplicated code
- Keep platform-specific logic in original files
- Balance abstraction vs simplicity

## Timeline Estimate

- Create shared modules: 30 minutes
- Refactor GitHub Actions: 30 minutes
- Refactor GitLab CI: 30 minutes
- Testing and validation: 30 minutes
- **Total**: ~2 hours

## Open Questions

1. Should we create a base class or use functional composition?
   - **Recommendation**: Functional composition (current approach) is simpler

2. Should `_get_git_web_url()` be unified or kept separate?
   - **Recommendation**: Create unified version that detects provider

3. Should we support other CI platforms now?
   - **Recommendation**: Design for extensibility but don't implement yet
