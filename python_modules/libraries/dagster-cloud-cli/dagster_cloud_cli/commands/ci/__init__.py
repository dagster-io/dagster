# CI/CD agnostic commands that work with the current CI/CD system
import json
import logging
import os
import pathlib
import shutil
import sys
from collections import Counter
from enum import Enum
from typing import Annotated, Any, Optional, cast

import click
import typer
import yaml
from dagster_shared import check
from dagster_shared.utils import remove_none_recursively
from jinja2 import TemplateSyntaxError
from typer import Typer

from dagster_cloud_cli import docker_utils, gql, pex_utils, ui
from dagster_cloud_cli.commands import metrics
from dagster_cloud_cli.commands.ci import checks, report, state, utils
from dagster_cloud_cli.commands.workspace import wait_for_load
from dagster_cloud_cli.config import DagsterCloudConfigDefaultsMerger, JinjaTemplateLoader
from dagster_cloud_cli.config.models import load_dagster_cloud_yaml
from dagster_cloud_cli.config_utils import (
    DAGSTER_ENV_OPTION,
    LOCATION_LOAD_TIMEOUT_OPTION,
    ORGANIZATION_OPTION,
    URL_ENV_VAR_NAME,
    dagster_cloud_options,
    get_agent_heartbeat_timeout_option,
    get_location_document,
    get_org_url,
    get_user_token,
)
from dagster_cloud_cli.core import pex_builder
from dagster_cloud_cli.core.artifacts import (
    download_organization_artifact,
    upload_organization_artifact,
)
from dagster_cloud_cli.core.pex_builder import (
    code_location,
    deps,
    github_context,
    gitlab_context,
    parse_workspace,
)
from dagster_cloud_cli.gql import DagsterPlusDeploymentAgentType
from dagster_cloud_cli.types import CliEventTags, CliEventType, SnapshotBaseDeploymentCondition
from dagster_cloud_cli.utils import DEFAULT_PYTHON_VERSION

app = Typer(help="Commands for deploying code to Dagster+ from any CI/CD environment")

DEFAULT_SERVERLESS_AGENT_HEARTBEAT_TIMEOUT = 900
DEFAULT_HYBRID_AGENT_HEARTBEAT_TIMEOUT = 120


@app.callback()
def main():
    logging.basicConfig(
        level=logging.getLevelName(os.getenv("DAGSTER_CLOUD_CLI_LOG_LEVEL", "WARNING"))
    )


@app.command(help="Print json information about current CI/CD environment")
def inspect(project_dir: str):
    project_dir = os.path.abspath(project_dir)
    source = metrics.get_source()
    info = {"source": str(source), "project-dir": project_dir}
    if source == CliEventTags.source.github:
        info.update(load_github_info(project_dir))


def load_github_info(project_dir: str) -> dict[str, Any]:
    event = github_context.get_github_event(project_dir)
    return {
        "git-url": event.commit_url,
        "commit-hash": event.github_sha,
    }


@app.command(
    help=(
        "Print the branch deployment name (or nothing) for the current context. Creates a new"
        " branch deployment if necessary. Requires DAGSTER_CLOUD_ORGANIZATION and"
        " DAGSTER_CLOUD_API_TOKEN environment variables."
    )
)
def branch_deployment(
    project_dir: str,
    organization: Optional[str] = ORGANIZATION_OPTION,
    dagster_env: Optional[str] = DAGSTER_ENV_OPTION,
    mark_closed: bool = False,
    read_only: bool = False,
    base_deployment_name: Optional[str] = None,
    snapshot_base_condition: Optional[SnapshotBaseDeploymentCondition] = None,
):
    try:
        if organization:
            url = get_org_url(organization, dagster_env)
        else:
            url = os.environ[URL_ENV_VAR_NAME]

        if read_only:
            print(get_branch_deployment_name_from_context(url, project_dir))  # noqa: T201
            return

        print(  # noqa: T201
            create_or_update_deployment_from_context(
                url,
                project_dir,
                mark_closed,
                base_deployment_name=base_deployment_name,
                snapshot_base_condition=snapshot_base_condition,
                require_branch_deployment=True,
            )
        )
    except ValueError as err:
        ui.error(
            f"cannot determine branch deployment: {err}",
        )
        sys.exit(1)


def create_or_update_deployment_from_context(
    url,
    project_dir: str,
    mark_closed: bool,
    base_deployment_name: Optional[str],
    snapshot_base_condition: Optional[SnapshotBaseDeploymentCondition],
    require_branch_deployment: bool = False,
) -> Optional[str]:
    source = metrics.get_source()
    api_token = check.not_none(get_user_token())
    if source == CliEventTags.source.github:
        event = github_context.get_github_event(project_dir)
        deployment_name = code_location.create_or_update_branch_deployment_from_github_context(
            url,
            api_token,
            event,
            mark_closed,
            base_deployment_name=base_deployment_name,
            snapshot_base_condition=snapshot_base_condition,
        )
        if not deployment_name:
            raise ValueError(
                f"could not determine branch deployment for PR {event.pull_request_id}"
            )

        return deployment_name
    elif source == CliEventTags.source.gitlab:
        event = gitlab_context.get_gitlab_event(project_dir)
        if not event.merge_request_iid:
            raise ValueError("no merge request id")
        with gql.graphql_client_from_url(url, api_token) as client:
            deployment_name = gql.create_or_update_branch_deployment(
                client,
                repo_name=event.project_name,
                branch_name=event.branch_name,
                commit_hash=event.commit_sha,
                timestamp=float(event.git_metadata.timestamp),
                branch_url=event.branch_url,
                pull_request_url=event.merge_request_url,
                pull_request_status=("CLOSED" if mark_closed else "OPEN"),
                pull_request_number=event.merge_request_iid,
                author_name=event.git_metadata.name,
                author_email=event.git_metadata.email,
                commit_message=event.git_metadata.message,
                base_deployment_name=base_deployment_name,
                snapshot_base_condition=snapshot_base_condition,
            )

            return deployment_name

    elif source == CliEventTags.source.cli:
        if require_branch_deployment:
            deployment_name = (
                code_location.create_or_update_branch_deployment_from_local_git_context(
                    url,
                    api_token,
                    project_dir,
                    mark_closed,
                    base_deployment_name=base_deployment_name,
                    snapshot_base_condition=snapshot_base_condition,
                )
            )
            if not deployment_name:
                raise Exception(
                    "Could not determine branch deployment to use from local git context"
                )

            return deployment_name
        else:
            return None
    else:
        raise ValueError(f"unsupported for {source}")


def get_branch_deployment_name_from_context(url, project_dir: str) -> Optional[str]:
    source = metrics.get_source()
    api_token = check.not_none(get_user_token())
    if source == CliEventTags.source.github:
        event = github_context.get_github_event(project_dir)
        if not event.branch_name:
            return None
        with gql.graphql_client_from_url(url, api_token) as client:
            return gql.get_branch_deployment_name(
                client,
                repo_name=event.repo_name,
                branch_name=event.branch_name,
            )
    elif source == CliEventTags.source.gitlab:
        event = gitlab_context.get_gitlab_event(project_dir)
        with gql.graphql_client_from_url(url, api_token) as client:
            return gql.get_branch_deployment_name(
                client,
                repo_name=event.project_name,
                branch_name=event.branch_name,
            )
    elif source == CliEventTags.source.cli:
        branch_name = code_location.get_local_branch_name(project_dir)

        if not branch_name:
            raise Exception("Could not determine branch name from local git context")

        # Extract just the org/repo part from the git URL
        repo_name = code_location.get_local_repo_name(project_dir)

        if not repo_name:
            raise Exception("Could not determine repo name from local git context")

        with gql.graphql_client_from_url(url, api_token) as client:
            return gql.get_branch_deployment_name(
                client,
                repo_name=repo_name,
                branch_name=branch_name,
            )
    else:
        raise ValueError(f"unsupported for {source}")


@app.command(name="check", help="Validate configuration")
def check_command(
    organization: Optional[str] = ORGANIZATION_OPTION,
    dagster_env: Optional[str] = DAGSTER_ENV_OPTION,
    project_dir: str = typer.Option("."),
    dagster_cloud_yaml_path: str = "dagster_cloud.yaml",
    dagster_cloud_yaml_check: checks.Check = typer.Option("error"),
    dagster_cloud_connect_check: checks.Check = typer.Option("error"),
):
    project_path = pathlib.Path(project_dir)

    verdicts = []
    if dagster_cloud_yaml_check != checks.Check.skip:
        yaml_path = project_path / dagster_cloud_yaml_path
        result = checks.check_dagster_cloud_yaml(yaml_path)
        verdicts.append(
            checks.handle_result(
                result,
                dagster_cloud_yaml_check,
                prefix_message="[dagster_cloud.yaml] ",
                success_message="Checked OK",
                failure_message=(
                    "Invalid dagster_cloud.yaml, please see"
                    " https://docs.dagster.io/deployment/code-locations/dagster-cloud-yaml"
                ),
            )
        )

    if dagster_cloud_connect_check != checks.Check.skip:
        if not organization:
            raise ui.error(
                "DAGSTER_CLOUD_ORGANIZATION or --organization required for connection check."
            )
        url = get_org_url(organization, dagster_env)
        result = checks.check_connect_dagster_cloud(url)
        verdicts.append(
            checks.handle_result(
                result,
                dagster_cloud_connect_check,
                prefix_message="[dagster.cloud connection] ",
                success_message="Able to connect to dagster.cloud",
                failure_message="Unable to connect to dagster.cloud",
            )
        )

    verdict_counts = Counter(verdicts)
    ui.print(f"Passed: {verdict_counts[checks.Verdict.passed]}")
    if verdict_counts[checks.Verdict.warning]:
        ui.print(f"Warnings: {verdict_counts[checks.Verdict.warning]}")
    if verdict_counts[checks.Verdict.failed]:
        ui.print(ui.red(f"Failed: {verdict_counts[checks.Verdict.failed]}"))
        sys.exit(1)


STATEDIR_OPTION = typer.Option(..., envvar="DAGSTER_BUILD_STATEDIR")


@app.command(help="Render the processed dagster cloud configuration file to the console")
def template(
    project_dir: str = typer.Option(".", help="Path to the project directory"),
    dagster_cloud_yaml_path: str = typer.Option(
        "dagster_cloud.yaml", help="Path to the dagster cloud configuration file"
    ),
    values_file: Optional[str] = typer.Option(default=None, help="Path to a values file"),
    value: list[str] = typer.Option(
        [],
        help="Key value pairs to override in the yaml file, value can be a str or a valid json representation",
    ),
    merge: bool = typer.Option(
        True,
        help="Render the yaml file with defaults merged in each location",
        is_flag=True,
    ),
) -> None:
    project_path = pathlib.Path(project_dir)
    yaml_path = project_path / dagster_cloud_yaml_path
    if not yaml_path.exists():
        raise ui.error(f"No such file {yaml_path}")

    context = _create_context_from_values(value, values_file)

    template_loader = JinjaTemplateLoader()
    rendered_config_yaml: str
    try:
        rendered_config_yaml = template_loader.render(filepath=str(yaml_path), context=context)
    except TemplateSyntaxError as error:
        raise ui.error(
            f"jinja TemplateSyntaxError: {error.message} at line {error.lineno} in {error.filename}"
        )
    except Exception as error:
        raise ui.error(f"Error rendering template: {error}")

    if not merge:
        ui.print(rendered_config_yaml)
        return

    try:
        dagster_cloud_config = load_dagster_cloud_yaml(rendered_config_yaml)
    except Exception as err:
        raise ui.error(f"Error parsing the configuration: {err}")

    config_merger = DagsterCloudConfigDefaultsMerger()
    processed_config = config_merger.process(dagster_cloud_config)
    config_as_dict = remove_none_recursively(processed_config.model_dump())
    ui.print(yaml.dump(config_as_dict))


def _create_context_from_values(
    values_list: list[str], values_file: Optional[str]
) -> dict[str, Any]:
    """Creates a collection of values by loading values from a file then
    overlaying a value list to extend or override those values.
    """
    context: dict[str, Any] = {}

    # load values from file
    values_file_path = pathlib.Path(values_file) if values_file else None
    if values_file_path:
        try:
            with open(values_file_path) as f:
                if values_file_path.suffix == ".json":
                    context.update(json.load(f))
                elif values_file_path.suffix in [".yaml", ".yml"]:
                    context.update(yaml.safe_load(f))
                else:
                    raise ui.error(f"Unsupported values file extension {values_file_path.suffix}")
        except Exception as err:
            raise ui.error(f"Error parsing values file {values_file}: {err}")

    # overlay command line value arguments
    for value_entry in values_list:
        key, value = value_entry.split("=", 1)
        try:
            # command line values may be expressed as json to allow for complex values
            val = json.loads(value)
        except json.JSONDecodeError:
            val = value

        # command line values may specify a path to set keys in
        key_path = key.split(".") if "." in key else [key]
        sub_context_ref = context
        for step in key_path:
            if step == key_path[-1]:
                sub_context_ref[step] = val
            elif step not in sub_context_ref:
                sub_context_ref[step] = {}
            sub_context_ref = sub_context_ref[step]
    return context


@app.command(help="Initialize a build session")
@dagster_cloud_options(allow_empty=False, allow_empty_deployment=True, requires_url=False)
def init(
    organization: str,
    deployment: Optional[str],
    dagster_env: Optional[str] = DAGSTER_ENV_OPTION,
    project_dir: str = typer.Option("."),
    dagster_cloud_yaml_path: str = "dagster_cloud.yaml",
    statedir: str = STATEDIR_OPTION,
    clean_statedir: bool = typer.Option(True, help="Delete any existing files in statedir"),
    location_name: list[str] = typer.Option([]),
    git_url: Optional[str] = None,
    commit_hash: Optional[str] = None,
    status_url: Optional[str] = None,
    snapshot_base_condition: Optional[SnapshotBaseDeploymentCondition] = None,
    require_branch_deployment: bool = typer.Option(
        None, help="Whether to require that a branch deployment be created"
    ),
):
    init_impl(
        organization,
        deployment,
        dagster_env,
        project_dir,
        dagster_cloud_yaml_path,
        statedir,
        clean_statedir,
        location_name,
        git_url,
        commit_hash,
        status_url,
        snapshot_base_condition,
        require_branch_deployment,
    )


def init_impl(
    organization: str,
    deployment: Optional[str],
    dagster_env: Optional[str],
    project_dir: str,
    dagster_cloud_yaml_path: str,
    statedir: str,
    clean_statedir: bool,
    location_name: list[str],
    git_url: Optional[str],
    commit_hash: Optional[str],
    status_url: Optional[str],
    snapshot_base_condition: Optional[SnapshotBaseDeploymentCondition],
    require_branch_deployment: bool,
):
    yaml_path = pathlib.Path(project_dir) / dagster_cloud_yaml_path
    if not yaml_path.exists():
        raise ui.error(
            f"Dagster Cloud yaml file not found at specified path {yaml_path.resolve()}."
        )
    locations_def = load_dagster_cloud_yaml(yaml_path.read_text())
    locations = locations_def.locations
    if location_name:
        selected_locations = set(location_name)
        unknown = selected_locations - set(location.location_name for location in locations)
        if unknown:
            raise ui.error(f"Locations not found in {dagster_cloud_yaml_path}: {unknown}")
        locations = [
            location for location in locations if location.location_name in selected_locations
        ]
    url = get_org_url(organization, dagster_env)
    # Deploy to the branch deployment for the current context. If there is no branch deployment
    # available (eg. if not in a PR) then we fallback to the --deployment flag.

    try:
        branch_deployment_name = create_or_update_deployment_from_context(
            url,
            project_dir,
            mark_closed=False,
            base_deployment_name=deployment,
            snapshot_base_condition=snapshot_base_condition,
            require_branch_deployment=require_branch_deployment,
        )
        if branch_deployment_name:
            ui.print(
                f"Deploying to branch deployment {branch_deployment_name}"
                + (f", using base deployment {deployment}" if deployment else "")
            )
            deployment = branch_deployment_name
            is_branch_deployment = True
        else:
            if not deployment:
                raise ui.error("Cannot determine deployment name. Please specify --deployment.")

            ui.print(f"Deploying to {deployment}.")
            is_branch_deployment = False

    except ValueError as err:
        if deployment:
            ui.print(f"Deploying to {deployment}. No branch deployment ({err}).")
            is_branch_deployment = False
        else:
            raise ui.error(
                f"Cannot determine deployment name in current context ({err}). Please specify"
                " --deployment."
            )

    if require_branch_deployment and not is_branch_deployment:
        raise ui.error(
            "--branch-deployment flag was provided, but was unable to determine a branch deployment."
        )

    if clean_statedir and os.path.exists(statedir):
        shutil.rmtree(statedir, ignore_errors=True)
    state_store = state.FileStore(statedir=statedir)

    ui.print(f"Initializing {statedir}")
    for location in locations:
        location_state = state.LocationState(
            url=url,
            deployment_name=deployment,
            location_file=str(yaml_path.absolute()),
            location_name=location.location_name,
            is_branch_deployment=is_branch_deployment,
            build=state.BuildMetadata(
                git_url=git_url,
                commit_hash=commit_hash,
                build_config=location.build,
            ),
            build_output=None,
            status_url=status_url,
            project_dir=project_dir,
        )
        location_state.add_status_change(state.LocationStatus.pending, "initialized")
        state_store.save(location_state)

    ui.print(
        f"Initialized {statedir} to build and deploying following locations for directory"
        f" {project_dir}:"
    )
    for location in state_store.list_locations():
        ui.print(f"- {location.location_name}")


class StatusOutputFormat(Enum):
    json = "json"
    markdown = "markdown"


@app.command(help="Show status of the current build session")
def status(
    statedir: str = STATEDIR_OPTION,
    output_format: StatusOutputFormat = typer.Option("json", help="Output format for build status"),
):
    state_store = state.FileStore(statedir=statedir)
    location_states = state_store.list_locations()
    if output_format == StatusOutputFormat.json:
        for location in location_states:
            ui.print(location.json())
    elif output_format == StatusOutputFormat.markdown:
        ui.print(report.markdown_report(location_states))


@app.command(help="Update the PR comment with the latest status for branch deployments in Github.")
def notify(
    statedir: str = STATEDIR_OPTION,
    project_dir: str = typer.Option("."),
):
    state_store = state.FileStore(statedir=statedir)
    location_states = state_store.list_locations()

    source = metrics.get_source()
    if source == CliEventTags.source.github:
        event = github_context.get_github_event(project_dir)
        msg = f"Your pull request at commit `{event.github_sha}` is automatically being deployed to Dagster Cloud."
        event.update_pr_comment(
            msg + "\n\n" + report.markdown_report(location_states),
            orig_author="github-actions[bot]",
            orig_text="Dagster Cloud",  # used to identify original comment
        )
    else:
        raise ui.error("'dagster-cloud ci notify' is only available within Github actions.")


@app.command(help="List locations in the current build session")
def locations_list(
    statedir: str = STATEDIR_OPTION,
):
    state_store = state.FileStore(statedir=statedir)
    for location in state_store.list_locations():
        if location.selected:
            ui.print(f"{location.location_name}")
        else:
            ui.print(f"{location.location_name} DESELECTED")


@app.command(help="Mark the specified locations as excluded from the current build session")
def locations_deselect(
    location_names: list[str],
    statedir: str = STATEDIR_OPTION,
):
    state_store = state.FileStore(statedir=statedir)
    state_store.deselect(location_names)
    ui.print("Deselected locations: {locations_names}")


@app.command(help="Mark the specified locations as included in the current build session")
def locations_select(
    location_names: list[str],
    statedir: str = STATEDIR_OPTION,
):
    state_store = state.FileStore(statedir=statedir)
    state_store.select(location_names)
    ui.print("Deselected locations: {locations_names}")


def _get_selected_locations(
    state_store: state.Store, location_name: list[str]
) -> dict[str, state.LocationState]:
    requested_locations = set(location_name)
    selected = {
        location.location_name: location
        for location in state_store.list_selected_locations()
        if not requested_locations or location.location_name in requested_locations
    }
    unknown_locations = requested_locations - set(selected)
    if unknown_locations:
        raise ui.error(f"Unknown or deselected location names requested: {unknown_locations}")
    return selected


class BuildStrategy(Enum):
    pex = "python-executable"
    docker = "docker"


@app.command(help="Build selected or requested locations")
def build(
    statedir: str = STATEDIR_OPTION,
    location_name: list[str] = typer.Option([]),
    build_directory: Optional[str] = typer.Option(
        None,
        help=(
            "Directory root for building this code location. Read from dagster_cloud.yaml by"
            " default."
        ),
    ),
    build_strategy: BuildStrategy = typer.Option(
        "docker",
        help=(
            "Build strategy used to build code locations. 'docker' builds a docker image."
            " 'python-executable' builds a set of pex files."
        ),
    ),
    docker_image_tag: Optional[str] = typer.Option(
        None, help="Tag for built docker image. Auto-generated by default."
    ),
    docker_base_image: Optional[str] = typer.Option(
        None,
        help="Base image used to build the docker image for --build-strategy=docker.",
    ),
    docker_env: list[str] = typer.Option([], help="Env vars for docker builds."),
    dockerfile_path: Optional[str] = typer.Option(
        None,
        help=(
            "Path to a Dockerfile to use for the docker build. If not provided, a default templated Dockerfile is used."
        ),
    ),
    python_version: str = typer.Option(
        DEFAULT_PYTHON_VERSION,
        help=(
            "Python version used to build the python-executable; or to determine the default base"
            " image for docker."
        ),
    ),
    pex_build_method: deps.BuildMethod = typer.Option("local"),
    pex_deps_cache_from: Optional[str] = None,
    pex_deps_cache_to: Optional[str] = None,
    pex_base_image_tag: Optional[str] = typer.Option(
        None,
        help="Base image used to run python executable for --build-strategy=python-executable.",
    ),
    use_editable_dagster: bool = typer.Option(
        False,
        help="Include the editable dagster package in the Docker context for the build.",
    ),
) -> None:
    build_impl(
        statedir,
        location_name,
        build_directory,
        build_strategy,
        docker_image_tag,
        docker_base_image,
        docker_env,
        dockerfile_path,
        python_version,
        pex_build_method,
        pex_deps_cache_from,
        pex_deps_cache_to,
        pex_base_image_tag,
        use_editable_dagster,
    )


def build_impl(
    statedir: str,
    location_name: list[str],
    build_directory: Optional[str],
    build_strategy: BuildStrategy,
    docker_image_tag: Optional[str],
    docker_base_image: Optional[str],
    docker_env: list[str],
    dockerfile_path: Optional[str],
    python_version: str,
    pex_build_method: deps.BuildMethod,
    pex_deps_cache_from: Optional[str],
    pex_deps_cache_to: Optional[str],
    pex_base_image_tag: Optional[str],
    use_editable_dagster: bool,
):
    if python_version:
        # ensure version is parseable
        pex_builder.util.parse_python_version(python_version)

    if build_strategy == BuildStrategy.pex:
        if docker_base_image or docker_image_tag:
            raise ui.error(
                "--base-image or --image-tag not supported for --build-strategy=python-executable."
            )

    if docker_base_image and dockerfile_path:
        raise ui.error(
            "--base-image and --dockerfile-path cannot both be provided. Please provide only one."
        )

    state_store = state.FileStore(statedir=statedir)
    locations = _get_selected_locations(state_store, location_name)
    ui.print("Going to build the following locations:")
    for name in locations:
        ui.print(f"- {name}")

    for name, location_state in locations.items():
        project_dir = location_state.project_dir
        try:
            configured_build_directory = (
                location_state.build.build_config.directory
                if (
                    location_state.build.build_config
                    and location_state.build.build_config.directory
                )
                else None
            )
            if build_directory and configured_build_directory:
                ui.warn(
                    f"Overriding configured build:directory:{configured_build_directory!r} with"
                    f" cmdline provided --build-directory={build_directory!r}"
                )
                location_build_dir = build_directory
            elif (not build_directory) and configured_build_directory:
                location_build_dir = configured_build_directory
            elif build_directory and (not configured_build_directory):
                location_build_dir = build_directory
            else:
                location_build_dir = "."

            if project_dir and not os.path.isabs(location_build_dir):
                location_build_dir = str(pathlib.Path(project_dir) / location_build_dir)

            url = location_state.url
            api_token = get_user_token() or ""

            if build_strategy == BuildStrategy.docker:
                location_state.build_output = _build_docker(
                    url=url,
                    api_token=api_token,
                    name=name,
                    location_build_dir=location_build_dir,
                    docker_base_image=docker_base_image,
                    python_version=python_version,
                    docker_env=docker_env,
                    location_state=location_state,
                    dockerfile_path=dockerfile_path,
                    use_editable_dagster=use_editable_dagster,
                )
                state_store.save(location_state)
            elif build_strategy == BuildStrategy.pex:
                location_state.build_output = _build_pex(
                    url=url,
                    api_token=api_token,
                    name=name,
                    location_build_dir=location_build_dir,
                    python_version=python_version,
                    pex_build_method=pex_build_method,
                    pex_deps_cache_from=pex_deps_cache_from,
                    pex_deps_cache_to=pex_deps_cache_to,
                    pex_base_image_tag=pex_base_image_tag,
                    location_state=location_state,
                )
                state_store.save(location_state)
                ui.print(
                    "Built and uploaded python executable"
                    f" {location_state.build_output.pex_tag} for location {name}"
                )
        except:
            location_state.add_status_change(state.LocationStatus.failed, "build failed")
            state_store.save(location_state)
            raise
        else:
            location_state.add_status_change(state.LocationStatus.pending, "build successful")
            state_store.save(location_state)


@metrics.instrument(
    CliEventType.BUILD,
    tags=[
        CliEventTags.subcommand.dagster_cloud_ci,
        CliEventTags.server_strategy.docker,
    ],
)
# url and api_token are used by the instrument decorator
def _build_docker(
    url: str,
    api_token: str,
    name: str,
    location_build_dir: str,
    python_version: str,
    docker_base_image: Optional[str],
    docker_env: list[str],
    location_state: state.LocationState,
    use_editable_dagster: bool,
    dockerfile_path: Optional[str] = None,
) -> state.DockerBuildOutput:
    name = location_state.location_name
    docker_utils.verify_docker()
    registry_info = utils.get_registry_info(url)

    docker_image_tag = docker_utils.default_image_tag(
        location_state.deployment_name, name, location_state.build.commit_hash
    )

    if not dockerfile_path and not docker_base_image:
        docker_base_image = f"python:{python_version}-slim"

    ui.print(
        f"Building docker image for location {name}"
        + (f" using base image {docker_base_image}" if docker_base_image else "")
    )

    retval = docker_utils.build_image(
        location_build_dir,
        docker_image_tag,
        registry_info,
        env_vars=docker_env,
        base_image=docker_base_image,
        dockerfile_path=dockerfile_path,
        use_editable_dagster=use_editable_dagster,
    )
    if retval != 0:
        raise ui.error(f"Failed to build docker image for location {name}")

    retval = docker_utils.upload_image(docker_image_tag, registry_info)
    if retval != 0:
        raise ui.error(f"Failed to upload docker image for location {name}")

    image = f"{registry_info['registry_url']}:{docker_image_tag}"
    ui.print(f"Built and uploaded image {image} for location {name}")

    return state.DockerBuildOutput(image=image)


@metrics.instrument(
    CliEventType.BUILD,
    tags=[CliEventTags.subcommand.dagster_cloud_ci, CliEventTags.server_strategy.pex],
)
# url and api_token are used by the instrument decorator
def _build_pex(
    url: str,
    api_token: str,
    name: str,
    location_build_dir: str,
    python_version: str,
    pex_build_method: deps.BuildMethod,
    pex_deps_cache_from: Optional[str],
    pex_deps_cache_to: Optional[str],
    pex_base_image_tag: Optional[str],
    location_state: state.LocationState,
) -> state.PexBuildOutput:
    pex_location = parse_workspace.Location(
        name,
        directory=location_build_dir,
        build_folder=location_build_dir,
        location_file=location_state.location_file,
    )

    location_kwargs = pex_utils.build_upload_pex(
        url=url,
        api_token=api_token,
        location=pex_location,
        build_method=pex_build_method,
        kwargs={
            "python_version": python_version,
            "base_image_tag": pex_base_image_tag,
            "deps_cache_from": pex_deps_cache_from,
            "deps_cache_to": pex_deps_cache_to,
        },
    )
    return state.PexBuildOutput(
        python_version=python_version,
        image=location_kwargs.get("image"),
        pex_tag=location_kwargs["pex_tag"],
    )


@app.command(help="Update the current build session for an externally built docker image.")
def set_build_output(
    statedir: str = STATEDIR_OPTION,
    location_name: list[str] = typer.Option([]),
    image_tag: str = typer.Option(
        ...,
        help=(
            "Tag for the built docker image. Note the registry must be specified in"
            " dagster_cloud.yaml."
        ),
    ),
) -> None:
    set_build_output_impl(
        statedir,
        location_name,
        image_tag,
    )


def set_build_output_impl(
    statedir: str,
    location_name: list[str],
    image_tag: str,
) -> None:
    state_store = state.FileStore(statedir=statedir)
    locations = _get_selected_locations(state_store, location_name)
    ui.print("Going to update the following locations:")
    for name in locations:
        ui.print(f"- {name}")

    # validation pass - computes the full image name for all locations
    images = {}
    for name, location_state in locations.items():
        configured_defs = load_dagster_cloud_yaml(
            open(location_state.location_file, encoding="utf-8").read()
        )
        location_defs = [loc for loc in configured_defs.locations if loc.location_name == name]
        if not location_defs:
            raise ui.error(f"Location {name} not found in {location_state.location_file}")
        location_def = location_defs[0]
        registry = location_def.build.registry if location_def.build else None
        if not registry:
            raise ui.error(
                f"No build:registry: defined for location {name} in {location_state.location_file}"
            )

        images[name] = f"{registry}:{image_tag}"

    # save pass - save full image name computed in the previous pass for all locations
    for name, location_state in locations.items():
        # Update and save build state
        location_state.build_output = state.DockerBuildOutput(image=images[name])
        state_store.save(location_state)
        ui.print(f"Recorded image {images[name]} for location {name}")
    ui.print("Use 'ci deploy' to update dagster-cloud.")


@app.command(help="Deploy built code locations to dagster cloud.")
def deploy(
    statedir: str = STATEDIR_OPTION,
    location_name: list[str] = typer.Option([]),
    location_load_timeout: int = LOCATION_LOAD_TIMEOUT_OPTION,
    agent_heartbeat_timeout: int = get_agent_heartbeat_timeout_option(default_timeout=None),
):
    deploy_impl(statedir, location_name, location_load_timeout, agent_heartbeat_timeout)


def deploy_impl(
    statedir: str,
    location_name: list[str],
    location_load_timeout: int,
    agent_heartbeat_timeout: Optional[int],
):
    state_store = state.FileStore(statedir=statedir)
    locations = _get_selected_locations(state_store, location_name)
    ui.print("Going to deploy the following locations:")

    built_locations: list[state.LocationState] = []
    unbuilt_location_names: list[str] = []
    for name, location_state in locations.items():
        if location_state.build_output:
            status = "Ready to deploy"
            built_locations.append(location_state)
        else:
            status = "Not ready to deploy"
            unbuilt_location_names.append(name)
        ui.print(f"- {name} [{status}]")

    if unbuilt_location_names:
        raise ui.error(
            f"Cannot deploy because the following location{'s have' if len(unbuilt_location_names) > 1 else ' has'} "
            f"not been built: {', '.join(unbuilt_location_names)}. "
            "Use 'ci build' (in Dagster+ Serverless) or `ci set-build-output` (in Dagster+ Hybrid) to build"
            " locations."
        )

    if not built_locations:
        ui.print("No locations to deploy")
        return

    try:
        _deploy(
            url=built_locations[0].url,
            api_token=check.not_none(get_user_token()),
            built_locations=built_locations,
            location_load_timeout=location_load_timeout,
            agent_heartbeat_timeout=agent_heartbeat_timeout,
        )
    except:
        # unfortunately we do not know if only a subset of locations failed to deploy
        for location_state in built_locations:
            location_state.add_status_change(state.LocationStatus.failed, "deploy failed")
            state_store.save(location_state)
        raise
    else:
        for location_state in built_locations:
            location_state.add_status_change(state.LocationStatus.success, "deploy successful")
            state_store.save(location_state)

    deployment_url = built_locations[0].url + "/" + built_locations[0].deployment_name
    ui.print(f"View the status of your locations at {deployment_url}/locations.")


@metrics.instrument(CliEventType.DEPLOY, tags=[CliEventTags.subcommand.dagster_cloud_ci])
# url and api_token are used by the instrument decorator
def _deploy(
    *,
    url: str,
    api_token: str,
    built_locations: list[state.LocationState],
    location_load_timeout: int,
    agent_heartbeat_timeout: Optional[int],
):
    locations_document = []
    for location_state in built_locations:
        build_output = location_state.build_output
        if not build_output:  # not necessary but keep type checker happy
            continue

        location_args = {
            "image": build_output.image,
            "location_file": location_state.location_file,
            "git_url": location_state.build.git_url,
            "commit_hash": location_state.build.commit_hash,
            **(
                {"defs_state_info": location_state.defs_state_info.model_dump()}
                if location_state.defs_state_info
                else {}
            ),
        }
        if build_output.strategy == "python-executable":
            metrics.instrument_add_tags([CliEventTags.server_strategy.pex])
            location_args["pex_tag"] = build_output.pex_tag
            location_args["python_version"] = build_output.python_version
        else:
            metrics.instrument_add_tags([CliEventTags.server_strategy.docker])

        locations_document.append(
            get_location_document(location_state.location_name, location_args)
        )

    deployment_url = built_locations[0].url + "/" + built_locations[0].deployment_name
    with utils.client_from_env(
        built_locations[0].url, deployment=built_locations[0].deployment_name
    ) as client:
        location_names = [location_state.location_name for location_state in built_locations]
        gql.deploy_code_locations(client, {"locations": locations_document})
        ui.print(
            f"Updated code location{'s' if len(location_names) > 1 else ''} {', '.join(location_names)} in dagster-cloud."
        )

        if not agent_heartbeat_timeout:
            agent_type = gql.fetch_agent_type(client)
            # raise the agent heartbeat timeout for serverless deploys to ensure that the
            # deploy doesn't fail if the agent is still being spun up. A deploy is serverless if
            # that's the default agent type for the deployment and the locations aren't being
            # deployed to some other agent queue (since serverless agents only serve the default
            # agent queue)
            if agent_type != DagsterPlusDeploymentAgentType.SERVERLESS or any(
                location_config.get("agent_queue") for location_config in locations_document
            ):
                agent_heartbeat_timeout = DEFAULT_HYBRID_AGENT_HEARTBEAT_TIMEOUT
            else:
                agent_heartbeat_timeout = DEFAULT_SERVERLESS_AGENT_HEARTBEAT_TIMEOUT

        wait_for_load(
            client,
            location_names,
            location_load_timeout=location_load_timeout,
            agent_heartbeat_timeout=agent_heartbeat_timeout,
            url=deployment_url,
        )


dagster_dbt_app = typer.Typer(
    hidden=True,
    help="Dagster Cloud commands for managing the `dagster-dbt` integration.",
    add_completion=False,
)
app.add_typer(dagster_dbt_app, name="dagster-dbt", no_args_is_help=True)

project_app = typer.Typer(
    name="project",
    no_args_is_help=True,
    help="Commands for using a dbt project in Dagster.",
    add_completion=False,
)
dagster_dbt_app.add_typer(project_app, name="project", no_args_is_help=True)


@project_app.command(
    name="manage-state",
    help="""
    This CLI command will handle uploading and downloading dbt state, in the form of manifest.json,
    if `state_path` is specified on `DbtProject`.
    """,
)
def manage_state_command(
    statedir: str = STATEDIR_OPTION,
    file: Annotated[
        Optional[pathlib.Path],
        typer.Option(
            help="The file containing DbtProject definitions to prepare.",
        ),
    ] = None,
    components: Annotated[
        Optional[pathlib.Path],
        typer.Option(
            help="The path to a dg project directory containing DbtProjectComponents.",
        ),
    ] = None,
    source_deployment: Annotated[
        str,
        typer.Option(
            help="Which deployment should upload its manifest.json.",
        ),
    ] = "prod",
    key_prefix: Annotated[
        str,
        typer.Option(
            help="A key prefix for the key the manifest.json is saved with.",
        ),
    ] = "",
):
    try:
        from dagster_dbt import DbtProject
    except:
        ui.print(
            "Unable to import dagster_dbt. To use `manage-state`, dagster_dbt must be installed."
        )
        return
    try:
        from dagster._core.code_pointer import load_python_file
        from dagster._core.definitions.module_loaders.utils import find_objects_in_module_of_types
    except:
        ui.print("Unable to import dagster. To use `manage-state`, dagster must be installed.")
        return

    state_store = state.FileStore(statedir=statedir)
    locations = state_store.list_locations()
    if not locations:
        raise ui.error("Unable to determine deployment state.")

    location = locations[0]
    deployment_name = location.deployment_name
    is_branch = location.is_branch_deployment
    if file:
        contents = load_python_file(file, None)
        projects = find_objects_in_module_of_types(contents, DbtProject)
    elif components:
        from dagster_dbt.components.dbt_project.component import get_projects_from_dbt_component

        projects = get_projects_from_dbt_component(components)
    else:
        raise click.UsageError("Must specify --file or --components")

    for project in projects:
        project = cast("DbtProject", project)
        if project.state_path:
            download_path = project.state_path.joinpath("manifest.json")
            key = f"{key_prefix}{os.fspath(download_path)}"
            if is_branch:
                ui.print(f"Downloading {source_deployment} manifest for branch deployment.")
                os.makedirs(project.state_path, exist_ok=True)
                download_organization_artifact(key, download_path)
                ui.print("Download complete.")

            elif deployment_name == source_deployment:
                ui.print(f"Uploading {source_deployment} manifest.")
                upload_organization_artifact(key, project.manifest_path)
                ui.print("Upload complete")

            else:
                ui.warn(
                    f"Deployment named {deployment_name} does not match source deployment {source_deployment}, taking no action. "
                    f"If this is the desired dbt state artifacts to upload, set the cli flags `--source-deployment {deployment_name}`."
                )
