import base64
import json
import os
import subprocess
from pathlib import Path
from typing import Optional

from dagster_shared import seven
from typer import Argument, Option, Typer

from dagster_cloud_cli import docker_utils, gql, pex_utils, ui
from dagster_cloud_cli.commands import metrics
from dagster_cloud_cli.commands.workspace import wait_for_load
from dagster_cloud_cli.config_utils import (
    DEPLOYMENT_CLI_OPTIONS,
    dagster_cloud_options,
    get_location_document,
)
from dagster_cloud_cli.core import pex_builder
from dagster_cloud_cli.types import CliEventTags, CliEventType
from dagster_cloud_cli.utils import DEFAULT_PYTHON_VERSION, add_options

app = Typer(help="Build and deploy your code to Dagster Cloud.")

_BUILD_OPTIONS = {
    "source_directory": (
        Path,
        Option(
            None,
            "--source-directory",
            "-d",
            exists=False,
            help="Source directory to build for the image.",
        ),
    ),
    "base_image": (
        str,
        Option(None, "--base-image", exists=False),
    ),
    "env": (
        list[str],
        Option(
            [],
            "--env",
            exists=False,
            help="Environment variable to be defined in image, in the form of `MY_ENV_VAR=hello`",
        ),
    ),
}

DEPLOY_DOCKER_OPTIONS = {
    "image": (
        str,
        Option(
            None,
            "--image",
            exists=False,
            help="Override built Docker image tag. Should not be needed outside of debugging.",
            hidden=True,
        ),
    ),
    "base_image": (
        str,
        Option(None, "--base-image", exists=False, help="Custom base image"),
    ),
    "env": (
        list[str],
        Option(
            [],
            "--env",
            exists=False,
            help="Environment variable to be defined in image, in the form of `MY_ENV_VAR=hello`",
        ),
    ),
}


@app.command(name="build", short_help="Build image for Dagster Cloud code location.", hidden=True)
@dagster_cloud_options(allow_empty=True, requires_url=True)
@add_options(_BUILD_OPTIONS)
@metrics.instrument(
    CliEventType.BUILD,
    tags=[CliEventTags.subcommand.dagster_cloud_serverless, CliEventTags.server_strategy.docker],
)
def build_command(
    api_token: str,
    url: str,
    location_load_timeout: int,
    agent_heartbeat_timeout: int,
    image: str = Argument(None, help="Image name."),
    **kwargs,
):
    """Add or update the image for a code location in the workspace."""
    source_directory = str(kwargs.get("source_directory"))
    base_image = kwargs.get("base_image")
    env_vars = kwargs.get("env", [])
    docker_utils.verify_docker()

    with gql.graphql_client_from_url(url, api_token) as client:
        ecr_info = gql.get_ecr_info(client)
        registry = ecr_info["registry_url"]

        if base_image and not ecr_info.get("allow_custom_base"):
            ui.warn("Custom base images are not enabled for this organization.")
            base_image = None

        retval = docker_utils.build_image(
            source_directory, image, ecr_info, env_vars, base_image, use_editable_dagster=False
        )
        if retval == 0:
            ui.print(f"Built image {registry}:{image}")


@app.command(
    name="upload",
    short_help="Upload the built code location image to Dagster Cloud's image repository.",
    hidden=True,
)
@dagster_cloud_options(allow_empty=True, requires_url=True)
@metrics.instrument(
    CliEventType.UPLOAD,
    tags=[CliEventTags.subcommand.dagster_cloud_serverless, CliEventTags.server_strategy.docker],
)
def upload_command(
    api_token: str,
    url: str,
    location_load_timeout: int,
    agent_heartbeat_timeout: int,
    image: str = Argument(None, help="Image name."),
    **kwargs,
):
    """Add or update the image for a code location in the workspace."""
    docker_utils.verify_docker()

    with gql.graphql_client_from_url(url, api_token) as client:
        ecr_info = gql.get_ecr_info(client)
        registry = ecr_info["registry_url"]
        retval = docker_utils.upload_image(image, ecr_info)
        if retval == 0:
            ui.print(f"Pushed image {image} to {registry}")


@app.command(
    name="registry-info",
    short_help="Get registry information and temporary creds for an image repository",
    hidden=True,
)
@dagster_cloud_options(allow_empty=True, requires_url=True)
def registry_info_command(
    api_token: str,
    url: str,
    location_load_timeout: int,
    agent_heartbeat_timeout: int,
    **kwargs,
):
    """Add or update the image for a code location in the workspace. Used by GH action to
    authenticate to the image registry.
    """
    with gql.graphql_client_from_url(url, api_token) as client:
        ecr_info = gql.get_ecr_info(client)
        registry_url = ecr_info["registry_url"]
        aws_region = ecr_info.get("aws_region", "us-west-2")
        aws_token = ecr_info["aws_auth_token"]
        custom_base_image_allowed = ecr_info["allow_custom_base"]

        if not aws_token or not registry_url:
            return

        username, password = base64.b64decode(aws_token).decode("utf-8").split(":")

        values = [
            f"REGISTRY_URL={registry_url}",
            f"AWS_DEFAULT_REGION={aws_region}",
            f"AWS_ECR_USERNAME={username}",
            f"AWS_ECR_PASSWORD={password}",
        ]
        if custom_base_image_allowed:
            values.append("CUSTOM_BASE_IMAGE_ALLOWED=1")
        ui.print("\n".join(values) + "\n")


@app.command(name="deploy", short_help="Alias for 'deploy-docker'.", hidden=True)
@app.command(
    name="deploy-docker",
    short_help=(
        "Add a code location from a local directory, deployed as a Docker image. "
        "Also see 'deploy-python-executable' as an alternative deployment method."
    ),
)
@dagster_cloud_options(allow_empty=True, requires_url=True)
@add_options(DEPLOY_DOCKER_OPTIONS)
@add_options(DEPLOYMENT_CLI_OPTIONS)
@metrics.instrument(
    CliEventType.DEPLOY,
    tags=[CliEventTags.subcommand.dagster_cloud_serverless, CliEventTags.server_strategy.docker],
)
def deploy_command(
    api_token: str,
    url: str,
    location_load_timeout: int,
    agent_heartbeat_timeout: int,
    deployment: str,
    source_directory: Path = Argument(".", help="Source directory."),
    **kwargs,
):
    """Add a code location from a local directory, deployed as a Docker image."""
    location_name = kwargs.get("location_name")
    if not location_name:
        raise ui.error(
            "No location name provided. You must specify the location name as an argument."
        )

    if not source_directory:
        raise ui.error("No source directory provided.")

    _check_source_directory(source_directory)
    docker_utils.verify_docker()

    env_vars = kwargs.get("env", [])
    base_image = kwargs.get("base_image")

    with gql.graphql_client_from_url(url, api_token, deployment_name=deployment) as client:
        ecr_info = gql.get_ecr_info(client)
        registry = ecr_info["registry_url"]

        image_tag = kwargs.get("image") or docker_utils.default_image_tag(
            deployment, location_name, kwargs.get("commit_hash")
        )
        retval = docker_utils.build_image(
            source_directory, image_tag, ecr_info, env_vars, base_image, use_editable_dagster=False
        )
        if retval != 0:
            return

        retval = docker_utils.upload_image(image_tag, ecr_info)
        if retval != 0:
            return

        location_args = {**kwargs, "image": f"{registry}:{image_tag}"}
        location_document = get_location_document(location_name, location_args)
        gql.add_or_update_code_location(client, location_document)

        wait_for_load(
            client,
            [location_name],
            location_load_timeout=location_load_timeout,
            agent_heartbeat_timeout=agent_heartbeat_timeout,
            url=url,
        )

        workspace_url = f"{url}/locations"
        ui.print(
            f"Added or updated location {location_name}. "
            f"View the status of your workspace at {workspace_url}."
        )


@app.command(
    name="upload-base-image",
    short_help=(
        "Upload a local Docker image to Dagster cloud, to use as a custom base image for"
        " deploy-python-executable."
    ),
)
@dagster_cloud_options(allow_empty=True, requires_url=True)
@metrics.instrument(
    CliEventType.UPLOAD,
    tags=[CliEventTags.subcommand.dagster_cloud_serverless, CliEventTags.server_strategy.pex],
)
def upload_base_image_command(
    api_token: str,
    url: str,
    local_image: str = Argument(..., help="Pre-built local image, eg. 'local-image:local-tag'"),
    published_tag: str = Option(
        None,
        help=(
            "Published tag used to identify this image in Dagster Cloud. "
            "A tag is auto-generated if not provided."
        ),
    ),
):
    if not published_tag:
        published_tag = _generate_published_tag_for_image(local_image)

    with gql.graphql_client_from_url(url, api_token) as client:
        ecr_info = gql.get_ecr_info(client)
        registry = ecr_info["registry_url"]
        published_image = f"{registry}:{published_tag}"

        # tag local image with new tag
        cmd = [
            "docker",
            "tag",
            local_image,
            published_image,
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as err:
            raise ui.error(
                f"Error tagging local image {local_image}: " + err.stderr.decode("utf-8")
            )

        # upload tagged image
        retval = docker_utils.upload_image(image=published_tag, registry_info=ecr_info)
        if retval == 0:
            ui.print(f"Pushed image {published_tag} to {registry}.")
            ui.print(
                "To use the uploaded image run: "
                f"dagster-cloud serverless deploy-python-executable --base-image-tag={published_tag} [ARGS]"
            )


def _generate_published_tag_for_image(image: str):
    image_id = subprocess.check_output(["docker", "inspect", image, "--format={{.Id}}"])
    #  The id is something like 'sha256:518ad2f92b078c63c60e89f0310f13f19d3a1c7ea9e1976d67d59fcb7040d0d6'
    return image_id.decode("utf-8").replace(":", "_").strip()


@app.command(name="build-python-executable", short_help="Build a Python Executable", hidden=True)
@add_options(
    {
        "python_version": (
            str,
            Option(
                DEFAULT_PYTHON_VERSION,
                help="Target Python version as 'major.minor'",
            ),
        ),
        "build_method": (
            pex_builder.deps.BuildMethod,
            Option("docker-fallback", help="Environment used to build the dependencies."),
        ),
    }
)
@dagster_cloud_options(allow_empty=True, requires_url=True)
@metrics.instrument(
    CliEventType.BUILD,
    tags=[CliEventTags.subcommand.dagster_cloud_serverless, CliEventTags.server_strategy.pex],
)
def build_python_executable_command(
    code_directory: str,
    output_directory: str,
    python_version: str,
    build_method: pex_builder.deps.BuildMethod,
    api_token: str,
    url: str,
):
    parsed_python_version = pex_builder.util.parse_python_version(python_version)
    code_directory = os.path.abspath(code_directory)
    output_directory = os.path.abspath(output_directory)

    locations = [
        pex_builder.parse_workspace.Location(
            name="",  # unused since we don't upload
            directory=code_directory,
            build_folder=output_directory,
            location_file="",  # unused
        )
    ]
    ui.print(
        f"Going to build Python executable from {code_directory} for Python {parsed_python_version}"
    )
    builds = pex_builder.deploy.build_locations(
        url,
        api_token,
        locations,
        output_directory,
        upload_pex=False,
        deps_cache_tags=pex_builder.deploy.DepsCacheTags(
            deps_cache_from_tag=None, deps_cache_to_tag=None
        ),
        python_version=parsed_python_version,
        build_method=build_method,
    )
    build = builds[0]
    pex_utils.print_built_pex_details(build)


@app.command(
    name="build-python-deps", short_help="Build dependencies for a Python Executable", hidden=True
)
def build_python_dependencies(
    requirements_path: str,
    output_pex_path: str,
    pex_flags: str,
):
    ui.print(f"Going to build Python dependencies pex from {requirements_path}")
    if not os.path.isfile(requirements_path):
        raise ui.error(f"No such file {requirements_path}")
    try:
        pex_builder.deps.build_deps_from_requirements_file(
            requirements_path, output_pex_path, json.loads(pex_flags)
        )
    except pex_builder.deps.DepsBuildFailure as err:
        errors = [
            "Could not build dependencies for this project.",
            f"Dependencies:\n {' '.join(open(requirements_path).readlines())}",
            err.format_error(),
        ]
        raise ui.error("\n".join(errors))


@app.command(
    name="deploy-python-executable",
    short_help=(
        "[Fast Deploys] Add a code location from a local directory, deployed as a Python"
        " executable. Also see 'deploy-docker' as an alternative deployment method."
    ),
)
@dagster_cloud_options(allow_empty=True, requires_url=True)
@add_options(pex_utils.DEPLOY_PEX_OPTIONS)
@add_options(DEPLOYMENT_CLI_OPTIONS)
@metrics.instrument(
    CliEventType.DEPLOY,
    tags=[CliEventTags.subcommand.dagster_cloud_serverless, CliEventTags.server_strategy.pex],
)
def deploy_python_executable_command(
    api_token: str,
    url: str,
    deployment: Optional[str],
    location_load_timeout: int,
    agent_heartbeat_timeout: int,
    build_method: pex_builder.deps.BuildMethod,
    source_directory: Path = Argument(".", help="Source directory."),
    **kwargs,
):
    """Add a code location from a local directory, deployed as a Python executable."""
    if seven.IS_WINDOWS:
        raise ui.error(
            "Deploying Python executables is not supported on Windows. See 'deploy-docker' as an"
            " alternative deployment method."
        )

    location_name = kwargs.get("location_name")
    if not location_name:
        raise ui.error(
            "No location name provided. You must specify the location name as an argument."
        )

    if (
        not kwargs.get("location_file")
        and not kwargs.get("python_file")
        and not kwargs.get("module_name")
        and not kwargs.get("package_name")
    ):
        raise ui.error(
            "Must specify --location-file, --package-name, --module-name, or --python-file."
        )

    if not source_directory:
        raise ui.error("No source directory provided.")
    source_directory = source_directory.absolute()

    location_file = kwargs.get("location_file")
    if location_file:
        location_file = location_file.absolute()
        kwargs["location_file"] = location_file
        locations = pex_builder.parse_workspace.get_locations(location_file)
    else:
        locations = []

    # Multi-location deployments using '*'
    if location_name == "*":
        if not locations:
            raise ui.error(
                "--location-name=* requires --location-file=path/to/dagster_cloud.yaml "
                "containing code location metadata, but no locations were found."
            )
        # location specific args don't make sense for multi location deploys
        single_locations_args = set(DEPLOYMENT_CLI_OPTIONS) - {
            "location_name",
            "location_file",
            "commit_hash",
            "git_url",
        }
        for arg in single_locations_args:
            if kwargs.get(arg):
                raise ui.error(
                    "--location-name=* reads metadata from --location-file and does not allow a"
                    f" flag for {arg}"
                )
    else:
        if location_file:
            # find the location matching this name loaded from location_file
            locations = [location for location in locations if location.name == location_name]
            if not locations:
                raise ui.error(f"Location {location_name} not found in {location_file}")
        else:
            # create a location using cmdline arguments only
            locations = [
                pex_builder.parse_workspace.Location(
                    name=location_name,
                    directory=str(source_directory),
                    build_folder=str(source_directory),
                    location_file="",
                )
            ]

    if len(locations) == 1:
        ui.print(f"Going to deploy location {locations[0].name}")
    else:
        ui.print(
            f"Going to deploy {len(locations)} locations:"
            f" {', '.join(location.name for location in locations)}"
        )
    for location in locations:
        _check_source_directory(location.directory)

    location_documents = []
    for location in locations:
        location_kwargs = pex_utils.build_upload_pex(
            url=url,
            api_token=api_token,
            location=location,
            build_method=build_method,
            kwargs=kwargs,
        )
        location_documents.append(get_location_document(location.name, location_kwargs))

    with gql.graphql_client_from_url(url, api_token, deployment_name=deployment) as client:
        for location_document in location_documents:
            gql.add_or_update_code_location(client, location_document)

        wait_for_load(
            client,
            [location.name for location in locations],
            location_load_timeout=location_load_timeout,
            agent_heartbeat_timeout=agent_heartbeat_timeout,
            url=url,
        )

        workspace_url = f"{url}/locations"
        ui.print(
            f"Added or updated locations: {', '.join([location.name for location in locations])}. "
            f"View the status of your workspace at {workspace_url}."
        )


SOURCE_INSTRUCTIONS = (
    "You can specify the directory you want to deploy by using the `--source-directory` argument "
    "(defaults to current directory)."
)


def _check_source_directory(source_directory):
    contents = os.listdir(source_directory)

    if (
        "setup.py" not in contents
        and "requirements.txt" not in contents
        and "pyproject.toml" not in contents
    ):
        message = (
            "Could not find a `setup.py`, `requirements.txt`, or `pyproject.toml` in the target directory. You must "
            "specify your required Python dependencies (including the `dagster-cloud` package) "
            "along with your source files to deploy to Dagster Cloud."
        )
        if source_directory == ".":
            message = f"{message} {SOURCE_INSTRUCTIONS}"
        raise ui.error(message)
