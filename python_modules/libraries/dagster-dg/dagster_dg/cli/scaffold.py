import subprocess
import sys
import textwrap
from collections.abc import Mapping
from copy import copy
from pathlib import Path
from typing import Any, Callable, NamedTuple, Optional, cast, get_args

import click
import typer
import yaml
from click.core import ParameterSource
from dagster_shared import check
from dagster_shared.plus.config import DagsterPlusCliConfig
from dagster_shared.serdes.objects import PluginObjectKey, PluginObjectSnap
from typer.rich_utils import rich_format_help

from dagster_dg.cli.plus.constants import DgPlusAgentPlatform, DgPlusAgentType
from dagster_dg.cli.shared_options import (
    GLOBAL_OPTIONS,
    dg_editable_dagster_options,
    dg_global_options,
    dg_path_options,
)
from dagster_dg.component import RemotePluginRegistry
from dagster_dg.config import (
    DgProjectPythonEnvironment,
    DgProjectPythonEnvironmentFlag,
    DgRawCliConfig,
    DgRawWorkspaceConfig,
    DgWorkspaceScaffoldProjectOptions,
    get_config_from_cli_context,
    has_config_on_cli_context,
    merge_build_configs,
    normalize_cli_config,
    set_config_on_cli_context,
)
from dagster_dg.context import DgContext
from dagster_dg.scaffold import (
    ScaffoldFormatOptions,
    scaffold_component_type,
    scaffold_library_object,
    scaffold_project,
    scaffold_workspace,
)
from dagster_dg.utils import (
    DgClickCommand,
    DgClickGroup,
    exit_with_error,
    generate_missing_plugin_object_error_message,
    json_schema_property_to_click_option,
    not_none,
    parse_json_option,
    snakecase,
)
from dagster_dg.utils.plus.build import (
    create_deploy_dockerfile,
    get_agent_type,
    get_agent_type_and_platform_from_graphql,
    get_dockerfile_path,
)
from dagster_dg.utils.plus.gql_client import DagsterPlusGraphQLClient
from dagster_dg.utils.telemetry import cli_telemetry_wrapper

DEFAULT_WORKSPACE_NAME = "dagster-workspace"

# These commands are not dynamically generated, but perhaps should be.
HARDCODED_COMMANDS = {"workspace", "project", "component-type"}


# The `dg scaffold` command is special because its subcommands are dynamically generated
# from the registered types in the project. Because the registered component types
# depend on the component modules we are using, we cannot resolve them until we have know these
# component modules, which can be set via the `--use-component-module` option, e.g.
#
#     dg --use-component-module dagster_components.test ...
#
# To handle this, we define a custom click.Group subclass that loads the commands on demand.
class ScaffoldGroup(DgClickGroup):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._commands_defined = False

    def get_command(self, ctx: click.Context, cmd_name: str) -> Optional[click.Command]:
        if not self._commands_defined and cmd_name not in HARDCODED_COMMANDS:
            self._define_commands(ctx)
        cmd = super().get_command(ctx, cmd_name)
        if cmd is None:
            exit_with_error(generate_missing_plugin_object_error_message(cmd_name))
        return cmd

    def list_commands(self, ctx: click.Context) -> list[str]:
        if not self._commands_defined:
            self._define_commands(ctx)
        return super().list_commands(ctx)

    def _define_commands(self, cli_context: click.Context) -> None:
        """Dynamically define a command for each registered component type."""
        if not has_config_on_cli_context(cli_context):
            cli_context.invoke(not_none(self.callback), **cli_context.params)
        config = get_config_from_cli_context(cli_context)
        dg_context = DgContext.for_defined_registry_environment(Path.cwd(), config)

        registry = RemotePluginRegistry.from_dg_context(dg_context)
        for key, component_type in registry.items():
            command = _create_scaffold_subcommand(key, component_type)
            self.add_command(command)

        self._commands_defined = True


class ScaffoldSubCommand(DgClickCommand):
    # We have to override this because the implementation of `format_help` used elsewhere will only
    # pull parameters directly off the target command. For these component scaffold subcommands  we need
    # to expose the global options, which are defined on the preceding group rather than the command
    # itself.
    def format_help(self, context: click.Context, formatter: click.HelpFormatter):
        """Customizes the help to include hierarchical usage."""
        if not isinstance(self, click.Command):
            raise ValueError("This mixin is only intended for use with click.Command instances.")

        # This is a hack. We pass the help format func a modified version of the command where the global
        # options are attached to the command itself. This will cause them to be included in the
        # help output.
        cmd_copy = copy(self)
        cmd_copy.params = [
            *cmd_copy.params,
            *(GLOBAL_OPTIONS.values()),
        ]
        rich_format_help(obj=cmd_copy, ctx=context, markup_mode="rich")

    def format_usage(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        if not isinstance(self, click.Command):
            raise ValueError("This mixin is only intended for use with click.Command instances.")
        arg_pieces = self.collect_usage_pieces(ctx)
        command_parts = ctx.command_path.split(" ")
        command_parts.insert(-1, "[GLOBAL OPTIONS]")
        return formatter.write_usage(" ".join(command_parts), " ".join(arg_pieces))


# We have to override the usual Click processing of `--help` here. The issue is
# that click will process this option before processing anything else, but because we are
# dynamically generating subcommands based on the content of other options, the output of --help
# actually depends on these other options. So we opt out of Click's short-circuiting
# behavior of `--help` by setting `help_option_names=[]`, ensuring that we can process the other
# options first and generate the correct subcommands. We then add a custom `--help` option that
# gets invoked inside the callback.
@click.group(
    name="scaffold",
    cls=ScaffoldGroup,
    invoke_without_command=True,
    context_settings={"help_option_names": []},
)
@click.option("-h", "--help", "help_", is_flag=True, help="Show this message and exit.")
@dg_global_options
@click.pass_context
def scaffold_group(context: click.Context, help_: bool, **global_options: object) -> None:
    """Commands for scaffolding Dagster code."""
    # Click attempts to resolve subcommands BEFORE it invokes this callback.
    # Therefore we need to manually invoke this callback during subcommand generation to make sure
    # it runs first. It will be invoked again later by Click. We make it idempotent to deal with
    # that.
    if not has_config_on_cli_context(context):
        cli_config = normalize_cli_config(global_options, context)
        set_config_on_cli_context(context, cli_config)
    if help_:
        click.echo(context.get_help())
        context.exit(0)


# ########################
# ##### WORKSPACE
# ########################


@scaffold_group.command(
    name="workspace",
    cls=ScaffoldSubCommand,
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.argument("name", type=str, default=DEFAULT_WORKSPACE_NAME)
@dg_editable_dagster_options
@dg_global_options
@cli_telemetry_wrapper
def scaffold_workspace_command(
    name: str,
    use_editable_dagster: Optional[str],
    **global_options: object,
):
    """Initialize a new Dagster workspace.

    The scaffolded workspace folder has the following structure:

    ├── <workspace_name>
    │   ├── projects
    |   |   └── <Dagster projects go here>
    │   └── pyproject.toml

    """
    workspace_config = DgRawWorkspaceConfig(
        scaffold_project_options=DgWorkspaceScaffoldProjectOptions.get_raw_from_cli(
            use_editable_dagster,
        )
    )
    scaffold_workspace(name, workspace_config)


# ########################
# ##### Build artifacts
# ########################


def _get_scaffolded_container_context_yaml(agent_platform: DgPlusAgentPlatform) -> Optional[str]:
    if agent_platform == DgPlusAgentPlatform.K8S:
        return textwrap.dedent(
            """
            ### Uncomment to add configuration for k8s resources.
            # k8s:
            #   server_k8s_config: # Raw kubernetes config for code servers launched by the agent
            #     pod_spec_config: # Config for the code server pod spec
            #       node_selector:
            #         disktype: standard
            #     pod_template_spec_metadata: # Metadata for the code server pod
            #       annotations:
            #         mykey: myvalue
            #     container_config: # Config for the main dagster container in the code server pod
            #       resources:
            #         limits:
            #           cpu: 100m
            #           memory: 128Mi
            #   run_k8s_config: # Raw kubernetes config for runs launched by the agent
            #     pod_spec_config: # Config for the run's PodSpec
            #       node_selector:
            #         disktype: ssd
            #     container_config: # Config for the main dagster container in the run pod
            #       resources:
            #         limits:
            #           cpu: 500m
            #           memory: 1024Mi
            #     pod_template_spec_metadata: # Metadata for the run pod
            #       annotations:
            #         mykey: myvalue
            #     job_spec_config: # Config for the Kubernetes job for the run
            #       ttl_seconds_after_finished: 7200
            """
        )
    elif agent_platform == DgPlusAgentPlatform.ECS:
        return textwrap.dedent(
            """
            ### Uncomment to add configuration for ECS resources.
            # ecs:
            #   env_vars:
            #     - DATABASE_NAME=staging
            #     - DATABASE_PASSWORD
            #   secrets:
            #     - name: 'MY_API_TOKEN'
            #       valueFrom: 'arn:aws:secretsmanager:us-east-1:123456789012:secret:FOO-AbCdEf:token::'
            #     - name: 'MY_PASSWORD'
            #       valueFrom: 'arn:aws:secretsmanager:us-east-1:123456789012:secret:FOO-AbCdEf:password::'
            #   server_resources: # Resources for code servers launched by the agent for this location
            #     cpu: "256"
            #     memory: "512"
            #   run_resources: # Resources for runs launched by the agent for this location
            #     cpu: "4096"
            #     memory: "16384"
            #   execution_role_arn: arn:aws:iam::123456789012:role/MyECSExecutionRole
            #   task_role_arn: arn:aws:iam::123456789012:role/MyECSTaskRole
            #   mount_points:
            #     - sourceVolume: myEfsVolume
            #       containerPath: '/mount/efs'
            #       readOnly: True
            #   volumes:
            #     - name: myEfsVolume
            #       efsVolumeConfiguration:
            #         fileSystemId: fs-1234
            #         rootDirectory: /path/to/my/data
            #   server_sidecar_containers:
            #     - name: DatadogAgent
            #       image: public.ecr.aws/datadog/agent:latest
            #       environment:
            #         - name: ECS_FARGATE
            #           value: true
            #   run_sidecar_containers:
            #     - name: DatadogAgent
            #       image: public.ecr.aws/datadog/agent:latest
            #       environment:
            #         - name: ECS_FARGATE
            #           value: true
            """
        )
    elif agent_platform == DgPlusAgentPlatform.DOCKER:
        return textwrap.dedent(
            """
            ### Uncomment to add configuration for Docker resources.
            # docker:
            #   env_vars:
            #     - DATABASE_NAME=staging
            #     - DATABASE_PASSWORD
            """
        )
    else:
        return None


@scaffold_group.command(
    name="build-artifacts",
    cls=ScaffoldSubCommand,
    context_settings={"help_option_names": ["-h", "--help"]},
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
    "-y",
    "--yes",
    "skip_confirmation_prompt",
    is_flag=True,
    help="Skip confirmation prompts.",
)
@dg_editable_dagster_options
@dg_global_options
@cli_telemetry_wrapper
def scaffold_build_artifacts_command(
    python_version: Optional[str],
    use_editable_dagster: Optional[str],
    skip_confirmation_prompt: bool,
    **global_options: object,
) -> None:
    """Scaffolds a Dockerfile to build the given Dagster project or workspace."""
    cli_config = normalize_cli_config(global_options, click.get_current_context())
    dg_context = DgContext.for_workspace_or_project_environment(Path.cwd(), cli_config)

    plus_config = DagsterPlusCliConfig.get() if DagsterPlusCliConfig.exists() else None

    if plus_config:
        gql_client = DagsterPlusGraphQLClient.from_config(plus_config)
        _, agent_platform = get_agent_type_and_platform_from_graphql(gql_client)
    else:
        agent_platform = DgPlusAgentPlatform.UNKNOWN

    scaffolded_container_context_yaml = _get_scaffolded_container_context_yaml(agent_platform)

    if not dg_context.is_project:
        click.echo("Scaffolding build artifacts for workspace...")

        create = True
        if dg_context.build_config_path.exists():
            create = skip_confirmation_prompt or click.confirm(
                f"Build config already exists at {dg_context.build_config_path}. Overwrite it?",
            )
        if create:
            dg_context.build_config_path.write_text(yaml.dump({"registry": "..."}))
            click.echo(f"Workspace build config created at {dg_context.build_config_path}.")

        if scaffolded_container_context_yaml:
            create = True
            if dg_context.container_context_config_path.exists():
                create = skip_confirmation_prompt or click.confirm(
                    f"Container config already exists at {dg_context.container_context_config_path}. Overwrite it?",
                )
            if create:
                dg_context.container_context_config_path.write_text(
                    scaffolded_container_context_yaml
                )
                click.echo(
                    f"Workspace container config created at {dg_context.container_context_config_path}."
                )

    project_contexts = _get_project_contexts(dg_context, cli_config)
    for project_context in project_contexts:
        click.echo(f"Scaffolding build artifacts for {project_context.code_location_name}...")

        create = True
        if project_context.build_config_path.exists():
            create = skip_confirmation_prompt or click.confirm(
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
                if dg_context.is_workspace
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
                create = skip_confirmation_prompt or click.confirm(
                    f"Container config already exists at {project_context.container_context_config_path}. Overwrite it?",
                )
            if create:
                project_context.container_context_config_path.write_text(
                    scaffolded_container_context_yaml
                )
                click.echo(
                    f"Project container config created at {project_context.container_context_config_path}."
                )

        dockerfile_path = get_dockerfile_path(project_context, workspace_context=dg_context)
        create = True
        if dockerfile_path.exists():
            create = skip_confirmation_prompt or click.confirm(
                f"A Dockerfile already exists at {dockerfile_path}. Overwrite it?",
            )
        if create:
            create_deploy_dockerfile(
                dockerfile_path,
                python_version or f"3.{sys.version_info.minor}",
                bool(use_editable_dagster),
            )
            click.echo(f"Dockerfile created at {dockerfile_path}.")


# ########################
# ##### GITHUB ACTIONS
# ########################


def search_for_git_root(path: Path) -> Optional[Path]:
    if path.joinpath(".git").exists():
        return path
    elif path.parent == path:
        return None
    else:
        return search_for_git_root(path.parent)


SERVERLESS_GITHUB_ACTION_FILE = (
    Path(__file__).parent.parent / "templates" / "serverless-github-action.yaml"
)
HYBRID_GITHUB_ACTION_FILE = Path(__file__).parent.parent / "templates" / "hybrid-github-action.yaml"


BUILD_LOCATION_FRAGMENT = (
    Path(__file__).parent.parent / "templates" / "build-location-fragment.yaml"
)


class ContainerRegistryInfo(NamedTuple):
    name: str
    match: Callable[[str], bool]
    fragment: Path
    secrets_hints: list[str]


REGISTRY_INFOS = [
    ContainerRegistryInfo(
        name="ECR",
        match=lambda url: "ecr" in url,
        fragment=Path(__file__).parent.parent
        / "templates"
        / "registry_fragments"
        / "ecr-login-fragment.yaml",
        secrets_hints=[
            'gh secret set AWS_ACCESS_KEY_ID --body "(your AWS access key ID)"',
            'gh secret set AWS_SECRET_ACCESS_KEY --body "(your AWS secret access key)"',
            'gh secret set AWS_REGION --body "(your AWS region)"',
        ],
    ),
    ContainerRegistryInfo(
        name="DockerHub",
        match=lambda url: "docker.io" in url,
        fragment=Path(__file__).parent.parent
        / "templates"
        / "registry_fragments"
        / "dockerhub-login-fragment.yaml",
        secrets_hints=[
            'gh secret set DOCKERHUB_USERNAME --body "(your DockerHub username)"',
            'gh secret set DOCKERHUB_TOKEN --body "(your DockerHub token)"',
        ],
    ),
    ContainerRegistryInfo(
        name="GitHub Container Registry",
        match=lambda url: "ghcr.io" in url,
        fragment=Path(__file__).parent.parent
        / "templates"
        / "registry_fragments"
        / "github-container-registry-login-fragment.yaml",
        secrets_hints=[],
    ),
    ContainerRegistryInfo(
        name="Azure Container Registry",
        match=lambda url: "azurecr.io" in url,
        fragment=Path(__file__).parent.parent
        / "templates"
        / "registry_fragments"
        / "azure-container-registry-login-fragment.yaml",
        secrets_hints=[
            'gh secret set AZURE_CLIENT_ID --body "(your Azure client ID)"',
            'gh secret set AZURE_CLIENT_SECRET --body "(your Azure client secret)"',
        ],
    ),
    ContainerRegistryInfo(
        name="Google Container Registry",
        match=lambda url: "gcr.io" in url,
        fragment=Path(__file__).parent.parent
        / "templates"
        / "registry_fragments"
        / "gcr-login-fragment.yaml",
        secrets_hints=[
            'gh secret set GCR_JSON_KEY --body "(your GCR JSON key)"',
        ],
    ),
]


def _get_project_contexts(dg_context: DgContext, cli_config: DgRawCliConfig) -> list[DgContext]:
    if dg_context.is_workspace:
        return [
            dg_context.for_project_environment(project.path, cli_config)
            for project in dg_context.project_specs
        ]
    else:
        return [dg_context]


def _get_git_web_url(git_root: Path) -> Optional[str]:
    from dagster_cloud_cli.core.pex_builder.code_location import get_local_repo_name

    try:
        local_repo_name = get_local_repo_name(str(git_root))
        return f"https://github.com/{local_repo_name}"
    except subprocess.CalledProcessError:
        return None


def _get_build_fragment_for_locations(
    location_ctxs: list[DgContext], git_root: Path, registry_urls: list[str]
) -> str:
    # TODO: when we cut over to dg deploy, we'll just use a single build call for the workspace
    # rather than iterating over each project
    output = []
    for location_ctx, registry_url in zip(location_ctxs, registry_urls):
        output.append(
            textwrap.indent(BUILD_LOCATION_FRAGMENT.read_text(), " " * 6)
            .replace("TEMPLATE_LOCATION_NAME", location_ctx.code_location_name)
            .replace("TEMPLATE_LOCATION_PATH", str(location_ctx.root_path.relative_to(git_root)))
            .replace("TEMPLATE_IMAGE_REGISTRY", registry_url)
        )
    return "\n" + "\n".join(output)


def _get_registry_fragment(registry_urls: list[str]) -> tuple[str, list[str]]:
    additional_secrets_hints = []
    output = []
    for registry_info in REGISTRY_INFOS:
        fragment = registry_info.fragment.read_text()
        matching_urls = [url for url in registry_urls if registry_info.match(url)]
        if matching_urls:
            if "TEMPLATE_IMAGE_REGISTRY" not in fragment:
                output.append(fragment)
            else:
                for url in matching_urls:
                    output.append(fragment.replace("TEMPLATE_IMAGE_REGISTRY", url))
            additional_secrets_hints.extend(registry_info.secrets_hints)

    return "\n".join(output), additional_secrets_hints


@scaffold_group.command(
    name="github-actions",
    cls=ScaffoldSubCommand,
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.option("--git-root", type=Path, help="Path to the git root of the repository")
@dg_global_options
@cli_telemetry_wrapper
def scaffold_github_actions_command(git_root: Optional[Path], **global_options: object) -> None:
    """Scaffold a GitHub Actions workflow for a Dagster project.

    This command will create a GitHub Actions workflow in the `.github/workflows` directory.
    """
    git_root = git_root or search_for_git_root(Path.cwd())
    if git_root is None:
        exit_with_error(
            "No git repository found. `dg scaffold github-actions` must be run from a git repository, or "
            "specify the path to the git root with `--git-root`."
        )

    cli_config = normalize_cli_config(global_options, click.get_current_context())
    dg_context = DgContext.for_workspace_or_project_environment(Path.cwd(), cli_config)

    plus_config = DagsterPlusCliConfig.get() if DagsterPlusCliConfig.exists() else None

    workflows_dir = git_root / ".github" / "workflows"
    workflows_dir.mkdir(parents=True, exist_ok=True)

    if plus_config and plus_config.organization:
        organization_name = plus_config.organization
        click.echo(f"Using organization name {organization_name} from Dagster Plus config.")
    else:
        organization_name = click.prompt("Dagster Plus organization name") or ""

    if plus_config and plus_config.default_deployment:
        deployment_name = plus_config.default_deployment
        click.echo(f"Using default deployment name {deployment_name} from Dagster Plus config.")
    else:
        deployment_name = click.prompt("Default deployment name", default="prod")

    agent_type = get_agent_type(plus_config)
    if agent_type == DgPlusAgentType.SERVERLESS:
        click.echo("Using serverless workflow template.")
    else:
        click.echo("Using hybrid workflow template.")

    additional_secrets_hints = []

    template = (
        SERVERLESS_GITHUB_ACTION_FILE.read_text()
        if agent_type == DgPlusAgentType.SERVERLESS
        else HYBRID_GITHUB_ACTION_FILE.read_text()
    )

    template = (
        template.replace(
            "TEMPLATE_ORGANIZATION_NAME",
            organization_name,
        )
        .replace(
            "TEMPLATE_DEFAULT_DEPLOYMENT_NAME",
            deployment_name,
        )
        .replace(
            "TEMPLATE_PROJECT_DIR",
            str(dg_context.root_path.relative_to(git_root)),
        )
    )

    registry_urls = None
    if agent_type == DgPlusAgentType.HYBRID:
        project_contexts = _get_project_contexts(dg_context, cli_config)

        registry_urls = [
            merge_build_configs(project.build_config, dg_context.build_config).get("registry")
            for project in project_contexts
        ]
        for project, registry_url in zip(project_contexts, registry_urls):
            if registry_url is None:
                raise click.ClickException(
                    f"No registry URL found for project {project.code_location_name}. Please specify a registry URL in `build.yaml`."
                )
        registry_urls = cast("list[str]", registry_urls)

        for location_ctx in project_contexts:
            dockerfile_path = get_dockerfile_path(location_ctx, dg_context)
            if not dockerfile_path.exists():
                raise click.ClickException(
                    f"Dockerfile not found at {dockerfile_path}. Please run `dg scaffold build-artifacts` in {location_ctx.root_path} to create one."
                )

        build_fragment = _get_build_fragment_for_locations(
            project_contexts, git_root, registry_urls
        )
        template = template.replace("      # TEMPLATE_BUILD_LOCATION_FRAGMENT", build_fragment)

        registry_fragment, additional_secrets_hints = _get_registry_fragment(registry_urls)
        template = template.replace(
            "# TEMPLATE_CONTAINER_REGISTRY_LOGIN_FRAGMENT",
            textwrap.indent(
                registry_fragment,
                " " * 6,
            ),
        )

    workflow_file = workflows_dir / "dagster-plus-deploy.yml"
    workflow_file.write_text(template)

    git_web_url = _get_git_web_url(git_root) or ""
    if git_web_url:
        git_web_url = f"({git_web_url}/settings/secrets/actions) "
    click.echo(
        typer.style(
            "\nGitHub Actions workflow created successfully. Commit and push your changes in order to deploy to Dagster Plus.\n",
            fg=typer.colors.GREEN,
        )
        + f"\nYou will need to set up the following secrets in your GitHub repository using\nthe GitHub UI {git_web_url}or CLI (https://cli.github.com/):"
        + typer.style(
            f"\ndg plus create ci-api-token --description 'Used in {git_root.name} GitHub Actions' | gh secret set DAGSTER_CLOUD_API_TOKEN"
            + "\n"
            + "\n".join(additional_secrets_hints),
            fg=typer.colors.YELLOW,
        )
    )


# ########################
# ##### PROJECT
# ########################


@scaffold_group.command(
    name="project",
    cls=ScaffoldSubCommand,
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.argument("path", type=Path)
@click.option(
    "--populate-cache/--no-populate-cache",
    is_flag=True,
    default=True,
    help="Whether to automatically populate the component type cache for the project.",
    hidden=True,
)
@click.option(
    "--python-environment",
    default="active",
    type=click.Choice(get_args(DgProjectPythonEnvironmentFlag)),
    help="Type of Python environment in which to launch subprocesses for this project.",
)
@dg_editable_dagster_options
@dg_global_options
@cli_telemetry_wrapper
def scaffold_project_command(
    path: Path,
    populate_cache: bool,
    use_editable_dagster: Optional[str],
    python_environment: DgProjectPythonEnvironmentFlag,
    **global_options: object,
) -> None:
    """Scaffold a Dagster project file structure and a uv-managed virtual environment scoped to
    the project.

    This command can be run inside or outside of a workspace directory. If run inside a workspace,
    the project will be created within the workspace directory's project directory.

    The project file structure defines a Python package with some pre-existing internal structure:

    ├── src
    │   └── <project_name>
    │       ├── __init__.py
    │       ├── definitions.py
    │       ├── defs
    │       │   └── __init__.py
    │       └── lib
    │           └── __init__.py
    ├── tests
    │   └── __init__.py
    └── pyproject.toml

    The `src.<project_name>.defs` directory holds Python objects that can be targeted by the
    `dg scaffold` command or have dg-inspectable metadata. Custom component types in the project
    live in `src.<project_name>.lib`. These types can be created with `dg scaffold component-type`.
    """
    cli_config = normalize_cli_config(global_options, click.get_current_context())
    dg_context = DgContext.from_file_discovery_and_command_line_config(Path.cwd(), cli_config)

    abs_path = path.resolve()
    if dg_context.is_workspace:
        if dg_context.has_project(abs_path.relative_to(dg_context.workspace_root_path)):
            exit_with_error(f"The current workspace already specifies a project at {abs_path}.")
        elif abs_path.exists():
            exit_with_error(f"A file or directory already exists at {abs_path}.")

    scaffold_project(
        abs_path,
        dg_context,
        use_editable_dagster=use_editable_dagster,
        populate_cache=populate_cache,
        python_environment=DgProjectPythonEnvironment.from_flag(python_environment),
    )


def _core_scaffold(
    cli_context: click.Context,
    cli_config: DgRawCliConfig,
    object_key: PluginObjectKey,
    instance_name: str,
    key_value_params,
    json_params,
    scaffold_format: ScaffoldFormatOptions,
) -> None:
    dg_context = DgContext.for_project_environment(Path.cwd(), cli_config)
    registry = RemotePluginRegistry.from_dg_context(dg_context)
    if not registry.has(object_key):
        exit_with_error(f"Scaffoldable object type `{object_key.to_typename()}` not found.")
    elif dg_context.has_component_instance(instance_name):
        exit_with_error(f"A component instance named `{instance_name}` already exists.")

    # Specified key-value params will be passed to this function with their default value of
    # `None` even if the user did not set them. Filter down to just the ones that were set by
    # the user.
    user_provided_key_value_params = {
        k: v
        for k, v in key_value_params.items()
        if cli_context.get_parameter_source(k) == ParameterSource.COMMANDLINE
    }
    if json_params is not None and user_provided_key_value_params:
        exit_with_error(
            "Detected params passed as both --json-params and individual options. These are mutually exclusive means of passing"
            " component generation parameters. Use only one.",
        )
    elif json_params:
        scaffold_params = json_params
    elif user_provided_key_value_params:
        scaffold_params = user_provided_key_value_params
    else:
        scaffold_params = None

    scaffold_library_object(
        Path(dg_context.defs_path) / instance_name,
        object_key.to_typename(),
        scaffold_params,
        dg_context,
        scaffold_format,
    )


def _create_scaffold_subcommand(key: PluginObjectKey, obj: PluginObjectSnap) -> DgClickCommand:
    # We need to "reset" the help option names to the default ones because we inherit the parent
    # value of context settings from the parent group, which has been customized.
    @click.command(
        cls=ScaffoldSubCommand,
        name=key.to_typename(),
        context_settings={"help_option_names": ["-h", "--help"]},
    )
    @click.argument("instance_name", type=str)
    @click.option(
        "--json-params",
        type=str,
        default=None,
        help="JSON string of component parameters.",
        callback=parse_json_option,
    )
    @click.option(
        "--format",
        type=click.Choice(["yaml", "python"], case_sensitive=False),
        default="yaml",
        help="Format of the component configuration (yaml or python)",
    )
    @click.pass_context
    @cli_telemetry_wrapper
    def scaffold_command(
        cli_context: click.Context,
        instance_name: str,
        json_params: Mapping[str, Any],
        format: str,  # noqa: A002 "format" name required for click magic
        **key_value_params: Any,
    ) -> None:
        f"""Scaffold a {key.name} object.

        This command must be run inside a Dagster project directory. The component scaffold will be
        placed in submodule `<project_name>.defs.<INSTANCE_NAME>`.

        Objects can optionally be passed scaffold parameters. There are two ways to do this:

        (1) Passing a single --json-params option with a JSON string of parameters. For example:

            dg scaffold foo.bar my_object --json-params '{{"param1": "value", "param2": "value"}}'`.

        (2) Passing each parameter as an option. For example:

            dg scaffold foo.bar my_object --param1 value1 --param2 value2`

        It is an error to pass both --json-params and key-value pairs as options.
        """
        check.invariant(
            format in ["yaml", "python"],
            "format must be either 'yaml' or 'python'",
        )
        cli_config = get_config_from_cli_context(cli_context)
        _core_scaffold(
            cli_context,
            cli_config,
            key,
            instance_name,
            key_value_params,
            json_params,
            cast("ScaffoldFormatOptions", format),
        )

    # If there are defined scaffold params, add them to the command
    if obj.scaffolder_schema:
        for name, field_info in obj.scaffolder_schema["properties"].items():
            # All fields are currently optional because they can also be passed under
            # `--json-params`
            option = json_schema_property_to_click_option(name, field_info, required=False)
            scaffold_command.params.append(option)

    return scaffold_command


# ########################
# ##### COMPONENT TYPE
# ########################


@scaffold_group.command(
    name="component-type",
    cls=ScaffoldSubCommand,
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.option(
    "--model/--no-model",
    is_flag=True,
    default=True,
    help="Whether to automatically make the generated class inherit from dagster.components.Model.",
)
@click.argument("name", type=str)
@dg_path_options
@dg_global_options
@click.pass_context
@cli_telemetry_wrapper
def scaffold_component_type_command(
    context: click.Context, name: str, model: bool, path: Path, **global_options: object
) -> None:
    """Scaffold of a custom Dagster component type.

    This command must be run inside a Dagster project directory. The component type scaffold
    will be placed in submodule `<project_name>.lib.<name>`.
    """
    cli_config = normalize_cli_config(global_options, context)
    dg_context = DgContext.for_component_library_environment(path, cli_config)
    registry = RemotePluginRegistry.from_dg_context(dg_context)

    module_name = snakecase(name)
    component_key = PluginObjectKey(name=name, namespace=dg_context.default_plugin_module_name)
    if registry.has(component_key):
        exit_with_error(f"Component type`{component_key.to_typename()}` already exists.")

    scaffold_component_type(
        dg_context=dg_context, class_name=name, module_name=module_name, model=model
    )
